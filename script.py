import json
import subprocess
from uuid import uuid4
import sys
import datetime

def parse_yt_links(file_path):
    entries = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) < 3:
                i += 1
                continue
            name = parts[0]
            category = parts[1]
            favicon = parts[2]
            extra_id = parts[3] if len(parts) > 3 else None
            
            # Look for the next line which should be the URL
            i += 1
            if i >= len(lines):
                break
            url_line = lines[i].strip()
            if url_line.startswith('https://www.youtube.com/'):
                entries.append({
                    'name': name,
                    'category': category,
                    'favicon': favicon,
                    'extra_id': extra_id,
                    'yt_url': url_line
                })
            else:
                # If no URL, skip or handle error
                print(f"Warning: No valid YouTube URL found for {name}", file=sys.stderr)
        i += 1
    
    return entries

def get_m3u8_url(yt_url):
    try:
        # Try to get the direct HLS manifest URL
        cmd = ['yt-dlp', '--no-warnings', '-g', '--no-playlist', '--format', 'best[protocol^=hls]']
        cmd.append(yt_url)
        output = subprocess.check_output(cmd).decode().strip()
        if not output:
            # Fallback to any best format URL
            cmd = ['yt-dlp', '--no-warnings', '-g', '--no-playlist', yt_url]
            output = subprocess.check_output(cmd).decode().strip()
        urls = output.split('\n')
        # Prefer the first URL that looks like m3u8
        for url in urls:
            if url.endswith('.m3u8'):
                return url
        # If none, return the first one
        if urls:
            return urls[0]
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error fetching m3u8 for {yt_url}: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: yt-dlp not found. Please install yt-dlp.", file=sys.stderr)
        sys.exit(1)

def main(yt_links_file, json_file, output_json_file):
    # Parse yt_links.txt
    entries = parse_yt_links(yt_links_file)
    
    # Get m3u8 for each
    for entry in entries:
        m3u8 = get_m3u8_url(entry['yt_url'])
        if m3u8:
            entry['m3u8'] = m3u8
        else:
            print(f"Skipping {entry['name']} due to failure in fetching m3u8.", file=sys.stderr)
    
    # Load existing JSON
    with open(json_file, 'r') as f:
        stations = json.load(f)
    
    # Generate current timestamp
    now = datetime.datetime.utcnow()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_iso = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Add new entries
    added_count = 0
    for entry in [e for e in entries if e.get('m3u8')]:
        new_station = {
            "changeuuid": str(uuid4()),
            "stationuuid": str(uuid4()),
            "serveruuid": str(uuid4()),
            "name": entry['name'],
            "url": entry['yt_url'],
            "url_resolved": entry['m3u8'],
            "homepage": "",
            "favicon": entry['favicon'],
            "tags": entry['category'],
            "country": "India",
            "countrycode": "ACTOR",
            "iso_3166_2": "",
            "state": "Tamil Nadu",
            "language": "tamil",
            "languagecodes": "ta",
            "votes": 0,
            "lastchangetime": timestamp,
            "lastchangetime_iso8601": timestamp_iso,
            "codec": "AAC",  # Typical for YouTube streams
            "bitrate": 128,   # Assumed average
            "hls": 1 if entry['m3u8'].endswith('.m3u8') else 0,
            "lastcheckok": 1,
            "lastchecktime": timestamp,
            "lastchecktime_iso8601": timestamp_iso,
            "lastcheckoktime": timestamp,
            "lastcheckoktime_iso8601": timestamp_iso,
            "lastlocalchecktime": timestamp,
            "lastlocalchecktime_iso8601": timestamp_iso,
            "clicktimestamp": timestamp,
            "clicktimestamp_iso8601": timestamp_iso,
            "clickcount": 0,
            "clicktrend": 0,
            "ssl_error": 0,
            "geo_lat": None,
            "geo_long": None,
            "geo_distance": None,
            "has_extended_info": False
        }
        stations.append(new_station)
        added_count += 1
    
    # Save updated JSON
    with open(output_json_file, 'w') as f:
        json.dump(stations, f, indent=2)
    
    print(f"Updated JSON saved to {output_json_file}. Added {added_count} new stations.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <yt_links.txt> <actor.json> <output.json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])