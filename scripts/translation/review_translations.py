#!/usr/bin/env python3
"""
Review the translation test results and apply improved Vanguard term corrections
"""
import pandas as pd
from pathlib import Path
import re

# Improved Vanguard term corrections
VANGUARD_CORRECTIONS = {
    # Capitalization fixes
    "vanguard": "Vanguard",
    "rear-guard": "Rear-guard", 
    "rear guard": "Rear-guard",
    "damage zone": "Damage Zone",
    "drop zone": "Drop Zone", 
    "drop zones": "Drop Zone",
    "drive check": "Drive Check",
    "g unit": "G Unit",
    "g units": "G Units", 
    "generation zone": "Generation Zone",
    "play mat": "Play Mat",
    "deck": "Deck",
    "card": "Card",
    "cards": "Cards",
    "field": "Field",
    "attack": "Attack",
    "guard": "Guard",
    "damage": "Damage",
    "power": "Power",
    "grade": "Grade",
    "unit": "Unit",
    "units": "Units",
    "fight": "Fight",
    
    # Common translation improvements
    "finals": "Finals",
    "tournament": "Tournament",
    "battle": "Battle",
    "turn": "Turn",
    "phase": "Phase"
}

def apply_vanguard_corrections(text: str) -> str:
    """Apply Vanguard-specific corrections to translated text"""
    if not text:
        return text
    
    # Apply corrections with word boundaries
    for wrong, correct in VANGUARD_CORRECTIONS.items():
        pattern = r'\b' + re.escape(wrong) + r'\b'
        text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
    
    # Fix common formatting issues
    text = text.replace('。', '.')  # Japanese period
    text = text.replace(' 、', ',')  # Japanese comma spacing
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces
    text = text.strip()
    
    # Clean up incomplete Vanguard syntax
    text = re.sub(r'<\s*\|\s*[^|]*\s*\|\s*[^>]*>', '', text)  # Remove incomplete <|x|y|> tags
    
    return text

def review_test_translations():
    """Review and improve the test translation results"""
    
    print("📊 CF Vanguard Translation Test Results Review")
    print("=" * 50)
    
    # Load test results
    test_file = Path("files/rtz_extracted/tutorials/tutorial_test_translated.csv")
    
    if not test_file.exists():
        print(f"❌ Test results not found: {test_file}")
        return
    
    df = pd.read_csv(test_file)
    print(f"📂 Loaded {len(df)} translation results")
    
    # Apply improved corrections
    print(f"\n🔧 Applying Vanguard term corrections...")
    df['english_improved'] = df['english_translation'].apply(apply_vanguard_corrections)
    
    # Show before/after examples
    print(f"\n📝 BEFORE/AFTER CORRECTIONS:")
    print("-" * 60)
    
    improvements_found = 0
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        original = row['english_translation']
        improved = row['english_improved']
        
        if original != improved:
            improvements_found += 1
            print(f"\n[{row['file']}:{row['segment_id']}]")
            print(f"JP: {row['japanese_cleaned'][:60]}...")
            print(f"Before: {original}")
            print(f"After:  {improved}")
        else:
            # Show good translations too
            print(f"\n[{row['file']}:{row['segment_id']}] ✅")
            print(f"JP: {row['japanese_cleaned'][:60]}...")
            print(f"EN: {improved}")
    
    print(f"\n📊 IMPROVEMENT SUMMARY:")
    print(f"   Translations improved: {improvements_found}")
    print(f"   Already good: {len(df) - improvements_found}")
    
    # Save improved results
    output_file = Path("files/rtz_extracted/tutorials/tutorial_test_improved.csv")
    df.to_csv(output_file, index=False)
    print(f"\n💾 Improved translations saved to: {output_file}")
    
    # Quality assessment
    high_quality = len(df[df['quality_tier'] == 'HIGH'])
    medium_quality = len(df[df['quality_tier'] == 'MEDIUM'])
    
    print(f"\n🎯 QUALITY ASSESSMENT:")
    print(f"   HIGH quality: {high_quality}/{len(df)} ({high_quality/len(df)*100:.1f}%)")
    print(f"   MEDIUM quality: {medium_quality}/{len(df)} ({medium_quality/len(df)*100:.1f}%)")
    
    if high_quality >= len(df) * 0.8:  # 80% high quality
        print(f"\n✅ EXCELLENT RESULTS!")
        print(f"   Ready for RTZ injection testing")
        print(f"   Next: python3 scripts/translation/inject_rtz_translations.py --test")
    else:
        print(f"\n⚠️  Results need review")
    
    return df

def show_vanguard_terms_found(df):
    """Show which Vanguard terms were successfully translated"""
    
    print(f"\n🎮 VANGUARD TERMS SUCCESSFULLY TRANSLATED:")
    print("-" * 40)
    
    vanguard_terms_found = {
        'Damage Zone': 0,
        'Drop Zone': 0, 
        'Vanguard': 0,
        'Field': 0,
        'Card': 0,
        'Deck': 0,
        'Grade': 0,
        'G Unit': 0,
        'Play Mat': 0,
        'Fight': 0
    }
    
    for _, row in df.iterrows():
        text = row.get('english_improved', row['english_translation']).upper()
        for term in vanguard_terms_found.keys():
            if term.upper() in text:
                vanguard_terms_found[term] += 1
    
    for term, count in vanguard_terms_found.items():
        if count > 0:
            print(f"   ✅ {term}: {count} times")
        
def main():
    df = review_test_translations()
    if df is not None:
        show_vanguard_terms_found(df)

if __name__ == "__main__":
    main()