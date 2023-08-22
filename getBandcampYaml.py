# WIP, might never finish because it's a huge pain in the ass

import requests
from bs4 import BeautifulSoup
import yaml
from datetime import date
import sys


def extract_substring(s, keyword, delimiters=['.', '\n']):
    lower_s = s.lower()
    start_idx = lower_s.find(keyword.lower())
    if start_idx == -1:
        return ""
    substring = s[start_idx:]
    for delimiter in delimiters:
        end_idx = substring.find(delimiter)
        if end_idx != -1:
            return substring[:end_idx].replace(keyword, '').strip()
    return substring.replace(keyword, '').strip()

def extract_bandcamp_album_metadata(url):
    # get the base URL for the album, which might be https://{GROUP_NAME}.bandcamp.com
    base_url = url.split('/album/')[0]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Album data
    album_title = soup.select_one('#name-section .trackTitle').text.strip()
    album_desc = soup.select_one('.tralbumData.tralbum-about').text.strip()
    album_artists = extract_substring(album_desc, "art by", [',', 'and', '.', '\n']).split()
    if not album_artists:
        album_artists = extract_substring(album_desc, "cover by", [',', 'and', '.', '\n']).split()
    
    track_elements = soup.select('.title')
    print(f"Found {len(track_elements)} track elements")
    tracks_urls = [base_url + link.a['href'] for link in track_elements if link.a and '/track/' in link.a['href']]

    album_data = {
        'Album': album_title,
        'Date Added': str(date.today()),
        'URLs': [url, '-'],
        'Cover Artists': album_artists,
        'Color': '#ffffff',
        'Groups': ['-'],
    }

    tracks_data = []

    for track_url in tracks_urls:
        print(f"Fetching data from {track_url}")
        track_data = extract_bandcamp_track_metadata(track_url)
        if track_data:
            tracks_data.append(track_data)

    return album_data, tracks_data

def extract_bandcamp_track_metadata(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    track_title = soup.select_one('.trackTitle').text.strip()
    
    if ' - ' in track_title:
        artist, track_name = track_title.split(' - ', 1)
    else:
        track_name = track_title
        artist_desc = soup.select_one('.tralbumData.tralbum-credits').text.strip()
        artist = extract_substring(artist_desc, "music by")

    track_data = {
        'Track': track_name,
        'Artists': [artist],
        'URLs': [url, '-'],
    }

    # Duration and referenced tracks
    duration_element = soup.select_one('.time.secondaryText')
    if duration_element:
        track_data['Duration'] = duration_element.text.strip()

    return track_data

def main():
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <Bandcamp_album_URL>")
        sys.exit(1)

    url = sys.argv[1]
    album_data, tracks_data = extract_bandcamp_album_metadata(url)

    with open('metadata.yaml', 'w', encoding='utf-8') as outfile:
        yaml.dump(album_data, outfile, default_flow_style=False, allow_unicode=True)
        outfile.write("---\n")
        for track_data in tracks_data:
            yaml.dump(track_data, outfile, default_flow_style=False, allow_unicode=True)
            outfile.write("---\n")

if __name__ == "__main__":
    main()