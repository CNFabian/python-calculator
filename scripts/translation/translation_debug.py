#!/usr/bin/env python3
"""
Translation Process Debugger
Checks what happened during your translation injection process
"""

import sys
from pathlib import Path
import csv

def check_translation_files():
    """Check the status of translation files and process"""
    print("🔍 Translation Process Debugger")
    print("=" * 50)
    
    # Check key files exist
    key_files = {
        "originalGame.3ds": "Original ROM",
        "files/extracted_strings_translated.csv": "Main game translations",
        "files/rtz_extracted/tutorials/tutorial_test_translated.csv": "Tutorial translations",
        "romfs/fe/tuto_001.bin": "Tutorial 1 binary",
        "romfs/fe/tuto_008.bin": "Tutorial 8 binary"
    }
    
    print("📁 File Status Check:")
    files_exist = {}
    for file_path, description in key_files.items():
        path_obj = Path(file_path)
        exists = path_obj.exists()
        files_exist[file_path] = exists
        
        if exists:
            size = path_obj.stat().st_size
            print(f"   ✅ {description}: {size:,} bytes")
        else:
            print(f"   ❌ {description}: NOT FOUND")
    
    print()
    
    # Check translation CSV content if it exists
    tutorial_csv = Path("files/rtz_extracted/tutorials/tutorial_test_translated.csv")
    if tutorial_csv.exists():
        print("📊 Tutorial Translation Analysis:")
        try:
            with open(tutorial_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            print(f"   📝 {len(rows)} translation entries found")
            
            # Check for English content
            english_count = 0
            sample_translations = []
            
            for i, row in enumerate(rows[:10]):  # Check first 10
                if 'translated_text' in row and row['translated_text']:
                    translated = row['translated_text']
                    if any(c.isascii() and c.isalpha() for c in translated):
                        english_count += 1
                        if len(sample_translations) < 3:
                            original = row.get('original_text', 'N/A')[:30]
                            translated_short = translated[:30]
                            sample_translations.append(f"'{original}' → '{translated_short}'")
            
            print(f"   🎯 {english_count} entries contain English text")
            
            if sample_translations:
                print("   📖 Sample translations:")
                for sample in sample_translations:
                    print(f"      {sample}")
            else:
                print("   ⚠️  No clear English translations found in samples")
                
        except Exception as e:
            print(f"   ❌ Error reading CSV: {e}")
    
    print()
    
    # Check if injection scripts ran
    injection_indicators = [
        "scripts/translation/inject_rtz_translations.py",
        "scripts/translation/translate_tutorials.py"
    ]
    
    print("🔧 Translation Script Status:")
    for script_path in injection_indicators:
        path_obj = Path(script_path)
        if path_obj.exists():
            print(f"   ✅ {script_path}")
        else:
            print(f"   ❌ {script_path} - Script missing")
    
    print()
    
    # Analyze binary files
    print("📂 Binary File Analysis:")
    bin_files = [
        Path("romfs/fe/tuto_001.bin"),
        Path("romfs/fe/tuto_008.bin")
    ]
    
    for bin_file in bin_files:
        if bin_file.exists():
            size = bin_file.stat().st_size
            print(f"   📁 {bin_file.name}: {size:,} bytes")
            
            # Quick check for any text content
            try:
                data = bin_file.read_bytes()
                
                # Count potential text characters
                ascii_count = sum(1 for b in data if 32 <= b <= 126)
                ascii_percentage = (ascii_count / len(data)) * 100
                
                # Look for UTF-16LE patterns
                utf16_count = 0
                for i in range(0, len(data) - 1, 2):
                    if data[i + 1] == 0x00 and 32 <= data[i] <= 126:
                        utf16_count += 1
                
                print(f"      ASCII chars: {ascii_count} ({ascii_percentage:.1f}%)")
                print(f"      UTF-16LE patterns: {utf16_count}")
                
                # Try to find any English words
                test_bytes = [
                    b'card',
                    b'play',
                    b'zone',
                    b'damage',
                    b'the\x00',  # UTF-16LE "the"
                    b'a\x00n\x00d\x00',  # UTF-16LE "and"
                ]
                
                found_patterns = []
                for pattern in test_bytes:
                    if pattern in data:
                        found_patterns.append(pattern)
                
                if found_patterns:
                    print(f"      🎯 Found patterns: {len(found_patterns)} potential English words")
                else:
                    print(f"      ⚠️  No obvious English patterns found")
                    
            except Exception as e:
                print(f"      ❌ Error analyzing: {e}")
        else:
            print(f"   ❌ {bin_file.name}: NOT FOUND")
    
    print()
    
    # Provide diagnosis
    print("🎯 DIAGNOSIS & RECOMMENDATIONS")
    print("=" * 40)
    
    if not files_exist.get("files/rtz_extracted/tutorials/tutorial_test_translated.csv"):
        print("❌ ISSUE: Translation CSV not found")
        print("   🔧 Run translation script first:")
        print("   python scripts/translation/translate_tutorials.py")
        
    elif not (files_exist.get("romfs/fe/tuto_001.bin") and files_exist.get("romfs/fe/tuto_008.bin")):
        print("❌ ISSUE: Binary files not found") 
        print("   🔧 Check RTZ extraction and injection:")
        print("   python scripts/translation/inject_rtz_translations.py")
        
    else:
        print("📊 All key files present - checking content quality...")
        print()
        print("🎮 RECOMMENDED TESTING APPROACH:")
        print("   1. Verify translation content with diagnostic script")
        print("   2. Check if translations are in expected format") 
        print("   3. Test in Citra emulator directly")
        print("   4. Look for visual changes in tutorial text")
        
        print()
        print("⚡ QUICK TEST:")
        print("   # Load ROM in Citra and check Tutorial menu")
        print("   # Even if hex search fails, visual test may show English")

def main():
    check_translation_files()

if __name__ == "__main__":
    main()