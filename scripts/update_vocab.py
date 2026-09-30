#!/usr/bin/env python3
"""
Vocabulary data updater - fetches from Google Sheets App_data tabs and saves to JSON
Run this script to update vocabulary data from Google Sheets

Usage: python3 scripts/update_vocab.py

Requires: ~/.hermes/google_token.json with valid OAuth token
          (token['token'] key, not token['access_token'])

Output (split files — site only fetches what it needs):
  data/vocab_current.json   — { basic, level1..level4, current_label }            (always loaded)
  data/vocab_archived.json  — { basic, level1..level4, archived_label }           (lazy-loaded only when
                                                                            someone clicks "📦 Archived")

Why split (2026-09-27 perf fix): the combined file was 625 KB raw / 149 KB gzipped
because the archived bucket (1,529 words from 2025 Fall) accounted for 84% of the
bytes but is rarely accessed. GH Pages edge cache made the combined fetch variable
1.6s-15.4s on the live apex domain. Splitting drops the always-loaded payload by ~6x.

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
    'basic':  '1Y8mu5i64CX_jW9a_XId0f5EHUMAdjH2yMe-cirkLb7I',  # V Level Basic Y2026 (new folder)
    'level1': '1hVBUoG3G_kAqOd93ZflxeuBXj4UH-pq_XnA7igq21rA',  # V Level 1 Y2026 (new folder)
    'level2': '1gI-oEZllGeVFmbcI3kH_vxHBygcb9A-mYmtCp0TRttE',  # V Level 2 Y2026 (new folder)
    'level3': '1psNG94DfBjWGsctpalEA93K573SuJdyP01OSSq59jbk',  # V Level 3 Y2026 (new folder)
    'level4': '1j6AyvZk0103_R7QDLv9MtjTxjk14IZKPvPmLbRMIpog',  # V Level 4 Y2026 (new folder)
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

    # Write two separate files. The site only fetches vocab_current.json on first
    # paint; vocab_archived.json is lazy-loaded when the user clicks "📦 Archived".
    # Old combined data/vocabulary.json is no longer written.
    current_payload = dict(current)
    current_payload['current_label'] = CURRENT_LABEL

    archived_payload = dict(archived)
    archived_payload['archived_label'] = ARCHIVE_LABEL

    current_path = 'data/vocab_current.json'
    archived_path = 'data/vocab_archived.json'
    with open(current_path, 'w', encoding='utf-8') as f:
        json.dump(current_payload, f, indent=2, ensure_ascii=False)
    with open(archived_path, 'w', encoding='utf-8') as f:
        json.dump(archived_payload, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to {current_path} + {archived_path}")
    print("\nSummary (current):")
    for level in LEVEL_KEYS:
        print(f"  {level:8s}: {len(current_payload[level])} words")
    print("Summary (archived):")
    for level in LEVEL_KEYS:
        print(f"  {level:8s}: {len(archived_payload[level])} words")


if __name__ == '__main__':
    main()
