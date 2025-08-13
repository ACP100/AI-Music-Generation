#LakhMIDI ma bhayeko midi haru ko lyrics haru
#ajai sabai ko nikalisakeko chaina, dher baki cha 
import os
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup
import re

# Configuration
MIDI_ROOT = "AI-MUSIC-GENERATION/MIDIS"  # Root folder containing artist folders
LYRIC_SOURCES = ["genius", "lyricsfreak"]  # Sources to try in order
REQUEST_DELAY = 2  # Seconds between requests
DEBUG = True  # Set to False to reduce output

# Headers to mimic browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def debug_print(message):
    if DEBUG:
        print(message)

def clean_for_search(name):
    """Convert underscores to spaces and clean for URL/search"""
    # Replace underscores with spaces for searching
    name = name.replace('_', ' ')
    # Remove content in brackets/parentheses
    name = re.sub(r'\(.*?\)|\[.*?\]|\{.*?\}', '', name)
    # Remove special characters
    name = re.sub(r'[^\w\s-]', '', name).strip()
    # Replace spaces with hyphens for URLs
    name = re.sub(r'\s+', '-', name)
    return name.lower()

def get_genius_lyrics(artist, song):
    """Fetch lyrics from Genius.com"""
    try:
        debug_print(f"  Trying Genius: {artist} - {song}")
        artist_clean = clean_for_search(artist)
        song_clean = clean_for_search(song)
        url = f"https://genius.com/{artist_clean}-{song_clean}-lyrics"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        lyrics_div = soup.find("div", {"data-lyrics-container": "true"})
        
        if lyrics_div:
            lyrics = lyrics_div.get_text("\n")
            return lyrics.strip()
    except Exception as e:
        debug_print(f"  Genius error: {str(e)}")
    return None

def get_lyricsfreak_lyrics(artist, song):
    """Fetch lyrics from LyricsFreak.com"""
    try:
        debug_print(f"  Trying LyricsFreak: {artist} - {song}")
        artist_clean = artist.replace('_', ' ')
        song_clean = song.replace('_', ' ')
        search_url = f"https://www.lyricsfreak.com/search.php?q={artist_clean}+{song_clean}"
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        result_link = soup.find("a", href=re.compile(r"/lyrics/.*\.html"))
        
        if result_link:
            lyrics_url = "https://www.lyricsfreak.com" + result_link['href']
            lyrics_response = requests.get(lyrics_url, headers=HEADERS, timeout=10)
            lyrics_response.raise_for_status()
            
            lyrics_soup = BeautifulSoup(lyrics_response.text, 'html.parser')
            lyrics_div = lyrics_soup.find("div", {"id": "content"})
            
            if lyrics_div:
                lyrics = lyrics_div.get_text("\n")
                return lyrics.strip()
    except Exception as e:
        debug_print(f"  LyricsFreak error: {str(e)}")
    return None

def process_artist_folder(artist_path):
    """Process all MIDI files in an artist folder"""
    artist_name = artist_path.name
    debug_print(f"\nProcessing artist: {artist_name}")
    
    midi_files = list(artist_path.glob("*.mid")) + list(artist_path.glob("*.MID"))
    if not midi_files:
        debug_print(f"No MIDI files found in {artist_name}")
        return 0
    
    processed_count = 0
    for midi_file in midi_files:
        song_name = midi_file.stem
        lyrics_file = midi_file.with_suffix(".txt")
        
        if lyrics_file.exists():
            debug_print(f"Lyrics already exist for {song_name}")
            continue
        
        debug_print(f"\nProcessing: {song_name}")
        
        # Try each source until we get lyrics
        lyrics = None
        for source in LYRIC_SOURCES:
            if source == "genius":
                lyrics = get_genius_lyrics(artist_name, song_name)
            elif source == "lyricsfreak":
                lyrics = get_lyricsfreak_lyrics(artist_name, song_name)
            
            if lyrics:
                with open(lyrics_file, "w", encoding="utf-8") as f:
                    f.write(lyrics)
                debug_print(f"✅ Saved lyrics for {song_name}")
                processed_count += 1
                break
            
            time.sleep(REQUEST_DELAY)
        
        if not lyrics:
            debug_print(f"❌ Could not find lyrics for {song_name}")
        
        time.sleep(REQUEST_DELAY)
    
    return processed_count

def main():
    print("=== MIDI Lyrics Downloader ===")
    print(f"Scanning directory: {MIDI_ROOT}")
    
    # Verify root directory exists
    if not os.path.exists(MIDI_ROOT):
        print(f"Error: Directory not found - {MIDI_ROOT}")
        print("Please check the MIDI_ROOT path in the script")
        return
    
    total_artists = 0
    total_processed = 0
    start_time = time.time()
    
    # Process each artist folder
    for artist_dir in Path(MIDI_ROOT).iterdir():
        if artist_dir.is_dir():
            total_artists += 1
            processed = process_artist_folder(artist_dir)
            total_processed += processed
    
    duration = time.time() - start_time
    print("\n=== Summary ===")
    print(f"Artists processed: {total_artists}")
    print(f"Songs with lyrics downloaded: {total_processed}")
    print(f"Time taken: {duration:.1f} seconds")

if __name__ == "__main__":
    main()