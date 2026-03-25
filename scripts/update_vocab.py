#!/usr/bin/env python3
"""
Vocabulary data updater - fetches from Google Sheets and saves to JSON
Run this script to update vocabulary data from Google Sheets
"""

import sys
sys.path.insert(0, '/home/openclaw-j/.openclaw/workspace/google-drive/scripts')
from gdrive_auth import get_drive_service
from googleapiclient.discovery import build
import json
import os

# Google Sheet IDs for vocabulary (App_Data tab)
LEVELS = {
    'basic': '10xtBPuQAGxYT_rA9VHqJlrep1CKTxa5foqkAF-bFWlc',
    'level1': '1ihwmHHA7mzDWv-CCtS_-UI8cJ3Wt1a23gtR0oua1KOE',
    'level2': '15V4BJ2df6FQzQYoFpvop0JifWKalVTVDAtSh1JEvrHM',
    'level3': '15V4BJ2df6FQzQYoFpvop0JifWKalVTVDAtSh1JEvrHM',
    'level4': '1sspHipHnyGNjpdnrAukkBoD1mmgVQ--AZoEamIScF3o'
}

def fetch_vocabulary():
    """Fetch vocabulary data from all Google Sheets"""
    service = get_drive_service()
    sheets_service = build('sheets', 'v4', credentials=service._http.credentials)
    
    all_data = {}
    
    for level_name, sheet_id in LEVELS.items():
        try:
            # Try App_Data first (for Basic, L1, L2)
            try:
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range='App_Data!A1:D1000'
                ).execute()
                values = result.get('values', [])
                
                words = []
                for row in values[1:]:  # Skip header
                    if len(row) >= 3 and row[0] and row[1]:
                        words.append({
                            'date': row[0],
                            'word': row[1],
                            'chinese': row[2] if len(row) > 2 else '',
                            'example': row[3] if len(row) > 3 else ''
                        })
                
                all_data[level_name] = words
                print(f"✓ {level_name}: {len(words)} words from App_Data")
                
            except:
                # Fallback to direct sheet read (for L3, L4 if different structure)
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range='A1:D1000'
                ).execute()
                values = result.get('values', [])
                
                words = []
                for row in values[1:]:
                    if len(row) >= 3 and row[0] and row[1]:
                        words.append({
                            'date': row[0],
                            'word': row[1],
                            'chinese': row[2] if len(row) > 2 else '',
                            'example': row[3] if len(row) > 3 else ''
                        })
                
                all_data[level_name] = words
                print(f"✓ {level_name}: {len(words)} words (fallback)")
                
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
