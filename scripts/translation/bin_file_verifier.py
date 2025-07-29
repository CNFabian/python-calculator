#!/usr/bin/env python3
"""
Binary File Translation Verifier
Checks if English translations are properly embedded in .bin tutorial files
Ignores RTZ compression status - focuses on direct .bin file modification
"""

import sys
from pathlib import Path
import re

def search_utf16_patterns(file_path):
    """Search for UTF-16LE English patterns in binary file"""
    try:
        data = file_path.read_bytes()
        results = {
            'file_size': len(data),
            'english_terms_found': [],
            'english_char_count': 0,
            'common_words_found': [],
            'sample_text': []
        }
        
        # English terms we expect from your translations
        english_terms = [
            "Home", "Damage", "Zone", "Card", "Field", "Vanguard", 
            "Grade", "Play", "Mat", "Fight", "explain", "detail", 
            "place", "number", "will", "can", "this", "when"
        ]
        
        # Search for each term in UTF-16LE
        for term in english_terms:
            utf16_bytes = term.encode('utf-16le')
            if utf16_bytes in data:
                pos = data.find(utf16_bytes)
                results['english_terms_found'].append({
                    'term': term,
                    'position': f'0x{pos:X}',
                    'utf16_hex': utf16_bytes.hex()
                })
        
        # Count English letters (UTF-16LE format: letter followed by 0x00)
        english_count = 0
        for i in range(0, len(data) - 1, 2):
            byte1, byte2 = data[i], data[i + 1]
            if byte2 == 0x00 and (65 <= byte1 <= 90 or 97 <= byte1 <= 122):
                english_count += 1
        
        results['english_char_count'] = english_count
        
        # Extract sample readable text (UTF-16LE)
        try:
            # Look for UTF-16LE text patterns
            sample_texts = []
            i = 0
            while i < len(data) - 20 and len(sample_texts) < 5:
                # Look for potential UTF-16LE text start
                if (data[i + 1] == 0x00 and 
                    32 <= data[i] <= 126):  # Printable ASCII
                    
                    # Try to decode a chunk
                    chunk_end = min(i + 40, len(data))
                    try:
                        text = data[i:chunk_end].decode('utf-16le', errors='ignore')
                        # Filter for meaningful text (contains letters)
                        if any(c.isalpha() for c in text) and len(text.strip()) > 3:
                            clean_text = ''.join(c for c in text if c.isprintable())
                            if clean_text and len(clean_text) > 3:
                                sample_texts.append({
                                    'position': f'0x{i:X}',
                                    'text': clean_text[:30] + ('...' if len(clean_text) > 30 else '')
                                })
                    except:
                        pass
                i += 2  # Move by 2 bytes for UTF-16LE
            
            results['sample_text'] = sample_texts
        except Exception as e:
            results['sample_text_error'] = str(e)
        
        return results
        
    except Exception as e:
        return {'error': str(e)}

def analyze_translation_injection(file_path):
    """Analyze if translation injection was successful"""
    print(f"🔍 Analyzing: {file_path.name}")
    print("=" * 50)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    results = search_utf16_patterns(file_path)
    
    if 'error' in results:
        print(f"❌ Error analyzing file: {results['error']}")
        return False
    
    # File size
    size_mb = results['file_size'] / (1024 * 1024)
    print(f"📊 File size: {results['file_size']:,} bytes ({size_mb:.2f} MB)")
    
    # English terms found
    english_terms = results['english_terms_found']
    if english_terms:
        print(f"✅ Found {len(english_terms)} English terms:")
        for term_info in english_terms[:5]:  # Show first 5
            term = term_info['term']
            pos = term_info['position']
            print(f"   📝 '{term}' at {pos}")
        
        if len(english_terms) > 5:
            print(f"   📝 ... and {len(english_terms) - 5} more terms")
    else:
        print("⚠️  No exact English terms found")
    
    # English character count
    eng_chars = results['english_char_count']
    if eng_chars > 100:
        percentage = (eng_chars * 2) / results['file_size'] * 100  # *2 for UTF-16LE
        print(f"📝 Contains {eng_chars} English characters ({percentage:.1f}% of file)")
    elif eng_chars > 10:
        print(f"📝 Contains {eng_chars} English characters (limited)")
    else:
        print("⚠️  Very few English characters detected")
    
    # Sample text
    samples = results.get('sample_text', [])
    if samples:
        print(f"📖 Sample text found ({len(samples)} segments):")
        for sample in samples[:3]:  # Show first 3
            pos = sample['position']
            text = sample['text']
            print(f"   {pos}: '{text}'")
    else:
        print("⚠️  No readable text samples extracted")
    
    # Overall assessment
    success_indicators = 0
    if english_terms:
        success_indicators += 2
    if eng_chars > 100:
        success_indicators += 1
    if samples:
        success_indicators += 1
    
    print(f"\n🎯 Translation Success Assessment:")
    if success_indicators >= 3:
        print("   ✅ HIGH - Translation injection likely successful")
        return True
    elif success_indicators >= 2:
        print("   🟡 MEDIUM - Some translation detected")
        return True
    elif success_indicators >= 1:
        print("   🟠 LOW - Minimal translation detected")
        return False
    else:
        print("   ❌ NONE - No clear translation detected")
        return False

def main():
    print("🔍 Binary File Translation Verifier")
    print("📁 Checking .bin files for successful translation injection")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("originalGame.3ds").exists():
        print("❌ originalGame.3ds not found")
        print("   Run this script from the vanguard-translation directory")
        return 1
    
    # Files to check
    tutorial_files = [
        "romfs/fe/tuto_001.bin",
        "romfs/fe/tuto_008.bin",
        "romfs/fe/tuto_002.bin",
        "romfs/fe/tuto_003.bin",
    ]
    
    successful_files = []
    
    for file_path in tutorial_files:
        path_obj = Path(file_path)
        success = analyze_translation_injection(path_obj)
        if success:
            successful_files.append(path_obj)
        print()  # Blank line between files
    
    # Summary
    print("📋 SUMMARY")
    print("=" * 30)
    if successful_files:
        print(f"✅ {len(successful_files)} files show successful translation:")
        for file_path in successful_files:
            print(f"   📁 {file_path.name}")
        
        print(f"\n🎮 Next Steps:")
        print(f"   1. Test {successful_files[0].name} in Citra emulator")
        print(f"   2. Look for English text in tutorial dialogue")
        print(f"   3. If working, build full ROM with translations")
    else:
        print("❌ No files show clear translation success")
        print("🔧 Check translation injection process")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())