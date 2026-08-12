# Requires pip install pyyaml if you ever want to rebake this for whatever reason

from typing import List
import yaml
import os
import json
import re
import random
import datetime
from collections import Counter

COUNTED_REFERENCE_GROUPS = ['Official Discography', 'group:official']

INCLUDED_GROUPS = [*COUNTED_REFERENCE_GROUPS, 'Fandom']

EXCLUDED_GROUPS = ['Desynced']

EXCLUDED_ALBUMS = ['hiveswap-act-1-ost', 'hiveswap-act-2-ost', 'hiveswap-friendsim', 'the-grubbles', 'homestuck-vol-1-4', 'genesis-frog', 'sburb',
                   'call-and-new', 'call-and-new-2-locomotif', 'c-a-n-w-a-v-e', 'c-a-n-w-a-v-e-2']

# Songs that aren't fun to play
EXCLUDED_SONGS = [
    'lame-and-old-webcomic-voluem-10-mega-milx', # fuck you nik of links
    'special-delivery', # I cannot hear a single of these references
    'please-help-me-i-am-in-pain', # this song personally offends me
    'crystalmegamix',
    'waste-of-a-track-slot',
    'credit-shack',
    'licord-nacrasty',
    'im-not-saying-anything'
]

# Motifs that are generally just memes that shouldn't count for making a song playable
DISCARDED_MOTIFS = [
    'the-nutshack-intro',
    'bowmans-credit-score',
    'snow-halation',
    'dk-rap',
    'meet-the-flintstones'
]

# This will never change. Since the game has gone live, we must preserve songs between this date and...
ORIGINAL_DATETIME = datetime.datetime(2023, 8, 9, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)

# The first day of the newly generated songs
START_DATETIME = datetime.datetime(2026, 8, 13, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)

# The target end date until which we will loop songs if we run out
END_DATETIME = datetime.datetime(2029, 4, 13, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)

# How quickly a song's scheduling priority decays with age. Every this many years, music is half as
# likely to be picked early; undated albums are treated as fairly old
SHUFFLE_SEED = 716

RECENCY_HALF_LIFE_YEARS = 5.0
UNDATED_RECENCY_WEIGHT = 0.1

# the preview wiki, since that's the branch of hsmusic-data this reads, and it carries tracks the
# live site doesn't have yet
WIKI_URL_BASE = 'https://preview.hsmusic.wiki'

LEGACY_WIKI_TRACK_BASE = 'https://hsmusic.wiki/track'

def normalize_wiki_url(url: str) -> str:
    if url and url.startswith(LEGACY_WIKI_TRACK_BASE):
        return url.replace(LEGACY_WIKI_TRACK_BASE, f'{WIKI_URL_BASE}/track', 1)
    return url

# art is served from its own host, not from a path under the wiki
MEDIA_URL_BASE = 'https://media.hsmusic.wiki/album-art'

LEGACY_MEDIA_URL_BASES = [
    'https://hsmusic.wiki/thumb/album-art',
    'https://hsmusic.wiki/media/album-art',
]

def normalize_media_url(url: str) -> str:
    # moves art URLs from older bakes onto the current media host
    if not url:
        return url
    for legacy_base in LEGACY_MEDIA_URL_BASES:
        if url.startswith(legacy_base):
            return url.replace(legacy_base, MEDIA_URL_BASE, 1)
    return url

file_path = os.path.dirname(os.path.realpath(__file__))

OUTPUT_PATH = os.path.join(file_path, 'static/')

def load_file(path: str) -> List[object]:
    with open(path, 'r', encoding='utf8') as f:
        subfiles = yaml.load_all(f, Loader=yaml.SafeLoader)

        objs = []
        for subfile in subfiles:
            objs.append(subfile)

    return objs 

