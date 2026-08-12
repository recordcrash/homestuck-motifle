# Collects Bandcamp track and album ids and writes them into hsmusic-data.
#
# hsmusic has fields for these -- 'Bandcamp Track ID' and 'Bandcamp Album ID' -- but hardly any
# entries carry one, and Bandcamp's embedded player can't be pointed at anything without them.
#
# Bandcamp serves a JS bot challenge to plain HTTP clients, so requests/curl can't read these pages
# at all; a real browser on a normal connection can. This drives your own Chrome, one page at a
# time, at a human pace. Nothing here logs in or touches anything non-public: album pages are
# public, and one of them carries the ids of every track on it plus the album's own id.
#
#   Setup:  pip install playwright pyyaml
#           (playwright install chromium is NOT needed when using --cdp)
#
#   1. Start Chrome with a debugging port, on a profile of its own:
#        chrome.exe --remote-debugging-port=9222 --user-data-dir="%TEMP%\bc-harvest"
#
#   2. Collect the ids into bandcamp_ids.json (resumable; ^C and re-run any time). This covers
#      every album with a Bandcamp url; --official-and-fandom narrows it to those groups:
#        python bandcampIds.py harvest --cdp http://localhost:9222
#
#   3. Write them into the wiki data, one line per entry:
#        python bandcampIds.py apply --dry-run
#        python bandcampIds.py apply
#
# Then commit hsmusic-data and open a pull request. Ids never change, so this only needs re-running
# when albums are added.

from typing import Dict, List, Optional, Tuple
import argparse
import glob
import html
import json
import os
import random
import re
import sys
import time

import yaml

file_path = os.path.dirname(os.path.realpath(__file__))
DEFAULT_DATA_PATH = os.path.join(file_path, 'hsmusic-data')
CACHE_PATH = os.path.join(file_path, 'bandcamp_ids.json')

TRACK_FIELD = 'Bandcamp Track ID'
ALBUM_FIELD = 'Bandcamp Album ID'

INCLUDED_GROUPS = ['Official Discography', 'group:official', 'Fandom']

# a page every few seconds, jittered. there are only a few hundred and no reason to hammer anyone
MIN_DELAY_SECONDS = 3.0
MAX_DELAY_SECONDS = 6.0

# an id lives in three places on a page; the JSON-LD block is the structured one, the others are
# fallbacks in case Bandcamp's markup shifts again
JSON_LD_PATTERN = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
TRAILING_COMMENT_PATTERN = re.compile(r'<!--\s*(track|album)\s+id\s+(\d+)\s*-->')
PAGE_PROPERTIES_PATTERN = re.compile(r'<meta\s+name="bc-page-properties"\s+content="([^"]*)"')

KEY_PATTERN = re.compile(r'^[A-Za-z#]')

# where each id belongs: with the entry's identity fields, after them and before anything else,
# which is where the entries that already have one put it
TRACK_IDENTITY_FIELDS = (
    'Track:', 'Additional Names:', 'Directory:', 'Suffix Directory:',
    'Always Reference By Directory:', 'Main Release:', 'Originally Released As:',
)
ALBUM_IDENTITY_FIELDS = (
    'Album:', 'Directory:', 'Directory Suffix:', 'Suffix Track Directories:',
    'Additional Names:', 'Date:', 'Date Added:',
)


# ---------------------------------------------------------------- parsing

def normalize_url(url: str) -> str:
    # hsmusic and Bandcamp disagree about trailing slashes and http/https, so compare on a
    # canonical form: no scheme, no trailing slash, no query string
    url = re.sub(r'^https?://', '', url.strip())
    return url.split('?')[0].split('#')[0].rstrip('/').lower()


def _properties_to_dict(entity: dict) -> dict:
    # schema.org additionalProperty is a list of {name, value} pairs
    return {p.get('name'): p.get('value')
            for p in (entity.get('additionalProperty') or []) if isinstance(p, dict)}


