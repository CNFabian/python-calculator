#!/usr/bin/env python3
"""
CF Vanguard Tutorial Translation Pipeline
Translates extracted tutorial dialogue using LibreTranslate + Vanguard terminology
"""
import pandas as pd
import requests
import json
import re
import time
from pathlib import Path
from typing import Dict, List

# Vanguard-specific term mappings (expand from your card_list_jap_enriched.json)
VANGUARD_TERMS = {
    # Core game terms
    "ヴァンガード": "Vanguard",
    "リアガード": "Rear-guard", 
    "ダメージ": "Damage",
    "アタック": "Attack",
    "ガード": "Guard",
    "ドライブチェック": "Drive Check",
    "トリガー": "Trigger",
    "ファイト": "Fight",
    "デッキ": "Deck",
    "ソウル": "Soul",
    "ドロップゾーン": "Drop Zone",
    "ダメージゾーン": "Damage Zone",
    "ガーディアン": "Guardian",
    "インターセプト": "Intercept",
    "ブースト": "Boost",
    "ライド": "Ride",
    "コール": "Call",
    "スタンド": "Stand",
    "レスト": "Rest",
    "パワー": "Power",
    "クリティカル": "Critical",
    "シールド": "Shield",
    "グレード": "Grade",
    "ユニット": "Unit",
    "クラン": "Clan",
    "カード": "Card",
    "フィールド": "Field",
    "サークル": "Circle",
    "ターン": "Turn",
    "フェイズ": "Phase",
    "メインフェイズ": "Main Phase",
    "ライドフェイズ": "Ride Phase",
    "双闘": "Legion",
    "超越": "Stride",
    "Ｇユニット": "G Unit",
    "Ｇゾーン": "G Zone",
    "ストライドステップ": "Stride Step",
    "呪縛": "Lock",
    "解呪": "Unlock",
    "デリート": "Delete",
    
    # Tutorial specific
    "チュートリアル": "Tutorial",
    "説明": "Explanation",
    "練習": "Practice",
    "確認": "Confirm",
    "選択": "Select",
    "決定": "Decide",
    "終了": "End",
    "開始": "Start",
    "次": "Next",
    "前": "Previous",
    "戻る": "Return",
    "進む": "Proceed",
    
    # UI terms
    "ボタン": "Button",
    "画面": "Screen",
    "メニュー": "Menu",
    "設定": "Settings",
    "オプション": "Options",
    "ヘルプ": "Help",
    "情報": "Information"
}

