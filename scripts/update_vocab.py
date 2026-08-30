#!/usr/bin/env python3
"""
Vocabulary data updater - fetches from Google Sheets App_data tabs and saves to JSON
Run this script to update vocabulary data from Google Sheets

Usage: python3 scripts/update_vocab.py

Requires: ~/.hermes/google_token.json with valid OAuth token
          (token['token'] key, not token['access_token'])

Output (data/vocabulary.json):
  {
    "basic": [...], "level1": [...], "level2": [...], "level3": [...], "level4": [...],
    "current_label":  "2026 Fall",
    "archived_label": "2025 Fall",
    "archived": { "basic": [...], "level1": [...], "level2": [...], "level3": [...], "level4": [...] }
  }

The 'archived' bucket lets the live site expose a "📦 View 2025 Fall archive" toggle
without any history loss. When a new semester starts, just swap CURRENT_IDS — the
old sheets become the archive automatically (re-point ARCHIVE_IDS at them, or leave
ARCHIVE_IDS pointing at 2025 Fall indefinitely).
"""

import urllib.request
import urllib.parse
import json

# CURRENT semester — update these when a new semester starts.
CURRENT_LABEL = "2026 Fall"
CURRENT_IDS = {
    'basic':  '11jiY2_Bwe4Mfj8p2fcmFvE5leCrX1wOBrSbvnviJkQQ',  # V Level Basic Y2026
    'level1': '1chi308pH5GFMeC1Gmc7Vy3uue4vvIbccn-Ud7OUDEU0',  # V Level 1 Y2026
    'level2': '1ywYeFv6npjW0fNL-LaQBbdGdWB59n37JuZWhRRFieMI',  # V Level 2 Y2026
    'level3': '1E6GzSSIgpnxsot2yo5F9m5Tn82_BZrZP7LwSicY33dI',  # V Level 3 Y2026
    'level4': '1JudYt46nHWyXmKOv-6nDtNq4lWo8jCuxhqsGNgR8kRw',  # V Level 4 Y2026
}

# ARCHIVED semester — frozen history. When CURRENT rolls forward, move the old
# CURRENT_IDS into ARCHIVE_IDS so old vocab stays browsable on the site.
ARCHIVE_LABEL = "2025 Fall"
ARCHIVE_IDS = {
    'basic':  '10xtBPuQAGxYT_rA9VHqJlrep1CKTxa5foqkAF-bFWlc',
    'level1': '1ihwmHHA7mzDWv-CCtS_-UI8cJ3Wt1a23gtR0oua1KOE',
    'level2': '1ZQS3Si7V9-3iRp6XdZduAIt75z3cO1TD6aOJhhMlF2A',
    'level3': '15V4BJ2df6FQzQYoFpvop0JifWKalVTVDAtSh1JEvrHM',
    'level4': '1sspHipHnyGNjpdnrAukkBoD1mmgVQ--AZoEamIScF3o',
}

LEVEL_KEYS = ['basic', 'level1', 'level2', 'level3', 'level4']

def get_access_token():
    """Refresh Google OAuth token from ~/.hermes/google_token.json"""
    with open('/home/coder/.hermes/google_token.json') as f:
        token = json.load(f)
    params = urllib.parse.urlencode({
        "client_id": token['client_id'],
        "client_secret": token['client_secret'],
        "refresh_token": token['refresh_token'],
        "grant_type": "refresh_token"
    })
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=params.encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        new_token = json.loads(resp.read())
    token['token'] = new_token['access_token']
    with open('/home/coder/.hermes/google_token.json', 'w') as f:
        json.dump(token, f)
    return new_token['access_token']


def fetch_sheet(access_token, sheet_id):
    """Fetch a single sheet's App_data tab (cols A:G, rows 1..500)."""
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
           f"/values/App_data!A1:G500?valueRenderOption=FORMATTED_VALUE")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    values = result.get('values', [])

    words = []
    for row in values[1:]:  # skip header
        # Each row's first column is the date (YYMMDD like '260831'). Filter out blanks.
        if len(row) >= 3 and row[0] and row[1]:
            words.append({
                'date':      row[0],
                'word':      row[1],
                'chinese':   row[2] if len(row) > 2 else '',
                'example_1': row[3] if len(row) > 3 else '',
                'example_2': row[4] if len(row) > 4 else '',
                'trans_1':   row[5] if len(row) > 5 else '',
                'trans_2':   row[6] if len(row) > 6 else '',
            })
    return words


def fetch_all_from(access_token, id_map, label):
    """Fetch every level in id_map, return {level: [words]}."""
    out = {}
    for level in LEVEL_KEYS:
        try:
            out[level] = fetch_sheet(access_token, id_map[level])
            print(f"  ✓ {label} {level}: {len(out[level])} words")
        except Exception as e:
            print(f"  ✗ {label} {level}: {e}")
            out[level] = []
    return out


def main():
    print(f"Fetching vocabulary — CURRENT='{CURRENT_LABEL}', ARCHIVED='{ARCHIVE_LABEL}'")
    print("=" * 60)

    access_token = get_access_token()

    print(f"\n[{CURRENT_LABEL}] (CURRENT)")
    current = fetch_all_from(access_token, CURRENT_IDS, CURRENT_LABEL)

    print(f"\n[{ARCHIVE_LABEL}] (ARCHIVED)")
    archived = fetch_all_from(access_token, ARCHIVE_IDS, ARCHIVE_LABEL)

    payload = dict(current)  # basic, level1..level4 are the current bucket
    payload['current_label']  = CURRENT_LABEL
    payload['archived_label'] = ARCHIVE_LABEL
    payload['archived']       = archived

    output_file = 'data/vocabulary.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to {output_file}")
    print("\nSummary (current):")
    for level in LEVEL_KEYS:
        print(f"  {level:8s}: {len(payload[level])} words")
    print("Summary (archived):")
    for level in LEVEL_KEYS:
        print(f"  {level:8s}: {len(payload['archived'][level])} words")


if __name__ == '__main__':
    main()