def parse_track_ids(page_html: str) -> Dict[str, int]:
    # {track url: track id} for every track the page describes. an album page describes all of
    # its tracks; a track page just itself
    track_ids = {}
    for raw_json in JSON_LD_PATTERN.findall(page_html):
        try:
            data = json.loads(raw_json.strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        entities = [data] if data.get('@type') == 'MusicRecording' else []
        for element in ((data.get('track') or {}).get('itemListElement') or []):
            item = element.get('item') if isinstance(element, dict) else None
            if isinstance(item, dict):
                entities.append(item)
        for entity in entities:
            url = entity.get('mainEntityOfPage') or entity.get('@id')
            track_id = _properties_to_dict(entity).get('track_id')
            if url and track_id:
                track_ids[normalize_url(url)] = int(track_id)
    return track_ids


def parse_page_id(page_html: str) -> Optional[Tuple[str, int]]:
    # the id of whatever the page itself is, as ('track'|'album', id)
    match = PAGE_PROPERTIES_PATTERN.search(page_html)
    if match:
        try:
            properties = json.loads(html.unescape(match.group(1)))
            if properties.get('item_id'):
                kind = 'album' if properties.get('item_type') == 'a' else 'track'
                return kind, int(properties['item_id'])
        except json.JSONDecodeError:
            pass
    match = TRAILING_COMMENT_PATTERN.search(page_html)
    if match:
        return match.group(1), int(match.group(2))
    return None


def parse_album_id(page_html: str) -> Optional[int]:
    page_id = parse_page_id(page_html)
    return page_id[1] if page_id and page_id[0] == 'album' else None


# ---------------------------------------------------------------- cache

def load_cache(cache_path: str = None) -> dict:
    cache_path = cache_path or CACHE_PATH
    if not os.path.exists(cache_path):
        return {'tracks': {}, 'albums': {}}
    with open(cache_path, 'r', encoding='utf8') as f:
        data = json.load(f)
    if 'tracks' in data or 'albums' in data:
        return {'tracks': data.get('tracks', {}), 'albums': data.get('albums', {})}
    return {'tracks': data, 'albums': {}}  # the older flat {track url: id} format


def save_cache(cache: dict, cache_path: str = None) -> None:
    with open(cache_path or CACHE_PATH, 'w', encoding='utf8') as f:
        f.write(json.dumps({'tracks': dict(sorted(cache['tracks'].items())),
                            'albums': dict(sorted(cache['albums'].items()))}, indent=2))


# ---------------------------------------------------------------- reading the wiki

def read_albums(data_path: str) -> List[dict]:
    # one entry per album file: its path, url, and the bandcamp urls of its tracks
    albums = []
    for album_file in sorted(glob.glob(os.path.join(data_path, 'album', '*.yaml'))):
        with open(album_file, 'r', encoding='utf8') as f:
            documents = [d for d in yaml.safe_load_all(f) if d]
        album_object = next((d for d in documents if 'Album' in d), None)
        if not album_object:
            continue
        album_urls = [u for u in (album_object.get('URLs') or []) if u and 'bandcamp.com/album/' in u]
        if not album_urls:
            continue
        track_urls = []
        for song in documents:
            if 'Track' not in song:
                continue
            for url in (song.get('URLs') or []):
                if url and 'bandcamp.com' in url:
                    track_urls.append(normalize_url(url))
                    break
        albums.append({
            'file': album_file,
            'url': album_urls[0],
            'groups': album_object.get('Groups', []),
            'track_urls': track_urls,
        })
    return albums


def get_worklist(cache: dict, groups_only: bool, data_path: str) -> List[dict]:
    # albums still missing an id of either kind, most tracks first so a partial run buys the most.
    # every album with a Bandcamp url counts unless groups_only narrows it
    worklist = []
    for album in read_albums(data_path):
        if groups_only and not any(g in INCLUDED_GROUPS for g in album['groups']):
            continue
        needs_tracks = any(u not in cache['tracks'] for u in album['track_urls'])
        needs_album = normalize_url(album['url']) not in cache['albums']
        if needs_tracks or needs_album:
            worklist.append(album)
    worklist.sort(key=lambda a: -len(a['track_urls']))
    return worklist


# ---------------------------------------------------------------- harvesting

def open_browser(cdp_url: str, headless: bool):
    from playwright.sync_api import sync_playwright
    playwright = sync_playwright().start()
    if cdp_url:
        # the user's own Chrome: borrow a tab, and never close the context or browser
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        return playwright, browser, context, True
    profile_path = os.path.join(file_path, '.bandcamp-profile')
    return playwright, None, playwright.chromium.launch_persistent_context(profile_path, headless=headless), False


def harvest(args, fetch_page=None) -> None:
    cache = load_cache(args.cache)
    worklist = get_worklist(cache, args.groups_only, args.data_path)
    if args.album:
        wanted = [a.lower() for a in args.album]
        worklist = [a for a in worklist if any(w in a['url'].lower() for w in wanted)]
        if not worklist:
            print(f'Nothing matched {args.album}.')
            return
    if args.limit:
        worklist = worklist[:args.limit]

    print(f'{len(worklist)} albums still need fetching')
    if not worklist:
        print('Nothing to do -- the cache already covers every album.')
        return

    playwright = browser = context = page = None
    borrowed = False
    if fetch_page is None:
        playwright, browser, context, borrowed = open_browser(args.cdp, args.headless)
        page = context.new_page()

        def fetch_page(url):
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            # state='attached': a <script> tag is never 'visible'
            page.wait_for_selector('script[type="application/ld+json"]', state='attached', timeout=30000)
            return page.content()

    try:
        for index, album in enumerate(worklist, start=1):
            print(f'[{index}/{len(worklist)}] {album["url"]}')
            try:
                page_html = fetch_page(album['url'])
            except Exception as error:
                print(f'    FAILED: {error}')
                continue
            track_ids = parse_track_ids(page_html)
            album_id = parse_album_id(page_html)
            if not track_ids and not album_id:
                print('    no ids found -- page may have been the bot challenge')
                continue
            cache['tracks'].update(track_ids)
            if album_id:
                cache['albums'][normalize_url(album['url'])] = album_id
            print(f'    +{len(track_ids)} track ids' + (f', album id {album_id}' if album_id else ''))
            save_cache(cache, args.cache)  # save as we go, so an interrupted run keeps its progress
            if index < len(worklist):
                time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))
    finally:
        if page:
            page.close()
        if not borrowed:
            if context:
                context.close()
            if browser:
                browser.close()
        if playwright:
            playwright.stop()

    save_cache(cache, args.cache)
    print(f'\nDone. {len(cache["tracks"])} track ids and {len(cache["albums"])} album ids cached.')


