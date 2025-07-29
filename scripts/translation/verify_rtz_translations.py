#!/usr/bin/env python3
"""
RTZ Translation Verification Tool
Checks if English translations are properly embedded in tutorial files
"""

import sys
from pathlib import Path

def search_utf16_text(file_path, search_terms):
    """Search for UTF-16LE encoded terms in binary file"""
    try:
        data = Path(file_path).read_bytes()
        results = {}
        
        for term in search_terms:
            # Convert to UTF-16LE bytes
            utf16_bytes = term.encode('utf-16le')
            
            # Search for exact matches
            pos = data.find(utf16_bytes)
            if pos != -1:
                results[term] = {
                    'found': True,
                    'position': f'0x{pos:X}',
                    'context': data[max(0, pos-20):pos+len(utf16_bytes)+20]
                }
            else:
                results[term] = {'found': False}
        
        return results
    except Exception as e:
        return {'error': str(e)}

def analyze_file_changes(original_size, current_size):
    """Analyze if file size changes indicate successful injection"""
    if current_size > original_size:
        return f"✅ File grew by {current_size - original_size} bytes (translation likely successful)"
    elif current_size == original_size:
        return f"⚠️  File size unchanged ({current_size} bytes) - fixed-size replacement"
    else:
        return f"❌ File shrunk by {original_size - current_size} bytes (potential issue)"

def check_english_content(file_path):
    """Check for English letter patterns in the file"""
    try:
        data = Path(file_path).read_bytes()
        
        # Count English letters
        english_chars = sum(1 for b in data if 65 <= b <= 90 or 97 <= b <= 122)
        
        # Look for common English words in UTF-16LE
        common_words = ["the", "and", "you", "can", "will", "this", "card", "play"]
        found_words = []
        
        for word in common_words:
            utf16_word = word.encode('utf-16le')
            if utf16_word in data:
                found_words.append(word)
        
        return {
            'english_char_count': english_chars,
            'english_percentage': (english_chars / len(data)) * 100,
            'common_words_found': found_words
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    print("🔍 RTZ Translation Verification Tool\n")
    
    # Files to check
    test_files = [
        "romfs/fe/tuto_001.bin",
        "romfs/fe/tuto_008.bin"
    ]
    
    # English terms we expect to find based on your translations
    english_terms = [
        "Home", "Damage", "Zone", "Card", "Field", 
        "Vanguard", "Grade", "Play", "Mat", "Fight",
        "explain", "detail", "place", "number"
    ]
    
    for file_path in test_files:
        print(f"📁 Checking: {file_path}")
        
        if not Path(file_path).exists():
            print(f"   ❌ File not found\n")
            continue
            
        file_size = Path(file_path).stat().st_size
        print(f"   📊 File size: {file_size:,} bytes")
        
        # Search for specific English terms
        results = search_utf16_text(file_path, english_terms)
        
        found_terms = [term for term, data in results.items() 
                      if isinstance(data, dict) and data.get('found')]
        
        if found_terms:
            print(f"   ✅ Found English terms: {', '.join(found_terms)}")
            for term in found_terms[:3]:  # Show first 3 positions
                pos = results[term]['position']
                print(f"      - '{term}' at {pos}")
        else:
            print(f"   ⚠️  No exact English terms found")
            
        # Check for general English content
        english_analysis = check_english_content(file_path)
        if 'error' not in english_analysis:
            char_count = english_analysis['english_char_count']
            percentage = english_analysis['english_percentage']
            words_found = english_analysis['common_words_found']
            
            if char_count > 100:
                print(f"   📝 Contains {char_count} English letters ({percentage:.1f}% of file)")
            
            if words_found:
                print(f"   🔤 Common English words found: {', '.join(words_found)}")
        
        print()

    print("💡 Verification Analysis:")
    print("   ✅ If terms found: Translation injection successful")
    print("   ⚠️  If no exact terms: May be using fixed-size padding")
    print("   📊 File size changes indicate injection occurred")
    print("   🎮 Ultimate test: Load in Citra emulator")
    
    print("\n🎯 Recommended Next Steps:")
    print("   1. Run this verification script")
    print("   2. If translations detected: Test in Citra")
    print("   3. If no translations: Check injection process")
    print("   4. Scale to full tutorial dataset if working")

if __name__ == "__main__":
    main()