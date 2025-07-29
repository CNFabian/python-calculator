#!/usr/bin/env python3
"""
Minimal test of CF Vanguard translation pipeline
Tests on just 3-5 segments to validate the process quickly
"""
import requests
import json
import re
from pathlib import Path

# Test data - hand-picked good segments from your extraction
TEST_SEGMENTS = [
    {
        'file': 'tuto_001.bin',
        'segment_id': 1,
        'japanese': 'はじめまして！私はカムイです。',
        'expected_terms': []
    },
    {
        'file': 'tuto_001.bin', 
        'segment_id': 2,
        'japanese': 'ヴァンガードの基本的なルールを説明しますね。',
        'expected_terms': ['ヴァンガード']
    },
    {
        'file': 'tuto_002.bin',
        'segment_id': 5,
        'japanese': 'アタックしてダメージを与えよう！',
        'expected_terms': ['アタック', 'ダメージ']
    },
    {
        'file': 'tuto_002.bin',
        'segment_id': 8,
        'japanese': 'ドライブチェックを行います。',
        'expected_terms': ['ドライブチェック']
    },
    {
        'file': 'fe0001.bin',
        'segment_id': 3,
        'japanese': 'ガードするカードを選択してください。',
        'expected_terms': ['ガード', 'カード']
    }
]

# Vanguard terms (subset for testing)
VANGUARD_TERMS = {
    "ヴァンガード": "Vanguard",
    "アタック": "Attack", 
    "ダメージ": "Damage",
    "ガード": "Guard",
    "ドライブチェック": "Drive Check",
    "カード": "Card",
    "デッキ": "Deck",
    "ユニット": "Unit"
}

class MiniTranslator:
    def __init__(self, api_url="http://localhost:5001"):
        self.api_url = api_url
        self.terms_dict = VANGUARD_TERMS
        
    def clean_text(self, text: str) -> str:
        """Basic cleaning"""
        # Remove <|kanji|kana|> -> kanji
        text = re.sub(r'<\|([^|]+)\|[^|]*\|>', r'\1', text)
        # Remove color tags
        text = re.sub(r'\{\$[0-9A-Fa-f]*\}', '', text)
        return text.strip()
    
    def translate(self, japanese_text: str) -> str:
        """Translate with LibreTranslate + Vanguard terms"""
        try:
            response = requests.post(
                f"{self.api_url}/translate",
                headers={"Content-Type": "application/json"},
                json={
                    "q": japanese_text,
                    "source": "ja",
                    "target": "en",
                    "format": "text"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                translated = response.json().get("translatedText", "")
                # Apply Vanguard terminology
                for jp_term, en_term in self.terms_dict.items():
                    translated = translated.replace(jp_term, en_term)
                return translated
            else:
                return f"[API Error: {response.status_code}]"
                
        except Exception as e:
            return f"[Translation Error: {e}]"

def test_libretranslate_connection():
    """Test if LibreTranslate API is working"""
    print("🔗 Testing LibreTranslate connection...")
    try:
        response = requests.post(
            "http://localhost:5001/translate",
            headers={"Content-Type": "application/json"},
            json={"q": "こんにちは", "source": "ja", "target": "en"},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json().get("translatedText", "")
            print(f"   ✅ API working! Test: こんにちは → {result}")
            return True
        else:
            print(f"   ❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def main():
    print("🧪 CF Vanguard Translation Mini-Test")
    print("=" * 40)
    
    # Test API connection first
    if not test_libretranslate_connection():
        print("\n❌ LibreTranslate API not available!")
        print("   Start it with: docker-compose up libretranslate")
        return
    
    # Initialize translator
    translator = MiniTranslator()
    
    print(f"\n🔄 Testing translation on {len(TEST_SEGMENTS)} segments...")
    print("-" * 50)
    
    results = []
    success_count = 0
    
    for i, segment in enumerate(TEST_SEGMENTS, 1):
        print(f"\n[{i}/{len(TEST_SEGMENTS)}] {segment['file']}:{segment['segment_id']}")
        
        # Clean input
        japanese = segment['japanese']
        cleaned = translator.clean_text(japanese)
        
        print(f"   JP: {japanese}")
        if cleaned != japanese:
            print(f"   Cleaned: {cleaned}")
        
        # Translate
        translated = translator.translate(cleaned)
        print(f"   EN: {translated}")
        
        # Check for expected Vanguard terms
        found_terms = []
        for jp_term in segment['expected_terms']:
            if jp_term in japanese:
                en_term = VANGUARD_TERMS.get(jp_term, jp_term)
                if en_term in translated:
                    found_terms.append(f"{jp_term}→{en_term} ✅")
                else:
                    found_terms.append(f"{jp_term}→{en_term} ❌")
        
        if found_terms:
            print(f"   Terms: {', '.join(found_terms)}")
        
        # Assess success
        is_success = (
            not translated.startswith("[") and  # Not an error message
            len(translated) > 0 and
            translated != japanese  # Actually translated
        )
        
        if is_success:
            success_count += 1
            print(f"   ✅ SUCCESS")
        else:
            print(f"   ❌ FAILED")
        
        results.append({
            'file': segment['file'],
            'segment_id': segment['segment_id'],
            'japanese': japanese,
            'english': translated,
            'success': is_success
        })
    
    # Summary
    print(f"\n📊 MINI-TEST RESULTS")
    print("=" * 20)
    print(f"Successful translations: {success_count}/{len(TEST_SEGMENTS)}")
    print(f"Success rate: {success_count/len(TEST_SEGMENTS)*100:.1f}%")
    
    if success_count >= len(TEST_SEGMENTS) * 0.8:  # 80% success rate
        print(f"\n✅ PIPELINE WORKING!")
        print(f"   Ready to test with larger dataset")
        print(f"   Next: python prepare_tutorial_csv.py")
        print(f"   Then: python translate_tutorials.py --test")
    else:
        print(f"\n⚠️  PIPELINE NEEDS ATTENTION")
        print(f"   Check LibreTranslate setup")
        print(f"   Verify API responses")
    
    # Save mini results
    output_dir = Path("files/rtz_extracted/tutorials")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import pandas as pd
    df = pd.DataFrame(results)
    output_file = output_dir / "mini_test_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Mini-test results saved to: {output_file}")
    
    # Show file structure reminder
    print(f"\n📁 Current project structure detected:")
    print(f"   scripts/translation/ - Translation pipeline scripts")
    print(f"   scripts/extraction/ - RTZ extraction scripts") 
    print(f"   scripts/injection/ - ROM injection scripts")
    print(f"   scripts/rom_tools/ - ROM building tools")

if __name__ == "__main__":
    main()