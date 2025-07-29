import csv
import re
import json
from pathlib import Path

def load_vanguard_terminology():
    game_terms = {
        # Core Vanguard terms
        'ヴァンガード': 'Vanguard',
        'ファイト': 'Fight', 
        'デッキ': 'Deck',
        'カード': 'Card',
        'グレード': 'Grade',
        'パワー': 'Power',
        'クリティカル': 'Critical',
        'シールド': 'Shield',
        'クラン': 'Clan',
        'ネイション': 'Nation',
        'トリガー': 'Trigger',
        
        # UI terms
        'メニュー': 'Menu',
        'セーブ': 'Save',
        'ロード': 'Load',
        'オプション': 'Options',
        'ヘルプ': 'Help',
        'タイトル': 'Title',
        'ゲーム': 'Game',
        'バトル': 'Battle',
        'ストーリー': 'Story',
        'チュートリアル': 'Tutorial',
        
        # Skills (from your card data)
        '【永】': '[CONT]',
        '【自】': '[AUTO]',
        '【起】': '[ACT]',
        '【スタンド】': '[Stand]',
        '【レスト】': '[Rest]',
    }
    
    # Try to load card terminology
    try:
        with open('files/card_list_jap_enriched.json', 'r', encoding='utf-8') as f:
            cards = json.load(f)
        
        print(f"📚 Loading card terminology from {len(cards)} cards...")
        
        for card in cards[:500]:  # Process first 500 cards
            if card.get('kanji_name') and card.get('en_kanji_name'):
                game_terms[card['kanji_name']] = card['en_kanji_name']
                
            if card.get('clan') and card.get('en_clan'):
                game_terms[card['clan']] = card['en_clan']
                
    except Exception as e:
        print(f"⚠️ Could not load card data: {e}")
    
    return game_terms

def improve_translation(text, terminology):
    improved = text
    
    for jp_term, en_term in terminology.items():
        improved = improved.replace(jp_term, en_term)
    
    # Clean up spacing
    improved = re.sub(r'\s+', ' ', improved).strip()
    
    # Maintain original length with padding
    if len(improved) < len(text):
        improved += ' ' * (len(text) - len(improved))
    elif len(improved) > len(text):
        improved = improved[:len(text)]
    
    return improved

def process_translations():
    terminology = load_vanguard_terminology()
    print(f"🎮 Loaded {len(terminology)} terminology mappings")
    
    input_file = Path('files/extracted_strings_translated.csv')
    output_file = Path('files/extracted_strings_improved.csv')
    
    improvements = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile, delimiter=';')
        fieldnames = list(reader.fieldnames)
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
        
        writer.writeheader()
        
        for i, row in enumerate(reader):
            original = row['extract']
            improved = improve_translation(original, terminology)
            
            if improved != original:
                improvements += 1
                if improvements <= 5:
                    print(f"IMPROVED [{i+1}]: {original[:40]}...")
                    print(f"      ->: {improved[:40]}...\n")
            
            row['extract'] = improved
            writer.writerow(row)
    
    print(f"✅ Processed {i+1} translations")
    print(f"🔧 Made {improvements} improvements")
    print(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    process_translations()