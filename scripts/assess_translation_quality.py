import csv
import re
from pathlib import Path

def analyze_translation_quality(csv_file):
    stats = {
        'total': 0,
        'translated': 0,
        'still_japanese': 0,
        'empty': 0,
        'very_short': 0,
        'potential_issues': []
    }
    
    print(f"📊 Analyzing translation quality in {csv_file}")
    print("=" * 60)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for i, row in enumerate(reader):
            stats['total'] += 1
            text = row.get('extract', '').replace('†', '\n')
            
            if not text.strip():
                stats['empty'] += 1
                continue
                
            # Check if still contains Japanese characters
            if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text):
                stats['still_japanese'] += 1
            else:
                stats['translated'] += 1
            
            # Length analysis
            if len(text.strip()) < 3:
                stats['very_short'] += 1
            
            # Flag potential issues
            if 'error' in text.lower() or 'fail' in text.lower():
                stats['potential_issues'].append(f"Line {i+1}: {text[:50]}...")
    
    # Print results
    print(f"📈 TRANSLATION STATISTICS:")
    print(f"   Total entries: {stats['total']}")
    print(f"   ✅ Translated to English: {stats['translated']} ({stats['translated']/stats['total']*100:.1f}%)")
    print(f"   🔄 Still Japanese: {stats['still_japanese']} ({stats['still_japanese']/stats['total']*100:.1f}%)")
    print(f"   ❌ Empty: {stats['empty']}")
    print(f"   📏 Very short (<3 chars): {stats['very_short']}")
    
    return stats

def show_samples(csv_file, count=10):
    print(f"\n🔍 SAMPLE TRANSLATIONS:")
    print("=" * 60)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for i, row in enumerate(reader):
            if i >= count:
                break
                
            text = row.get('extract', '').replace('†', '\\n')
            print(f"\n[{i+1}] \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
            
            # Quality indicator
            if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text):
                print(f"    🔄 Status: STILL JAPANESE")
            elif len(text.strip()) < 3:
                print(f"    📏 Status: VERY SHORT")
            else:
                print(f"    ✅ Status: TRANSLATED")

if __name__ == "__main__":
    analyze_translation_quality('files/extracted_strings_translated.csv')
    show_samples('files/extracted_strings_translated.csv', 15)