def normalize_wiki_string(string: str) -> str:
    # a port of getKebabCase from hsmusic-wiki (src/common-util/wiki-data.js), which is what the wiki
    # itself uses to derive a directory from a name
    string = string.replace(' ', '-')

    # punctuation as words
    string = string.replace('&', '-and-').replace('+', '-plus-').replace('%', '-percent-')

    # punctuation which only divides words, not single characters
    string = re.sub(r'(\b[^\s\-.]{2,})\.', r'\1-', string)
    string = re.sub(r'\.([^\s\-.]{2,})\b', r'-\1', string)

    # punctuation which doesn't divide a number following a non-number
    string = re.sub(r'(?<=[0-9])\^', '-', string)
    string = re.sub(r'\^(?![0-9])', '-', string)

    # general punctuation which always separates surrounding words
    string = re.sub(r'[/@#$%*()_=,\[\]{}|\\;:<>?`~]', '-', string)
    string = re.sub(r'[–-—]', '-', string)  # en dash, em dash

    # accented characters
    for accented, plain in [('áâäàå', 'a'), ('çč', 'c'), ('éêëè', 'e'),
                            ('íîïì', 'i'), ('óôöò', 'o'), ('úûüù', 'u')]:
        string = re.sub(f'[{accented}]', plain, string, flags=re.IGNORECASE)

    string = re.sub(r'[^a-z0-9-]', '', string, flags=re.IGNORECASE)
    string = re.sub(r'-{2,}', '-', string)
    string = re.sub(r'^-+|-+$', '', string)
    return string.lower()

def legacy_normalize_wiki_string(string: str) -> str:
    # an older, less accurate normalization. only used to recognise slugs baked into songs that have
    # already been played, so their motif cards still resolve
    if string in ('MeGaLoVania', 'iRRRRRRRRECONCILA8LE'):
        return string
    string = "-".join(re.split(' ', string))
    string = re.sub('&', 'and', string)
    string = re.sub(r'[^a-zA-Z0-9\-]', '', string)
    string = re.sub('-{2,}', '-', string)
    string = re.sub('^-+|-+$', '', string).lower()
    return string

BANDCAMP_IDS_PATH = os.path.join(file_path, 'bandcamp_ids.json')

_bandcamp_ids = None

def get_bandcamp_ids() -> dict:
    # Fallback for tracks hsmusic-data has no 'Bandcamp Track ID' for yet. Populated by
    # bandcampIds.py
    global _bandcamp_ids
    if _bandcamp_ids is None:
        if os.path.exists(BANDCAMP_IDS_PATH):
            with open(BANDCAMP_IDS_PATH, 'r', encoding='utf8') as f:
                data = json.load(f)
            # the cache separates tracks from albums; older ones were a flat track map
            _bandcamp_ids = data.get('tracks', data) if isinstance(data, dict) else {}
        else:
            _bandcamp_ids = {}
    return _bandcamp_ids

def normalize_bandcamp_url(url: str) -> str:
    # must match the form bandcampIds.py keys its cache by
    url = re.sub(r'^https?://', '', url.strip())
    return url.split('?')[0].split('#')[0].rstrip('/').lower()