# ---------------------------------------------------------------- writing the wiki

def split_documents(text: str) -> List[List[str]]:
    # hsmusic YAML is a stream of documents separated by a bare '---' at column 0. keep each
    # separator with the document it precedes, so rejoining is lossless
    documents, current = [], []
    for line in text.split('\n'):
        if line.rstrip() == '---':
            documents.append(current)
            current = [line]
        else:
            current.append(line)
    documents.append(current)
    return documents


def find_bandcamp_url(document: List[str]) -> str:
    in_urls = False
    for line in document:
        if line.startswith('URLs:'):
            in_urls = True
            continue
        if in_urls:
            if line.startswith('- '):
                url = line[2:].strip().strip('"\'')
                if 'bandcamp.com' in url:
                    return normalize_url(url)
                continue
            if KEY_PATTERN.match(line):
                in_urls = False
    return ''


def insert_field(document: List[str], field: str, value: int,
                 identity_fields: tuple, opening_field: str, line_suffix: str) -> bool:
    insert_at = None
    for index, line in enumerate(document):
        if not KEY_PATTERN.match(line):
            continue  # list item or continuation of the field above
        if line.startswith(field + ':'):
            return False  # already recorded
        if line.startswith(identity_fields):
            insert_at = index + 1
            continue
        if insert_at is not None:
            break
        if line.startswith(opening_field):
            insert_at = index + 1
    if insert_at is None:
        return False
    # step over any list items belonging to the last identity field
    while insert_at < len(document) and not KEY_PATTERN.match(document[insert_at]) and document[insert_at].strip():
        insert_at += 1
    document.insert(insert_at, f'{field}: {value}{line_suffix}')
    return True