class VanguardTranslator:
    def __init__(self, api_url="http://localhost:5001"):
        self.api_url = api_url
        self.session = requests.Session()
        self.terms_dict = VANGUARD_TERMS
        
    def clean_japanese_text(self, text: str) -> str:
        """Clean Japanese text for translation"""
        if not text or not isinstance(text, str):
            return ""
            
        # Remove control characters but preserve newlines
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        # Clean Vanguard-specific formatting
        # <|kanji|kana|> -> kanji only  
        text = re.sub(r'<\|([^|]+)\|[^|]*\|>', r'\1', text)
        
        # Remove color tags {$123456} and {$}
        text = re.sub(r'\{\$[0-9A-Fa-f]*\}', '', text)
        
        # Replace special punctuation
        text = text.replace('､', '、').replace('｡', '。')
        text = text.replace('†', '\n')  # Special newline character
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def apply_vanguard_terminology(self, text: str) -> str:
        """Apply Vanguard-specific term replacements"""
        for jp_term, en_term in self.terms_dict.items():
            text = text.replace(jp_term, en_term)
        return text
    
    def translate_text(self, japanese_text: str) -> str:
        """Translate Japanese text to English"""
        if not japanese_text or len(japanese_text.strip()) < 2:
            return ""
            
        try:
            # Preserve newlines
            lines = japanese_text.split('\n')
            translated_lines = []
            
            for line in lines:
                if not line.strip():
                    translated_lines.append("")
                    continue
                    
                # Translate via LibreTranslate
                response = self.session.post(
                    f"{self.api_url}/translate",
                    headers={"Content-Type": "application/json"},
                    json={
                        "q": line.strip(),
                        "source": "ja", 
                        "target": "en",
                        "format": "text"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    translated = response.json().get("translatedText", "")
                    # Apply Vanguard terminology
                    translated = self.apply_vanguard_terminology(translated)
                    translated_lines.append(translated)
                else:
                    print(f"Translation failed: {response.status_code}")
                    translated_lines.append(line)  # Keep original on failure
                    
                # Rate limiting
                time.sleep(0.1)
                
            return '\n'.join(translated_lines)
            
        except Exception as e:
            print(f"Translation error: {e}")
            return japanese_text  # Return original on error
    
    def assess_quality(self, text: str) -> float:
        """Assess text quality (0.0 = garbage, 1.0 = perfect)"""
        if not text:
            return 0.0
            
        # Count Japanese characters vs total
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return 0.0
            
        japanese_ratio = japanese_chars / total_chars
        
        # Penalize control characters and corrupted content
        control_chars = len(re.findall(r'[\x00-\x1F\x7F-\x9F]', text))
        corruption_penalty = min(control_chars / total_chars, 0.5)
        
        # Boost score for Vanguard terms
        vanguard_bonus = 0.0
        for term in self.terms_dict.keys():
            if term in text:
                vanguard_bonus += 0.1
        vanguard_bonus = min(vanguard_bonus, 0.3)
        
        quality = japanese_ratio - corruption_penalty + vanguard_bonus
        return max(0.0, min(1.0, quality))

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Translate CF Vanguard tutorial dialogue')
    parser.add_argument('--test', action='store_true', help='Use small test dataset instead of full dataset')
    args = parser.parse_args()
    
    print("🎮 CF Vanguard Tutorial Translation Pipeline")
    if args.test:
        print("🧪 TESTING MODE - Using small dataset")
    print("=" * 50)
    
    # Paths
    base_dir = Path("files/rtz_extracted/tutorials")
    if args.test:
        input_file = base_dir / "tutorial_test_small.csv"
        output_file = base_dir / "tutorial_test_translated.csv"
        print(f"🧪 Using TEST dataset: {input_file}")
    else:
        input_file = base_dir / "tutorial_for_translation.csv"
        output_file = base_dir / "tutorial_translated.csv"
        print(f"📂 Using FULL dataset: {input_file}")
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    # Load data
    print(f"📂 Loading tutorial data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Initialize translator
    translator = VanguardTranslator()
    print(f"🔗 Using LibreTranslate API: {translator.api_url}")
    
    # Process translations
    print("\n🔄 Processing translations...")
    
    results = []
    high_quality_count = 0
    medium_quality_count = 0
    low_quality_count = 0
    
    total_segments = len(df)
    for idx, row in df.iterrows():
        file_name = row['file']
        segment_id = row['segment_id']
        japanese = str(row['japanese_text'])
        
        # Clean and assess quality
        cleaned = translator.clean_japanese_text(japanese)
        quality = translator.assess_quality(cleaned)
        
        # Categorize quality
        if quality >= 0.7:
            quality_tier = "HIGH"
            high_quality_count += 1
        elif quality >= 0.4:
            quality_tier = "MEDIUM" 
            medium_quality_count += 1
        else:
            quality_tier = "LOW"
            low_quality_count += 1
        
        # Translate if reasonable quality
        if quality >= 0.3:
            translated = translator.translate_text(cleaned)
            status = "TRANSLATED"
        else:
            translated = "[CORRUPTED - SKIP]"
            status = "SKIPPED"
        
        results.append({
            'file': file_name,
            'segment_id': segment_id,
            'japanese_original': japanese,
            'japanese_cleaned': cleaned,
            'english_translation': translated,
            'quality_score': round(quality, 3),
            'quality_tier': quality_tier,
            'status': status
        })
        
        print(f"[{idx+1:3d}/{total_segments}] {file_name}:{segment_id} - Quality: {quality:.3f} ({quality_tier}) - {status}")
        
        # Save progress every 10 translations for test mode, 50 for full mode
        save_interval = 10 if args.test else 50
        if (idx + 1) % save_interval == 0:
            temp_df = pd.DataFrame(results)
            temp_df.to_csv(output_file.with_suffix('.tmp.csv'), index=False)
            print(f"💾 Progress saved ({idx+1}/{total_segments})")
    
    # Save final results
    final_df = pd.DataFrame(results)
    final_df.to_csv(output_file, index=False)
    
    # Generate summary
    print("\n📊 TRANSLATION SUMMARY")
    print("=" * 30)
    print(f"Total segments: {total_segments}")
    print(f"High quality (≥0.7): {high_quality_count}")
    print(f"Medium quality (0.4-0.7): {medium_quality_count}")
    print(f"Low quality (<0.4): {low_quality_count}")
    print(f"Successfully translated: {len([r for r in results if r['status'] == 'TRANSLATED'])}")
    print(f"Skipped (corrupted): {len([r for r in results if r['status'] == 'SKIPPED'])}")
    print(f"\n✅ Results saved to: {output_file}")
    
    if args.test:
        print(f"\n🧪 TEST MODE COMPLETE")
        print(f"   If results look good, run without --test flag for full dataset")
    else:
        print(f"\n🎯 FULL TRANSLATION COMPLETE")
        print(f"   Ready for injection phase")
    
    # Show top quality examples
    print("\n🏆 TOP QUALITY TRANSLATIONS (Sample):")
    print("-" * 40)
    high_quality = [r for r in results if r['quality_tier'] == 'HIGH'][:5]
    for item in high_quality:
        print(f"JP: {item['japanese_cleaned'][:50]}...")
        print(f"EN: {item['english_translation'][:50]}...")
        print(f"Quality: {item['quality_score']}\n")

if __name__ == "__main__":
    main()