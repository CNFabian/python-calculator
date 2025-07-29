#!/usr/bin/env python3
"""
Fix path issues and test with known good Japanese data
"""
import pandas as pd
from pathlib import Path
import os

def fix_paths_and_create_test_data():
    """Create a small test dataset with known good Japanese text"""
    
    # Change to project root if we're in a subdirectory
    current_dir = Path.cwd()
    if current_dir.name == 'translation':
        os.chdir('../..')
        print(f"📁 Changed directory to: {Path.cwd()}")
    
    # Create test data with GOOD Japanese segments (from your paste.txt)
    good_japanese_segments = [
        {
            'file': 'tuto_001.bin',
            'segment_id': 25,
            'japanese_text': 'いくぜ……！！'
        },
        {
            'file': 'tuto_001.bin', 
            'segment_id': 26,
            'japanese_text': 'どっちもが'
        },
        {
            'file': 'tuto_001.bin',
            'segment_id': 27,
            'japanese_text': 'ついにやってきました……決勝戦！！\nどちらがこの大会を制するのかー！？'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 60,
            'japanese_text': 'ダメージゾーンのカードが、\n６枚になると<|負|ま'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 61,
            'japanese_text': 'プレイマットについて、詳しく説明するね。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 63,
            'japanese_text': 'ドロップゾーンは、\nフィールドから退却したカードや'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 65,
            'japanese_text': 'フィールドとカードについての\n説明をするね。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 66,
            'japanese_text': 'ヴァンガードがダメージを受けると、\nここにカードが置かれるわ。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 67,
            'japanese_text': 'この数字は、『グレード』を表しているの。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 68,
            'japanese_text': 'ここはダメージゾーン。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 70,
            'japanese_text': 'パワーは攻撃する時も、防御する時も\n高いほうが有利よ。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 72,
            'japanese_text': 'ファイトは、このプレイマットの上で\n行われるの。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 74,
            'japanese_text': 'このカード達（デッキ）はあなたと一緒に\n戦う仲間よ。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 75,
            'japanese_text': 'あなたが呼び出した\n味方のカードを置く場所ね。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 81,
            'japanese_text': 'あなたの分身になるカード、『ヴァンガード』を\n置く場所よ。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 83,
            'japanese_text': 'ジェネレーションゾーンは、\nあなたのＧユニットを置く場所よ。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 90,
            'japanese_text': 'デッキのカード枚数は５０枚ちょうど\nじゃないといけないから、注意してね。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 95,
            'japanese_text': 'グレードは『０』～『４』まであるから、\n覚えておいてね。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 98,
            'japanese_text': 'さっき教えた山札にあるカードの束。\nこれをデッキっていうの。'
        },
        {
            'file': 'tuto_008.bin',
            'segment_id': 99,
            'japanese_text': 'Ｇデッキには、Ｇユニットっていう\n特別なカードを、最大８枚まで入れられるわ。'
        }
    ]
    
    # Create directory structure
    output_dir = Path("files/rtz_extracted/tutorials")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create clean test dataset
    df = pd.DataFrame(good_japanese_segments)
    test_file = output_dir / "tutorial_test_small.csv"
    df.to_csv(test_file, index=False, encoding='utf-8')
    
    print(f"✅ Created clean test dataset: {test_file}")
    print(f"   Contains {len(df)} segments with GOOD Japanese text")
    
    # Show preview
    print(f"\n📝 Clean test data preview:")
    for i in range(min(5, len(df))):
        row = df.iloc[i]
        preview = row['japanese_text'][:50] + "..." if len(row['japanese_text']) > 50 else row['japanese_text']
        print(f"  {row['file']}:{row['segment_id']} - {preview}")
    
    return test_file

def main():
    print("🔧 CF Vanguard Path Fix and Clean Test Data")
    print("=" * 50)
    
    # Fix paths and create clean test data
    test_file = fix_paths_and_create_test_data()
    
    print(f"\n🎯 Now you can run from project root:")
    print(f"  python3 scripts/translation/translate_tutorials.py --test")
    print(f"  python3 scripts/translation/assess_tutorial_quality.py --test")
    
    print(f"\n📊 This test dataset uses CLEAN Japanese extracted from your paste.txt")
    print(f"    It contains real Vanguard tutorial dialogue that should translate well")

if __name__ == "__main__":
    main()