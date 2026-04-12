#!/usr/bin/env python3
"""
Vocabulary data updater - fetches from Google Sheets and saves to JSON
Run this script to update vocabulary data from Google Sheets

Usage: python3 scripts/update_vocab.py

Requires: ~/.hermes/google_token.json with valid OAuth token
          (token['token'] key, not token['access_token'])
"""

import urllib.request
import json

# Google Sheet IDs for vocabulary (V Basic/L1/L2/L3/L4 2025 Fall in OpnClwTutoring Drive folder)
# Note: These are Google Sheets shortcuts - targetId resolved via shortcutDetails
LEVELS = {
    'basic': '10xtBPuQAGxYT_rA9VHqJlrep1CKTxa5foqkAF-bFWlc',
    'level1': '1ihwmHHA7mzDWv-CCtS_-UI8cJ3Wt1a23gtR0oua1KOE',
    'level2': '1ZQS3Si7V9-3iRp6XdZduAIt75z3cO1TD6aOJhhMlF2A',  # Fixed: was swapped with level3
    'level3': '15V4BJ2df6FQzQYoFpvop0JifWKalVTVDAtSh1JEvrHM',
    'level4': '1sspHipHnyGNjpdnrAukkBoD1mmgVQ--AZoEamIScF3o'
}

def get_access_token():
    """Refresh Google OAuth token from ~/.hermes/google_token.json"""
    import urllib.parse
    with open('/home/coder/.hermes/google_token.json') as f:
        token = json.load(f)
    params = urllib.parse.urlencode({
        "client_id": token['client_id'],
        "client_secret": token['client_secret'],
        "refresh_token": token['refresh_token'],
        "grant_type": "refresh_token"
    })
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=params.encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        new_token = json.loads(resp.read())
    token['token'] = new_token['access_token']
    with open('/home/coder/.hermes/google_token.json', 'w') as f:
        json.dump(token, f)
    return new_token['access_token']

def fetch_vocabulary():
    """Fetch vocabulary data from all Google Sheets"""
    access_token = get_access_token()
    
    all_data = {}
    
    for level_name, sheet_id in LEVELS.items():
        try:
            # Read from A1:Z500 with FORMATTED_VALUE (range "A:ZZ" fails)
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A1:Z500?valueRenderOption=FORMATTED_VALUE"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
            values = result.get('values', [])
            
            words = []
            for row in values[1:]:  # Skip header row
                if len(row) >= 4 and row[0] and row[1]:
                    # Combine both example sentences
                    example = row[3] if len(row) > 3 else ''
                    if len(row) > 4 and row[4]:
                        example = f"{row[3]} {row[4]}"
                    words.append({
                        'date': row[0],
                        'word': row[1],
                        'chinese': row[2] if len(row) > 2 else '',
                        'example': example
                    })
            
            all_data[level_name] = words
            print(f"✓ {level_name}: {len(words)} words")
                
        except Exception as e:
            print(f"✗ {level_name}: {e}")
            all_data[level_name] = []
    
    return all_data

def save_vocabulary(data):
    """Save vocabulary data to JSON file"""
    output_file = 'data/vocabulary.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved to {output_file}")
    
    # Print summary
    print("\nSummary:")
    for level, words in data.items():
        print(f"  {level}: {len(words)} words")

if __name__ == '__main__':
    print("Fetching vocabulary data from Google Sheets...")
    print("=" * 50)
    
    data = fetch_vocabulary()
    save_vocabulary(data)
    
    print("\nDone! Run this script again to update data.")
