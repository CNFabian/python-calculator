#!/usr/bin/env python3
"""
Search for character select screen text in the existing extracted_strings.csv
The character select interface text should already be in the code.bin extraction
"""

import csv
import re
from pathlib import Path

def search_character_select_text():
    """Search for character select related text in extracted strings"""
    
    print("🎮 SEARCHING CHARACTER SELECT TEXT IN EXTRACTED STRINGS")
    print("=" * 60)
    
    # File path
    extracted_file = Path("files/extracted_strings.csv")
    
    if not extracted_file.exists():
        print(f"❌ File not found: {extracted_file}")
        print("   Make sure you have run the string extraction from code.bin")
        return
    
    print(f"📄 Analyzing: {extracted_file}")
    
    # Character select related terms to search for
    search_terms = {
        'character_jp': [
            'キャラクター', 'キャラ', 'ファイター', 'プレイヤー', '選手',
            'アイチ', 'カムイ', 'ミサキ', 'カイ', '先導', 'せんどう',
            'レン', 'アサカ', 'ナオキ', 'テツ', 'シンゴ'
        ],
        'ui_jp': [
            '選択', 'せんたく', '決定', 'けってい', '確認', 'かくにん',
            'キャンセル', 'きゃんせる', '戻る', 'もどる', '進む', 'すすむ',
            'メニュー', 'めにゅー', '画面', 'がめん'
        ],
        'deck_jp': [
            'デッキ', 'でっき', 'クラン', '構築', 'こうちく',
            'カード', 'かーど', '編集', 'へんしゅう'
        ],
        'english': [
            'character', 'select', 'fighter', 'player', 'menu', 'deck',
            'clan', 'confirm', 'cancel', 'back', 'next', 'aichi', 'kamui'
        ]
    }
    
    # Read the CSV file
    matches = []
    total_strings = 0
    
    try:
        with open(extracted_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row in reader:
                total_strings += 1
                extract_text = row.get('extract', '')
                
                # Clean the text for searching
                clean_text = extract_text.replace('†', '\n').replace('<|', '').replace('|>', '')
                clean_lower = clean_text.lower()
                
                # Check for matches
                found_terms = []
                category_matches = {}
                
                for category, terms in search_terms.items():
                    category_matches[category] = []
                    for term in terms:
                        if term.lower() in clean_lower:
                            found_terms.append(term)
                            category_matches[category].append(term)
                
                if found_terms:
                    matches.append({
                        'pointer_offsets': row.get('pointer_offsets', ''),
                        'pointer_value': row.get('pointer_value', ''),
                        'original_text': extract_text,
                        'clean_text': clean_text,
                        'found_terms': found_terms,
                        'categories': category_matches
                    })
        
        print(f"📊 Total strings analyzed: {total_strings:,}")
        print(f"🎯 Found {len(matches)} strings with character select related terms")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    if matches:
        print(f"\n📝 CHARACTER SELECT RELATED STRINGS")
        print("=" * 50)
        
        # Sort by relevance (number of matching terms)
        matches.sort(key=lambda x: len(x['found_terms']), reverse=True)
        
        # Categorize matches
        character_matches = []
        ui_matches = []
        deck_matches = []
        english_matches = []
        
        for match in matches:
            if match['categories']['character_jp']:
                character_matches.append(match)
            elif match['categories']['ui_jp']:
                ui_matches.append(match)
            elif match['categories']['deck_jp']:
                deck_matches.append(match)
            elif match['categories']['english']:
                english_matches.append(match)
        
        # Display character-related matches first (highest priority)
        if character_matches:
            print(f"\n🎯 CHARACTER NAMES & FIGHTER TEXT ({len(character_matches)} strings):")
            for i, match in enumerate(character_matches[:10], 1):  # Show top 10
                print(f"[{i}] {match['pointer_value']}")
                print(f"    Terms: {', '.join(match['found_terms'])}")
                print(f"    Text: '{match['clean_text'][:100]}{'...' if len(match['clean_text']) > 100 else ''}'")
                print()
        
        # Display UI-related matches
        if ui_matches:
            print(f"\n🎮 UI & MENU TEXT ({len(ui_matches)} strings):")
            for i, match in enumerate(ui_matches[:10], 1):  # Show top 10
                print(f"[{i}] {match['pointer_value']}")
                print(f"    Terms: {', '.join(match['found_terms'])}")
                print(f"    Text: '{match['clean_text'][:100]}{'...' if len(match['clean_text']) > 100 else ''}'")
                print()
        
        # Display deck-related matches
        if deck_matches:
            print(f"\n🎴 DECK & CARD TEXT ({len(deck_matches)} strings):")
            for i, match in enumerate(deck_matches[:5], 1):  # Show top 5
                print(f"[{i}] {match['pointer_value']}")
                print(f"    Terms: {', '.join(match['found_terms'])}")
                print(f"    Text: '{match['clean_text'][:100]}{'...' if len(match['clean_text']) > 100 else ''}'")
                print()
        
        # Display English matches
        if english_matches:
            print(f"\n🔤 ENGLISH TEXT ({len(english_matches)} strings):")
            for i, match in enumerate(english_matches[:5], 1):  # Show top 5
                print(f"[{i}] {match['pointer_value']}")
                print(f"    Terms: {', '.join(match['found_terms'])}")
                print(f"    Text: '{match['clean_text'][:100]}{'...' if len(match['clean_text']) > 100 else ''}'")
                print()
        
        print(f"\n💡 ANALYSIS RESULTS:")
        print(f"   ✅ Found character select related text in existing extraction!")
        print(f"   🎯 {len(character_matches)} character/fighter strings")
        print(f"   🎮 {len(ui_matches)} UI/menu strings")
        print(f"   🎴 {len(deck_matches)} deck/card strings")
        print(f"   🔤 {len(english_matches)} English strings")
        
        print(f"\n🔧 NEXT STEPS:")
        print(f"   1. These strings are already extracted and ready for translation")
        print(f"   2. Check files/extracted_strings_translated.csv for English versions")
        print(f"   3. Use the existing injection pipeline to update character select text")
        print(f"   4. Test in Citra emulator to see English character select screen")
        
        # Save results for reference
        output_file = Path("files/character_select_strings.csv")
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['pointer_offsets', 'pointer_value', 'category', 'found_terms', 'original_text', 'clean_text'])
            
            for match in matches:
                categories = []
                for cat, terms in match['categories'].items():
                    if terms:
                        categories.append(f"{cat}:{','.join(terms)}")
                
                writer.writerow([
                    match['pointer_offsets'],
                    match['pointer_value'],
                    '|'.join(categories),
                    ','.join(match['found_terms']),
                    match['original_text'],
                    match['clean_text']
                ])
        
        print(f"\n💾 Saved results to: {output_file}")
        
    else:
        print(f"\n⚠️  No character select related text found")
        print(f"   This might mean:")
        print(f"   - Character names are stored in RTZ files")
        print(f"   - Different terminology is used")
        print(f"   - Text is in image/graphics files")

def main():
    search_character_select_text()

if __name__ == "__main__":
    main()