def apply_to_wiki(cache: dict, dry_run: bool, data_path: str) -> None:
    tracks_added = albums_added = files_changed = 0
    tracks_present = albums_present = tracks_missing = albums_missing = 0

    for album_file in sorted(glob.glob(os.path.join(data_path, 'album', '*.yaml'))):
        # newline='' so line endings survive untranslated; some of these files are CRLF
        with open(album_file, 'r', encoding='utf8', newline='') as f:
            original = f.read()
        line_suffix = '\r' if '\r\n' in original else ''
        documents = split_documents(original)
        added_here = 0

        for document in documents:
            is_album = any(line.startswith('Album:') for line in document)
            is_track = any(line.startswith('Track:') for line in document)
            if not is_album and not is_track:
                continue

            url = find_bandcamp_url(document)
            if is_album:
                if any(line.startswith(ALBUM_FIELD + ':') for line in document):
                    albums_present += 1
                    continue
                album_id = cache['albums'].get(url) if url else None
                if not album_id:
                    albums_missing += 1
                    continue
                if insert_field(document, ALBUM_FIELD, album_id, ALBUM_IDENTITY_FIELDS, 'Album:', line_suffix):
                    added_here += 1
                    albums_added += 1
            else:
                if any(line.startswith(TRACK_FIELD + ':') for line in document):
                    tracks_present += 1
                    continue
                if not url:
                    continue
                track_id = cache['tracks'].get(url)
                if not track_id:
                    tracks_missing += 1
                    continue
                if insert_field(document, TRACK_FIELD, track_id, TRACK_IDENTITY_FIELDS, 'Track:', line_suffix):
                    added_here += 1
                    tracks_added += 1

        if added_here:
            files_changed += 1
            patched = '\n'.join('\n'.join(d) for d in documents)
            # the rejoin is only safe if nothing else moved
            if len(patched.split('\n')) != len(original.split('\n')) + added_here:
                print(f'  !! {os.path.basename(album_file)}: line count off, skipping to be safe')
                continue
            print(f'  {os.path.basename(album_file)}: +{added_here}')
            if not dry_run:
                with open(album_file, 'w', encoding='utf8', newline='') as f:
                    f.write(patched)

    verb = 'Would add' if dry_run else 'Added'
    print()
    print(f'{verb} {tracks_added} track ids and {albums_added} album ids across {files_changed} files')
    print(f'already recorded: {tracks_present} tracks, {albums_present} albums')
    print(f'no id known yet:  {tracks_missing} tracks, {albums_missing} albums')


# ---------------------------------------------------------------- cli

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)

    harvest_parser = commands.add_parser('harvest', help='read ids off Bandcamp into the cache')
    harvest_parser.add_argument('--cdp', default='', help='attach to a running Chrome, e.g. http://localhost:9222')
    harvest_parser.add_argument('--headless', action='store_true', help='hide the browser (likelier to be challenged)')
    harvest_parser.add_argument('--official-and-fandom', action='store_true', dest='groups_only',
                                help='only albums in the Official Discography or Fandom groups, '
                                     'rather than every album on Bandcamp')
    harvest_parser.add_argument('--limit', type=int, default=0, help='only the N biggest albums')
    harvest_parser.add_argument('--album', action='append', default=[], help='only albums whose url contains this')
    harvest_parser.add_argument('--data-path', default=DEFAULT_DATA_PATH,
                               help='your hsmusic-data clone (the folder holding album/)')
    harvest_parser.add_argument('--cache', default=CACHE_PATH, help='where to read/write ids')

    apply_parser = commands.add_parser('apply', help='write cached ids into hsmusic-data')
    apply_parser.add_argument('--dry-run', action='store_true', help='report changes without writing')
    apply_parser.add_argument('--data-path', default=DEFAULT_DATA_PATH,
                               help='your hsmusic-data clone (the folder holding album/)')
    apply_parser.add_argument('--cache', default=CACHE_PATH, help='where to read ids from')

    list_parser = commands.add_parser('list', help='show what still needs fetching')
    list_parser.add_argument('--official-and-fandom', action='store_true', dest='groups_only',
                             help='only albums in the Official Discography or Fandom groups')
    list_parser.add_argument('--data-path', default=DEFAULT_DATA_PATH,
                               help='your hsmusic-data clone (the folder holding album/)')
    list_parser.add_argument('--cache', default=CACHE_PATH, help='where to read ids from')

    args = parser.parse_args()
    cache = load_cache(args.cache)
    print(f'{len(cache["tracks"])} track ids and {len(cache["albums"])} album ids in cache\n')

    if args.command == 'harvest':
        harvest(args)
    elif args.command == 'apply':
        apply_to_wiki(cache, args.dry_run, args.data_path)
    else:
        worklist = get_worklist(cache, args.groups_only, args.data_path)
        print(f'{len(worklist)} albums still need fetching\n')
        try:
            for album in worklist:
                print(f'{len(album["track_urls"]):>6}  {album["url"]}')
        except BrokenPipeError:
            pass  # piped into head or less, which closed early
