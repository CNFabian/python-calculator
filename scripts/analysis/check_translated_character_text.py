#!/usr/bin/env python3
"""
Check if character select text is already translated in extracted_strings_translated.csv
"""

import csv
from pathlib import Path

def check_translated_character_text():
    """Check translated versions of character select text"""
    
    print("🔍 CHECKING TRANSLATED CHARACTER SELECT TEXT")
    print("=" * 50)
    
    # File paths
    character_file = Path("files/character_select_strings.csv")
    translated_file = Path("files/extracted_strings_translated.csv")
    
    if not character_file.exists():
        print(f"❌ Character strings file not found: {character_file}")
        print("   Run the search script first")
        return
    
    if not translated_file.exists():
        print(f"❌ Translated strings file not found: {translated_file}")
        print("   You may need to run the translation pipeline first")
        return
    
    print(f"📄 Reading character select strings from: {character_file}")
    print(f"📄 Reading translations from: {translated_file}")
    
    # Load character select strings
    character_pointers = set()
    with open(character_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            character_pointers.add(row['pointer_value'])
    
    print(f"📊 Found {len(character_pointers)} character select related pointers")
    
    # Load translated strings and find matches
    translated_matches = []
    total_translated = 0
    
    with open(translated_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            total_translated += 1
            pointer_value = row.get('pointer_value', '')
            
            if pointer_value in character_pointers:
                translated_matches.append({
                    'pointer_value': pointer_value,
                    'japanese': row.get('extract', ''),
                    'english': row.get('translation', ''),
                    'pointer_offsets': row.get('pointer_offsets', '')
                })
    
    print(f"📊 Total translated strings: {total_translated:,}")
    print(f"🎯 Character select strings with translations: {len(translated_matches)}")
    
    if translated_matches:
        print(f"\n📝 TRANSLATED CHARACTER SELECT TEXT")
        print("=" * 40)
        
        # Show examples of translated character select text
        for i, match in enumerate(translated_matches[:15], 1):  # Show first 15
            japanese = match['japanese'].replace('†', '\n')
            english = match['english'].replace('†', '\n')
            
            print(f"[{i}] {match['pointer_value']}")
            print(f"    🇯🇵 Japanese: '{japanese[:80]}{'...' if len(japanese) > 80 else ''}'")
            print(f"    🇺🇸 English:  '{english[:80]}{'...' if len(english) > 80 else ''}'")
            print()
        
        if len(translated_matches) > 15:
            print(f"    ... and {len(translated_matches) - 15} more translated strings")
        
        print(f"\n✅ SUCCESS: Character select text is already translated!")
        print(f"📝 Found {len(translated_matches)} translated strings")
        
        # Check translation quality
        good_translations = 0
        for match in translated_matches:
            english = match['english'].lower()
            if any(word in english for word in ['character', 'select', 'deck', 'clan', 'fighter', 'confirm', 'menu']):
                good_translations += 1
        
        print(f"🎯 {good_translations} strings contain English interface terms")
        
        print(f"\n🔧 NEXT STEPS:")
        print(f"   1. Character select text is already translated to English!")
        print(f"   2. Use your existing injection pipeline to apply translations")
        print(f"   3. Run: python3 scripts/injection/inject_from_file.py")
        print(f"   4. Rebuild ROM and test in Citra emulator")
        print(f"   5. You should see English character select screen!")
        
        # Save a subset for injection testing
        test_file = Path("files/character_select_test.csv")
        with open(test_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['pointer_offsets', 'pointer_value', 'separators', 'extract', 'translation'])
            
            for match in translated_matches[:20]:  # Save first 20 for testing
                writer.writerow([
                    match['pointer_offsets'],
                    match['pointer_value'],
                    '00 00',  # Default separator
                    match['japanese'],
                    match['english']
                ])
        
        print(f"💾 Saved test subset to: {test_file}")
        print(f"   Use this file to test character select translation injection")
        
    else:
        print(f"\n⚠️  No translated versions found for character select strings")
        print(f"   This might mean:")
        print(f"   - Translations haven't been generated yet")
        print(f"   - Different pointer values in files")
        print(f"   - Translation process needs to be run")
        
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print(f"   1. Run the translation pipeline on character select strings")
        print(f"   2. Use LibreTranslate to translate the Japanese text")
        print(f"   3. Update the extracted_strings_translated.csv file")

def main():
    check_translated_character_text()

if __name__ == "__main__":
    main()