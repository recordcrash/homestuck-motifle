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

EXCLUDED_ALBUMS = ['hiveswap-act-1-ost', 'hiveswap-act-2-ost', 'hiveswap-friendsim', 'the-grubbles', 'homestuck-vol-1-4', 'genesis-frog', 'sburb']

# Songs that aren't fun to play
EXCLUDED_SONGS = [
    'lame-and-old-webcomic-voluem-10-mega-milx', # fuck you nik of links
    'special-delivery', # I cannot hear a single of these references
    'please-help-me-i-am-in-pain', # this song personally offends me
    'crystalmegamix',
    'waste-of-a-track-slot',
    'credit-shack',
    'licord-nacrasty',
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
START_DATETIME = datetime.datetime(2023, 8, 29, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)

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
    # ugh, seems to be the only case where this matters
    if (string == 'MeGaLoVania'):
        return 'MeGaLoVania'
    string = re.split(' ', string)
    string = "-".join(string)
    string = re.sub('&', 'and', string)
    string = re.sub('[^a-zA-Z0-9\-]', '', string)
    string = re.sub('-{2,}', '-', string)
    string = re.sub('^-+|-+$', '', string).lower()
    return string

def load_slugs(album_path) -> dict:
    # iterates over all the songs, and either takes it's 'Directory' field or calculates it
    # by using normalize_wiki_string, then adds it to a dictionary with 'track:slug' as the key
    # and the full track name (song['Track']) as the key
    album_names = [os.path.splitext(album)[0] for album in os.listdir(album_path)
                if os.path.splitext(album)[1] == '.yaml']
    
    print(f'Slugging {len(album_names)} albums...')

    slugs_dict = {}
    for album_name in album_names:
        potential_songs = load_file(os.path.join(album_path, f"{album_name}.yaml"))
        album_object = next((album for album in potential_songs if 'Album' in album), None)
        album_lacks_art = 'Has Track Art' in album_object and album_object['Has Track Art'] == False
        for song in potential_songs:
            if song is None:
                continue
            # if it contains the field Originally Released As, skip it
            if 'Originally Released As' in song:
                continue
            if all(x in song for x in ['Track', 'URLs']):
                song_name = song['Track']
                song_slug = normalize_wiki_string(song_name)
                is_official = any(group in COUNTED_REFERENCE_GROUPS for group in album_object['Groups'])
                is_fandom = 'Fandom' in album_object['Groups'] if 'Groups' in song else False
                if album_lacks_art or ('Has Cover Art' in song and song['Has Cover Art'] == False):
                    image_url = f'https://hsmusic.wiki/media/album-art/{album_name}/cover.small.jpg'
                else:
                    image_url = f'https://hsmusic.wiki/media/album-art/{album_name}/{song_slug}.small.jpg'
                song_object = {
                    'name': song_name,
                    'albumName': album_object['Album'],
                    'isOfficial': is_official,
                    'isFandom': is_fandom,
                    'imageUrl': image_url,
                }
                # only add the song if it doesn't already exist
                # OR if there's a Directory field
                if 'Directory' in song:
                    slugs_dict[f'track:{song["Directory"]}'] = song_object
                elif f'track:{song_slug}' not in slugs_dict:
                    slugs_dict[f'track:{song_slug}'] = song_object
    print(f'Slugged {len(slugs_dict)} songs')
    return slugs_dict

def get_valid_songs(slugs_dict: dict, album_path) -> List[object]:
    valid_songs = []
    official_slugs = []
    leitmotif_counter = Counter()

    # the file_path has a bunch of files in the scheme "album-name.yaml", we get all the names without
    # the extension

    album_names = [os.path.splitext(album)[0] for album in os.listdir(album_path) 
                   if os.path.splitext(album)[1] == '.yaml']

    for album_name in album_names:
        print(f'Loading {album_name}...')
        if album_name in EXCLUDED_ALBUMS:
                    print(f'Skipping {album_name} because it is excluded')
                    continue

        potential_songs = load_file(os.path.join(album_path, f"{album_name}.yaml"))
        
        # we only want to include albums that have at least one group in GAME_GROUPS
        album_object = next((album for album in potential_songs if 'Album' in album), None)
        album_lacks_art = 'Has Track Art' in album_object and album_object['Has Track Art'] == False
        groups = album_object['Groups'] if 'Groups' in album_object else []
        if not any(group in INCLUDED_GROUPS for group in groups) or any(group in EXCLUDED_GROUPS for group in groups):
            print(f'Skipping {album_name} because it is not a Homestuck album')
            continue
        
        print(f'Loaded {len(potential_songs) - 1} songs from {album_name}')
        readable_album_name = potential_songs[0]['Album']

        for song in potential_songs:
            if song is None:
                continue
            # if it contains the field Originally Released As, skip it
            if 'Originally Released As' in song:
                continue
            if all(x in song for x in ['Track', 'URLs']):
                # print(f'Found song {song["Track"]} from {readable_album_name}')
                song_name = song['Track']
                track_slug_no_prefix = normalize_wiki_string(song_name) if 'Directory' not in song else song['Directory']
                track_slug = f"track:{track_slug_no_prefix}"
                is_official = any(group in COUNTED_REFERENCE_GROUPS for group in groups)
                is_fandom = 'Fandom' in groups
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
                referenced_tracks = list(set(referenced_tracks + sampled_tracks))
                leitmotifs = []
                for referenced_track in referenced_tracks:
                    if referenced_track in slugs_dict:
                        leitmotif_slug = referenced_track
                    else:
                        leitmotif_slug = f"track:{normalize_wiki_string(referenced_track)}"
                    leitmotif_counter[leitmotif_slug] += 1
                    leitmotifs.append(leitmotif_slug)
                # we fetch the url slug for the wiki URL and the image url
                wiki_url = f'https://hsmusic.wiki/track/{track_slug_no_prefix}'
                if album_lacks_art or ('Has Cover Art' in song and song['Has Cover Art'] == False):
                    image_url = f'https://hsmusic.wiki/media/album-art/{album_name}/cover.small.jpg'
                else:
                    image_url = f'https://hsmusic.wiki/media/album-art/{album_name}/{track_slug_no_prefix}.small.jpg'
                urls = song['URLs']
                # urls can contain multiple links, we want to grab the youtube link if it exists (and set urlType to youtube)
                # otherwise, the soundcloud link (and set urlType to soundcloud). if neither exist, url should be set to None
                url = None
                urlType = None
                for urlString in urls:
                    if 'youtu' in urlString:
                        url = urlString
                        urlType = 'youtube'
                        break
                    elif 'soundcloud' in urlString:
                        url = urlString
                        urlType = 'soundcloud'
                if url is not None and track_slug_no_prefix not in EXCLUDED_SONGS:
                    heardle_song = {
                        'slug': track_slug_no_prefix,
                        'name': song_name,
                        'artist': artists,  
                        'albumName': readable_album_name,
                        'leitmotifs': leitmotifs,
                        'nLeitmotifs': len(leitmotifs),
                        'wikiUrl': wiki_url,
                        'imageUrl': image_url,
                        'isOfficial': is_official,
                        'isFandom': is_fandom,
                        'url': url,
                        'urlType': urlType
                    }
                    if (artists, song_name) not in [(song['artist'], song['name']) for song in valid_songs]:
                        valid_songs.append(heardle_song)
                    else:
                        print(f'Skipping {song_name} because it is a duplicate')
                else:
                    print(f'Skipping {song_name} because it has no URL')
    print(f"{len(valid_songs)} songs added")
    random.Random(612).shuffle(valid_songs)

    return valid_songs, leitmotif_counter, official_slugs

def get_guesses_array(slugs_dict, leitmotif_counter: Counter, official_slugs, common_leitmotif_threshold: int, uncommon_leitmotif_threshold: int, rare_leitmotif_threshold: int):
    # adds metadata to the slugs_dict to convert it into a guesses array
    # this allows us to calculate if a leitmotif is common, uncommon, or rare
    # and create a final "guesses array" with it that we can use in the game as "valid guesses"
    guesses_array = []
    for slug, song in slugs_dict.items():
        if slug in leitmotif_counter:
            count = leitmotif_counter[slug]
            song['slug'] = slug
            if count == 1:
                song['rarity'] = 1
            elif count >= common_leitmotif_threshold:
                song['rarity'] = 5
            elif count >= uncommon_leitmotif_threshold:
                song['rarity'] = 4
            elif count >= rare_leitmotif_threshold:
                song['rarity'] = 3
            elif count < rare_leitmotif_threshold:
                song['rarity'] = 2
            if slug not in official_slugs:
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
    print(f'Found {len(common_leitmotifs)} common leitmotifs, {len(uncommon_leitmotifs)} uncommon leitmotifs, and {len(rare_leitmotifs)} rare leitmotifs')
    print(f'Common leitmotifs: {common_leitmotifs}')
    print(f'Uncommon leitmotifs: {uncommon_leitmotifs}')
    print(f'Rare leitmotifs: {rare_leitmotifs}')

    # add all sets into guessable_leitmotifs
    guessable_leitmotifs = common_leitmotifs.union(uncommon_leitmotifs).union(rare_leitmotifs)
    # with official_counter we can filter guessable_leitmotifs into official_leitmotifs
    official_leitmotifs = set()
    for leitmotif in guessable_leitmotifs:
        if leitmotif in official_counter:
            official_leitmotifs.add(leitmotif)
            

    # filter out songs that have less than min_n_references leitmotifs
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
    
    slugs_dict = load_slugs(album_path)

    # check if an old song file exist
    old_game_songs_file = None
    old_game_songs = []
    if os.path.exists(os.path.join(OUTPUT_PATH, 'game_songs_old.json')):
        with open(os.path.join(OUTPUT_PATH, 'game_songs_old.json'), 'r') as f:
            old_game_songs_file = json.loads(f.read())
    
    # if it exists, and the date is before the original date, we want to use the old songs and remove them from being picked
    if old_game_songs_file is not None:
        day_difference = (START_DATETIME - ORIGINAL_DATETIME).days
        for index in range(day_difference):
            old_game_songs.append(old_game_songs_file[index])
        print(f'Found {len(old_game_songs)} old songs: {old_game_songs}')

    songs, leitmotif_counter, official_slugs = get_valid_songs(slugs_dict, album_path)

    five_hundred_most_common = leitmotif_counter.most_common(500)
    # pretty print so it's one per line
    print('\n'.join([f'{leitmotif}: {count}' for leitmotif, count in five_hundred_most_common]))

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

    # add the old songs to the filtered songs
    game_songs = old_game_songs + filtered_songs

    guesses_array = get_guesses_array(slugs_dict, leitmotif_counter, official_slugs, common_leitmotif_threshold, uncommon_leitmotif_threshold, rare_leitmotif_threshold)
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