def parse_wiki_date(date_value) -> datetime.date:
    # hsmusic writes dates as 'December 12, 2010', occasionally with a time attached
    if isinstance(date_value, datetime.datetime):
        return date_value.date()
    if isinstance(date_value, datetime.date):
        return date_value
    if not date_value:
        return None
    text = str(date_value).strip()
    for date_format in ('%B %d, %Y %H:%M:%S', '%B %d, %Y', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def get_recency_weight(release_date) -> float:
    # a weight rather than a hard sort: sorting strictly by date would front-load every recent
    # album and leave a decade of older music queued behind it
    if release_date is None:
        return UNDATED_RECENCY_WEIGHT
    age_years = (datetime.date.today() - release_date).days / 365.25
    if age_years < 0:
        age_years = 0
    return 0.5 ** (age_years / RECENCY_HALF_LIFE_YEARS)


def is_rerelease(song) -> bool:
    # a re-release points at the track it duplicates, and must not be slugged or played as its own.
    # 'Main Release' is the current wiki field; 'Originally Released As' is its old name
    return 'Originally Released As' in song or 'Main Release' in song

def get_art_url(song, album_object, album_name, track_slug) -> str:
    # a track shows its own art when it has any, and the album cover otherwise. animated art has no
    # generated thumbnail, so gifs are linked whole while everything else uses the .small.jpg thumb
    if has_own_track_art(song, album_object):
        file_name = track_slug
        # 'Track Artwork' entries carry their own extension, which is how animated track art is declared
        artwork = song.get('Track Artwork')
        if isinstance(artwork, list):
            artwork = artwork[0] if artwork else None
        artwork_extension = artwork.get('File Extension') if isinstance(artwork, dict) else None
        extension = (song.get('Cover Art File Extension') or artwork_extension
                     or album_object.get('Track Art File Extension') or 'jpg')
    else:
        file_name = 'cover'
        extension = album_object.get('Cover Art File Extension') or 'jpg'
    if extension == 'gif':
        return f'{MEDIA_URL_BASE}/{album_name}/{file_name}.gif'
    return f'{MEDIA_URL_BASE}/{album_name}/{file_name}.small.jpg'

def get_track_slug(song, album_object, album_name) -> str:
    # a track's directory is its explicit Directory field or its normalized name, plus the album's
    # suffix when the track sets 'Suffix Directory' or the album sets 'Suffix Track Directories'.
    # the suffix is what separates same-named tracks: Retcon (2018)'s '-' is 'descend-retcon',
    # while plain 'descend' is Homestuck Vol. 5's
    slug = song['Directory'] if 'Directory' in song else normalize_wiki_string(song['Track'])
    # the track's own flag wins when present, including 'Suffix Directory: false' to opt out
    # of an album that suffixes everything
    if 'Suffix Directory' in song:
        should_suffix = song['Suffix Directory']
    else:
        should_suffix = album_object.get('Suffix Track Directories', False)
    if should_suffix:
        suffix = album_object.get('Directory Suffix') or album_object.get('Directory') or album_name
        slug = f'{slug}-{suffix}'
    return slug

def has_own_track_art(song, album_object) -> bool:
    # a track only has its own art file when it names artists for it, via either 'Cover Artists' or
    # 'Track Artwork', or when its album names a default set. otherwise the wiki serves the cover
    if album_object.get('Has Track Art') == False or song.get('Has Cover Art') == False:
        return False
    return bool(song.get('Cover Artists') or song.get('Track Artwork') or album_object.get('Default Track Cover Artists'))

def get_is_official(album_object, song, album_name) -> bool:
    song_exceptions = [
        ('penumbra-phantasm', 'Toby Fox')
    ]
    is_album_official = any(group in COUNTED_REFERENCE_GROUPS for group in album_object.get('Groups', []))
    # check if the song is an unreleased official song like PP
    song_slug = get_track_slug(song, album_object, album_name)
    song_authors = song['Artists'] if 'Artists' in song else []
    is_song_exception = any(song_slug == song_exception[0] and song_author == song_exception[1] for song_exception in song_exceptions for song_author in song_authors)
    return is_album_official or is_song_exception
    

def load_slugs(album_path) -> dict:
    # iterates over all the songs, and either takes it's 'Directory' field or calculates it
    # by using normalize_wiki_string, then adds it to a dictionary with 'track:slug' as the key
    # and the full track name (song['Track']) as the key
    # sorted, because os.listdir order varies by filesystem and decides which of two same-named
    # tracks is kept
    album_names = sorted(os.path.splitext(album)[0] for album in os.listdir(album_path)
                         if os.path.splitext(album)[1] == '.yaml')
    
    print(f'Slugging {len(album_names)} albums...')

    slugs_dict = {}
    # maps a normalized track *name* to its slug, so that references written by name
    # still resolve when the track has an explicit Directory that differs from its name
    # (e.g. 'The Will to Fight (Original Mix) [Denizen Strife]' -> track:the-will-to-fight-original-mix)
    names_dict = {}
    # slugs that came from a re-release. they're kept so references pointing at a re-release's own
    # directory still resolve, but the canonical track always takes the slug back if it turns up
    rerelease_slugs = set()
    # slugs from the older normalization, baked into the leitmotif lists of songs already played.
    # merged in at the end as aliases, never overriding a real slug
    legacy_aliases = {}
    # every key in slugs_dict, alias or not, mapped to the slug the wiki actually uses today
    canonical_slugs = {}
    for album_name in album_names:
        potential_songs = load_file(os.path.join(album_path, f"{album_name}.yaml"))
        album_object = next((album for album in potential_songs if 'Album' in album), None)
        if album_object is None:
            continue
        for song in potential_songs:
            if song is None:
                continue
            song_is_rerelease = is_rerelease(song)
            if 'Track' in song:
                song_name = song['Track']
                song_slug = get_track_slug(song, album_object, album_name)
                is_official = get_is_official(album_object, song, album_name)
                is_fandom = not is_official and 'Fandom' in album_object['Groups'] if 'Groups' in album_object else False
                image_url = get_art_url(song, album_object, album_name, song_slug)
                song_object = {
                    'name': song_name,
                    'albumName': album_object['Album'],
                    'isOfficial': is_official,
                    'isFandom': is_fandom,
                    'imageUrl': image_url,
                }
                # a slug is claimed if it doesn't already exist, if the track states its directory
                # explicitly, or if the slug currently belongs to a mere re-release
                full_slug = f'track:{song_slug}'
                slug_is_free = full_slug not in slugs_dict or full_slug in rerelease_slugs
                has_explicit_directory = 'Directory' in song or song_slug != normalize_wiki_string(song_name)
                if slug_is_free or (has_explicit_directory and not song_is_rerelease):
                    slugs_dict[full_slug] = song_object
                    if song_is_rerelease:
                        rerelease_slugs.add(full_slug)
                    else:
                        rerelease_slugs.discard(full_slug)
                canonical_slugs[full_slug] = full_slug
                legacy_slug = song['Directory'] if 'Directory' in song else legacy_normalize_wiki_string(song_name)
                if f'track:{legacy_slug}' != full_slug and not song_is_rerelease:
                    legacy_aliases.setdefault(f'track:{legacy_slug}', (song_object, full_slug))
                # tracks flagged 'Always Reference By Directory' are ambiguous by name, so they can't be
                # looked up that way. re-releases never win a name either, and first one wins otherwise
                normalized_name = normalize_wiki_string(song_name)
                if not song.get('Always Reference By Directory') and not song_is_rerelease and normalized_name not in names_dict:
                    names_dict[normalized_name] = full_slug
    alias_count = 0
    for legacy_slug, (song_object, canonical_slug) in legacy_aliases.items():
        if legacy_slug not in slugs_dict:
            slugs_dict[legacy_slug] = song_object
            canonical_slugs[legacy_slug] = canonical_slug
            alias_count += 1
    print(f'Slugged {len(slugs_dict)} songs ({alias_count} of them legacy aliases)')
    return slugs_dict, names_dict, canonical_slugs

def resolve_track_reference(reference: str, slugs_dict: dict, names_dict: dict) -> str:
    # a Referenced/Sampled Tracks entry is either an explicit 'track:directory' or a track name
    if reference in slugs_dict:
        return reference
    normalized = normalize_wiki_string(reference)
    if f'track:{normalized}' in slugs_dict:
        return f'track:{normalized}'
    # the name doesn't match any directory, so try resolving it as a track name
    return names_dict.get(normalized, f'track:{normalized}')

def get_valid_songs(slugs_dict: dict, names_dict: dict, album_path) -> List[object]:
    valid_songs = []
    official_slugs = []
    leitmotif_counter = Counter()
    bandcamp_id_sources = Counter()

    # the file_path has a bunch of files in the scheme "album-name.yaml", we get all the names without
    # the extension

    # sorted, because os.listdir order varies by filesystem and decides which of two same-named
    # tracks is kept
    album_names = sorted(os.path.splitext(album)[0] for album in os.listdir(album_path)
                         if os.path.splitext(album)[1] == '.yaml')

    for album_name in album_names:
        print(f'Loading {album_name}...')
        if album_name in EXCLUDED_ALBUMS:
            print(f'Skipping {album_name} because it is excluded')
            continue

        potential_songs = load_file(os.path.join(album_path, f"{album_name}.yaml"))
        
        # we only want to include albums that have at least one group in GAME_GROUPS
        album_object = next((album for album in potential_songs if 'Album' in album), None)
        if album_object is None:
            continue
        groups = album_object['Groups'] if 'Groups' in album_object else []
        if not any(group in INCLUDED_GROUPS for group in groups) or any(group in EXCLUDED_GROUPS for group in groups):
            print(f'Skipping {album_name} because it is not a Homestuck album')
            continue
        
        print(f'Loaded {len(potential_songs) - 1} songs from {album_name}')
        readable_album_name = potential_songs[0]['Album']
        album_release_date = parse_wiki_date(album_object.get('Date'))

        for song in potential_songs:
            if song is None:
                continue
            # skip re-releases, they duplicate a track that already exists elsewhere
            if is_rerelease(song):
                continue
            if all(x in song for x in ['Track', 'URLs']):
                # print(f'Found song {song["Track"]} from {readable_album_name}')
                song_name = song['Track']
                track_slug_no_prefix = get_track_slug(song, album_object, album_name)
                track_slug = f"track:{track_slug_no_prefix}"
                is_official = get_is_official(album_object, song, album_name)
                is_fandom = not is_official and 'Fandom' in groups
                if is_official:
                    official_slugs.append(track_slug)
                album_artists = potential_songs[0]['Artists'] if 'Artists' in potential_songs[0] else []
                artists = song['Artists'] if 'Artists' in song else album_artists
                for artist in artists:
                    # if artist doesn't contain artist:, slug it and put it before the artist name
                    if 'artist:' not in artist:
                        # remove anything between parentheses and then trim the end
                        normalized_artist = re.sub(r'\([^)]*\)', '', artist).strip()
                        artist_slug = f"artist:{normalize_wiki_string(normalized_artist)}"
                        artist_index = artists.index(artist)
                        artists[artist_index] = artist_slug

                referenced_tracks = song['Referenced Tracks'] if 'Referenced Tracks' in song else []
                sampled_tracks = song['Sampled Tracks'] if 'Sampled Tracks' in song else []
                leitmotifs = []
                samples = []
                for referenced_track in referenced_tracks:
                    leitmotif_slug = resolve_track_reference(referenced_track, slugs_dict, names_dict)
                    leitmotif_counter[leitmotif_slug] += 1
                    leitmotifs.append(leitmotif_slug)
                # samples
                for sample in sampled_tracks:
                    sample_slug = resolve_track_reference(sample, slugs_dict, names_dict)
                    samples.append(sample_slug)
                # we fetch the url slug for the wiki URL and the image url
                wiki_url = f'{WIKI_URL_BASE}/track/{track_slug_no_prefix}'
                image_url = get_art_url(song, album_object, album_name, track_slug_no_prefix)
                urls = song['URLs']
                # urls can contain multiple links, we want to grab the youtube link if it exists (and set urlType to youtube)
                # otherwise, the soundcloud link (and set urlType to soundcloud). if neither exist, url should be set to None
                url = None
                urlType = None
                for urlString in urls:
                    if not urlString:
                        print(f'WARNING: Skipping {song_name} because it somehow has a None URL!')
                        continue
                    if 'youtu' in urlString:
                        url = urlString
                        urlType = 'youtube'
                        break
                    elif 'soundcloud' in urlString:
                        url = urlString
                        urlType = 'soundcloud'
                # youtube and soundcloud are preferred because the game can drive them invisibly.
                # bandcamp needs its own player, and needs the track's numeric id
                bandcamp_track_id = None
                if url is None:
                    for urlString in urls:
                        if not urlString or 'bandcamp.com' not in urlString:
                            continue
                        found_id = song.get('Bandcamp Track ID')
                        if found_id:
                            bandcamp_id_sources['wiki'] += 1
                        else:
                            # not in the wiki yet, so try the local cache
                            found_id = get_bandcamp_ids().get(normalize_bandcamp_url(urlString))
                            if found_id:
                                bandcamp_id_sources['cache'] += 1
                        if found_id:
                            url = urlString
                            urlType = 'bandcamp'
                            bandcamp_track_id = found_id
                            break
                if url is not None and track_slug_no_prefix not in EXCLUDED_SONGS:
                    heardle_song = {
                        'slug': track_slug_no_prefix,
                        'name': song_name,
                        'artist': artists,  
                        'albumName': readable_album_name,
                        'leitmotifs': leitmotifs,
                        'samples': samples,
                        'nLeitmotifs': len(leitmotifs),
                        'wikiUrl': wiki_url,
                        'imageUrl': image_url,
                        'isOfficial': is_official,
                        'isFandom': is_fandom,
                        'url': url,
                        'urlType': urlType
                    }
                    if bandcamp_track_id:
                        heardle_song['bandcampTrackId'] = bandcamp_track_id
                    heardle_song['_releaseDate'] = album_release_date
                    if (artists, song_name) not in [(song['artist'], song['name']) for song in valid_songs]:
                        valid_songs.append(heardle_song)
                    else:
                        print(f'Skipping {song_name} because it is a duplicate')
                else:
                    print(f'Skipping {song_name} because it has no URL')
    print(f"{len(valid_songs)} songs added")
    print(f"Bandcamp ids: {bandcamp_id_sources['wiki']} from hsmusic-data, "
          f"{bandcamp_id_sources['cache']} from the local cache")

    # Shuffle, biased towards recent releases: Efraimidis-Spirakis weighted sampling, where raising
    # a random number to the power of 1/weight and sorting descending leaves every song able to land
    # anywhere while heavier (newer) ones tend towards the front
    def recency_sort_key(song):
        # the random draw is seeded per song rather than taken from one running sequence, so a
        # song's place depends only on itself. that keeps the order stable when albums are added
        # to the wiki, and means the same seed always means the same schedule
        weight = get_recency_weight(song['_releaseDate'])
        draw = random.Random(f'{SHUFFLE_SEED}:{song["slug"]}').random()
        return draw ** (1 / weight)
    valid_songs.sort(key=recency_sort_key, reverse=True)

    return valid_songs, leitmotif_counter, official_slugs

def get_guesses_array(slugs_dict, leitmotif_counter: Counter, common_leitmotif_threshold: int, uncommon_leitmotif_threshold: int, rare_leitmotif_threshold: int, preserved_slugs: set = None):
    # adds metadata to the slugs_dict to convert it into a guesses array
    # this allows us to calculate if a leitmotif is common, uncommon, or rare
    # and create a final "guesses array" with it that we can use in the game as "valid guesses"
    # motifs referenced only by songs we've already played still have to be guessable, otherwise
    # their cards vanish from those games
    preserved_slugs = preserved_slugs or set()
    guesses_array = []
    for slug, entry in slugs_dict.items():
        if slug in leitmotif_counter or slug in preserved_slugs:
            count = leitmotif_counter.get(slug, 0)
            # copy, because aliases share their entry with the canonical slug
            song = dict(entry)
            song['slug'] = slug
            if count <= 1:
                song['rarity'] = 1
            elif count >= common_leitmotif_threshold:
                song['rarity'] = 5
            elif count >= uncommon_leitmotif_threshold:
                song['rarity'] = 4
            elif count >= rare_leitmotif_threshold:
                song['rarity'] = 3
            elif count < rare_leitmotif_threshold:
                song['rarity'] = 2
            if not song['isOfficial']:
                song['rarity'] -= 1
            if song['rarity'] < 1:
                song['rarity'] = 1
            guesses_array.append(song)
    return guesses_array


def filter_songs(songs: list, old_game_songs: list, leitmotif_counter: Counter, official_slugs: list, 
                 common_leitmotif_threshold: int, uncommon_leitmotif_threshold: int, rare_leitmotif_threshold: int, 
                 min_leitmotifs: int, max_leitmotifs: int):
    # takes the full songs json and filters based on chosen gameplay parameters
    filtered_songs = []
    common_leitmotifs = set()
    uncommon_leitmotifs = set()
    rare_leitmotifs = set()

    # copy leitmotif_counter so we don't modify the original
    official_counter = leitmotif_counter.copy()
    # filter out leitmotifs that aren't official or are too rare
    for leitmotif, count in leitmotif_counter.items():
        if leitmotif not in official_slugs or count < rare_leitmotif_threshold:
            if leitmotif in official_counter:
                del official_counter[leitmotif]
    
    # filter out leitmotifs that appear less than min_leitmotif_counter times
    print(f'Filtering leitmotifs with thresholds {common_leitmotif_threshold}, {uncommon_leitmotif_threshold}, {rare_leitmotif_threshold}...')
    for leitmotif, count in leitmotif_counter.items():
        if count >= common_leitmotif_threshold:
            common_leitmotifs.add(leitmotif)
        elif count >= uncommon_leitmotif_threshold:
            uncommon_leitmotifs.add(leitmotif)
        elif count >= rare_leitmotif_threshold:
            rare_leitmotifs.add(leitmotif)

    # add all sets into guessable_leitmotifs
    guessable_leitmotifs = common_leitmotifs.union(uncommon_leitmotifs).union(rare_leitmotifs)
    # with official_counter we can filter guessable_leitmotifs into official_leitmotifs
    official_leitmotifs = set()
    for leitmotif in guessable_leitmotifs:
        if leitmotif in official_counter:
            official_leitmotifs.add(leitmotif)
            

    # filter out songs that have less than min_leitmotifs leitmotifs
    print(f'Filtering out songs that have less than {min_leitmotifs} leitmotifs or more than {max_leitmotifs}...')
    for song in songs:
        if song['slug'] in [song['slug'] for song in old_game_songs]:
            continue
        set_song_leitmotifs = set(song['leitmotifs'])
        for discarded_motif in DISCARDED_MOTIFS:
                set_song_leitmotifs.discard(f"track:{discarded_motif}")
        if len(set_song_leitmotifs) >= min_leitmotifs and song['nLeitmotifs'] <= max_leitmotifs:
            set_song_leitmotifs = set(song['leitmotifs'])
            # remove meme leitmotifs that shouldn't count
            # for example, the-nutshack-theme
            n_official_songs = len(set_song_leitmotifs.intersection(official_leitmotifs))
            n_common_unofficial_songs = len(set_song_leitmotifs.intersection(common_leitmotifs).difference(official_leitmotifs))
            # for fun gameplay, we want to make sure that there are either official or very well known leitmotifs in the song
            # let's account for these cases:
            # two or more official songs
            # one official song and two or more common songs
            if n_official_songs >= 2 or (n_official_songs >= 1 and n_common_unofficial_songs >= 2):
                filtered_songs.append(song)

    # add starting date
    day = START_DATETIME
    for song in filtered_songs:
        # we store the date in a string format readable by javascript
        song['day'] = day.strftime('%Y-%m-%d')
        day += datetime.timedelta(days=1)
    return filtered_songs

def get_game_data(store: bool = True) -> List[object]:
    file_path = os.path.dirname(os.path.realpath(__file__))
    hsmusic_data_path = os.path.join(file_path, 'hsmusic-data')
    album_path = os.path.join(hsmusic_data_path, 'album')
    
    slugs_dict, names_dict, canonical_slugs = load_slugs(album_path)

    # check if an old song file exist
    old_game_songs_file = None
    old_game_songs = []
    if os.path.exists(os.path.join(OUTPUT_PATH, 'game_songs_old.json')):
        with open(os.path.join(OUTPUT_PATH, 'game_songs_old.json'), 'r') as f:
            old_game_songs_file = json.loads(f.read())
    
    # if it exists, and the date is before the original date, we want to use the old songs and remove them from being picked
    if old_game_songs_file is not None:
        print(f"Using old songs from {ORIGINAL_DATETIME} to {START_DATETIME}")
        for index in range(len(old_game_songs_file)):
            old_song = old_game_songs_file[index]
            # preserved songs keep their slugs and motifs exactly, but their art URLs are rehosted
            old_song['wikiUrl'] = normalize_wiki_url(old_song.get('wikiUrl'))
            # prefer the art the wiki serves for this track today, since both the media host and the
            # cover-vs-track-art rules have changed since these songs were first baked
            old_slug = f"track:{old_song['slug']}"
            current_track = slugs_dict.get(old_slug)
            if current_track:
                old_song['imageUrl'] = current_track['imageUrl']
                # the slug itself stays frozen, but its wiki link should follow the track if the
                # directory the wiki uses for it has changed since this song was scheduled
                canonical_slug = canonical_slugs.get(old_slug, old_slug)
                old_song['wikiUrl'] = f'{WIKI_URL_BASE}/track/{canonical_slug[len("track:"):]}'
            else:
                old_song['imageUrl'] = normalize_media_url(old_song.get('imageUrl'))
            old_game_songs.append(old_song)

    songs, leitmotif_counter, official_slugs = get_valid_songs(slugs_dict, names_dict, album_path)
    # ugly exception, we need to manually add unreleased famous songs to official_slugs
    official_slugs.append('track:penumbra-phantasm')
    official_slugs.append('track:double-midnight')

    five_hundred_most_common = leitmotif_counter.most_common(500)

    common_leitmotif_threshold = 20
    uncommon_leitmotif_threshold = 10
    rare_leitmotif_threshold = 4
    min_leitmotifs = 3
    max_leitmotifs = 999

    filtered_songs = filter_songs(
        songs, old_game_songs, leitmotif_counter, official_slugs,
        common_leitmotif_threshold, 
        uncommon_leitmotif_threshold, 
        rare_leitmotif_threshold,
        min_leitmotifs,
        max_leitmotifs
    )

    print(f'Filtered {len(filtered_songs)} songs')

    for song in filtered_songs:
        song.pop('_releaseDate', None)  # scheduling detail, not part of the game data

    # add the old songs to the filtered songs
    game_songs = old_game_songs + filtered_songs

    # Now, if we have a target END_DATETIME, we loop the songs we have until we reach it.
    if game_songs:
        last_day_str = game_songs[-1]['day']
        last_day = datetime.datetime.strptime(last_day_str, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
        current_day = last_day + datetime.timedelta(days=1)

        # The pool is every distinct song in the order it was first played, which puts the songs we
        # just added at the end: players see all the new songs first, and only then does the loop
        # start over, now including those new songs in its rotation.
        loop_pool = []
        pooled_slugs = set()
        for song in game_songs:
            if song['slug'] not in pooled_slugs:
                pooled_slugs.add(song['slug'])
                loop_pool.append(song)

        # Loop through the pool repeatedly until we reach END_DATETIME. Note this appends to
        # game_songs while reading loop_pool, so the wrap-around actually wraps.
        song_index = 0
        while current_day <= END_DATETIME:
            base_song = loop_pool[song_index % len(loop_pool)]
            looped_song = dict(base_song)
            # Update the day for this looped instance
            looped_song['day'] = current_day.strftime('%Y-%m-%d')
            game_songs.append(looped_song)
            current_day += datetime.timedelta(days=1)
            song_index += 1

    preserved_slugs = {leitmotif for song in old_game_songs for leitmotif in song['leitmotifs']}
    guesses_array = get_guesses_array(slugs_dict, leitmotif_counter, common_leitmotif_threshold, uncommon_leitmotif_threshold, rare_leitmotif_threshold, preserved_slugs)
    print(f'Found {len(guesses_array)} guesses')
    
    # order guesses_array by descending rarity, and then alphabetical order
    guesses_array = sorted(guesses_array, key=lambda k: (-k['rarity'], k['name']))
    if store:
        motifs_path = os.path.join(OUTPUT_PATH, 'game_motifs.json')
        if os.path.exists(motifs_path):
            os.remove(motifs_path)
        with open(motifs_path, 'w') as f:
            f.write(json.dumps(guesses_array, indent=2))

    # count representation of album names in the filtered songs
    album_names = [song['albumName'] for song in game_songs]
    album_counter = Counter(album_names)
    # count representation of is_official
    is_official = [song['isOfficial'] for song in game_songs]
    is_official_counter = Counter(is_official)
    # count representation of url_type
    url_types = [song['urlType'] for song in game_songs]
    url_type_counter = Counter(url_types)
    print(f'Found {url_type_counter["youtube"]} youtube links and {url_type_counter["soundcloud"]} soundcloud links')
    # count representation of rarity per motif
    rarity = [song['rarity'] for song in guesses_array]
    rarity_counter = Counter(rarity)

    if store:
        songs_path = os.path.join(OUTPUT_PATH, 'game_songs.json')
        if os.path.exists(songs_path):
            os.remove(songs_path)
        with open(songs_path, 'w') as f:
            f.write(json.dumps(game_songs, indent=2))

    return game_songs

def backup_old_files():
    # backs up old game_songs.json to store old dates
    # this is so we can revert to the old version if we need to
    # and we can also access it when we're creating new versions
    songs_path = os.path.join(OUTPUT_PATH, 'game_songs.json')
    if os.path.exists(songs_path):
        # remove previous backup
        if os.path.exists(os.path.join(OUTPUT_PATH, 'game_songs_old.json')):
            os.remove(os.path.join(OUTPUT_PATH, 'game_songs_old.json'))
        os.rename(songs_path, os.path.join(OUTPUT_PATH, f'game_songs_old.json'))


if __name__ == '__main__':
    backup_old_files()
    get_game_data(store=True)
