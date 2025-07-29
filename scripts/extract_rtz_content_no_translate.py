#!/usr/bin/env python3
import sys
import struct
import re

def clean_text(text):
    """Clean extracted text"""
    # Remove null bytes and control characters
    text = text.replace('\x00', '')
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    return text.strip()

def extract_japanese_text(data):
    """Extract Japanese text patterns from binary data"""
    found_texts = []
    
    # Pattern 1: Look for Japanese text between common delimiters
    # Japanese characters are typically in these ranges:
    # Hiragana: 3040-309F
    # Katakana: 30A0-30FF
    # Kanji: 4E00-9FAF
    
    # Convert bytes to string, ignoring errors
    try:
        text = data.decode('utf-16le', errors='ignore')
    except:
        text = data.decode('utf-8', errors='ignore')
    
    # Find Japanese text patterns
    japanese_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+'
    matches = re.findall(japanese_pattern, text)
    
    for match in matches:
        if len(match) > 3:  # Only keep meaningful text
            found_texts.append(match)
    
    # Also look for text with special markers
    # The game seems to use patterns like <|kanji|reading|>
    special_pattern = r'<\|([^|]+)\|([^|]+)\|>'
    special_matches = re.findall(special_pattern, text)
    for kanji, reading in special_matches:
        found_texts.append(f"{kanji} ({reading})")
    
    return found_texts

def analyze_file(filename, offset=0):
    """Analyze RTZ file content"""
    print(f"\n=== Analyzing {filename} ===")
    
    with open(filename, 'rb') as f:
        f.seek(offset)
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Try to find text segments
    print("\n== Looking for Japanese text ==")
    texts = extract_japanese_text(data)
    
    if texts:
        print(f"Found {len(texts)} text segments:")
        for i, text in enumerate(texts[:20]):  # Show first 20
            print(f"[{i+1}] {text}")
        if len(texts) > 20:
            print(f"... and {len(texts) - 20} more")
    else:
        print("No Japanese text found with current method")
    
    # Look for specific patterns in hex
    print("\n== Checking for known patterns ==")
    
    # Check for UTF-16 BOM
    if data[:2] == b'\xff\xfe':
        print("Found UTF-16 LE BOM")
    elif data[:2] == b'\xfe\xff':
        print("Found UTF-16 BE BOM")
    
    # Look for common Japanese game text
    test_strings = [
        "この時",  # "At this time"
        "ヴァンガード",  # "Vanguard"
        "ダメージ",  # "Damage"
        "アタック",  # "Attack"
    ]
    
    for test in test_strings:
        try:
            if test.encode('utf-16le') in data:
                print(f"Found '{test}' in UTF-16LE")
            elif test.encode('utf-8') in data:
                print(f"Found '{test}' in UTF-8")
            elif test.encode('shift-jis') in data:
                print(f"Found '{test}' in Shift-JIS")
        except:
            pass
    
    # Show hex dump of beginning
    print("\n== First 256 bytes (hex) ==")
    for i in range(0, min(256, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"{i:04x}: {hex_str:<48} {ascii_str}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_rtz_content_no_translate.py <filename> [offset]")
        sys.exit(1)
    
    filename = sys.argv[1]
    offset = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0
    
    analyze_file(filename, offset)