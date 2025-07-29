#!/usr/bin/env python3
"""
Advanced Fighter Info RTZ Analyzer
Try multiple extraction methods to find readable Japanese text
"""

import struct
import re
from pathlib import Path

def try_different_encodings(data, start_pos, length):
    """Try different text encodings to find readable content"""
    encodings_to_try = [
        ('utf-16le', 'UTF-16LE (Little Endian)'),
        ('utf-16be', 'UTF-16BE (Big Endian)'),
        ('utf-8', 'UTF-8'),
        ('shift_jis', 'Shift JIS (Japanese)'),
        ('euc-jp', 'EUC-JP (Japanese)'),
        ('cp932', 'CP932 (Windows Japanese)')
    ]
    
    results = []
    text_bytes = data[start_pos:start_pos + length]
    
    for encoding, name in encodings_to_try:
        try:
            decoded = text_bytes.decode(encoding, errors='ignore')
            clean = ''.join(c for c in decoded if c.isprintable() or c in '\n\r\t')
            
            if len(clean.strip()) > 0:
                # Check for Japanese characters
                japanese_chars = sum(1 for c in clean if 
                    '\u3040' <= c <= '\u309F' or  # Hiragana
                    '\u30A0' <= c <= '\u30FF' or  # Katakana
                    '\u4E00' <= c <= '\u9FAF')    # Kanji
                
                results.append({
                    'encoding': name,
                    'text': clean[:100],  # First 100 chars
                    'japanese_chars': japanese_chars,
                    'total_chars': len(clean),
                    'quality_score': japanese_chars / max(len(clean), 1)
                })
        except:
            continue
    
    return sorted(results, key=lambda x: x['quality_score'], reverse=True)

def search_for_japanese_patterns(data):
    """Search for Japanese text patterns throughout the file"""
    print("🔍 Searching for Japanese text patterns...")
    
    found_patterns = []
    
    # Search for common Japanese patterns in different encodings
    for i in range(0, len(data) - 10, 1):  # Byte by byte search
        
        # Try UTF-16LE patterns (every 2 bytes)
        if i % 2 == 0 and i + 4 <= len(data):
            try:
                chunk = data[i:i+20]  # 10 UTF-16 characters max
                text = chunk.decode('utf-16le', errors='ignore')
                
                # Look for Japanese character patterns
                if any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF' 
                       for c in text):
                    clean = ''.join(c for c in text if c.isprintable())
                    if len(clean) >= 2:  # At least 2 readable characters
                        found_patterns.append({
                            'position': f"0x{i:X}",
                            'encoding': 'UTF-16LE',
                            'text': clean[:50]
                        })
            except:
                pass
        
        # Try Shift JIS patterns
        if i + 6 <= len(data):
            try:
                chunk = data[i:i+12]  # 6 Shift JIS characters max
                text = chunk.decode('shift_jis', errors='ignore')
                
                if any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF' 
                       for c in text):
                    clean = ''.join(c for c in text if c.isprintable())
                    if len(clean) >= 2:
                        found_patterns.append({
                            'position': f"0x{i:X}",
                            'encoding': 'Shift_JIS',
                            'text': clean[:50]
                        })
            except:
                pass
    
    # Remove duplicates and sort by position
    unique_patterns = []
    seen_texts = set()
    
    for pattern in found_patterns:
        if pattern['text'] not in seen_texts:
            seen_texts.add(pattern['text'])
            unique_patterns.append(pattern)
    
    return sorted(unique_patterns, key=lambda x: int(x['position'], 16))

def analyze_file_structure(data):
    """Analyze the overall file structure for clues"""
    print("🔍 Analyzing file structure...")
    
    # Check first 32 bytes for headers/magic numbers
    header = data[:32]
    print(f"📊 First 32 bytes (hex): {header.hex().upper()}")
    print(f"📊 First 32 bytes (raw): {repr(header)}")
    
    # Look for repeating patterns that might indicate structure
    print(f"\n🔍 Looking for structural patterns...")
    
    # Common RTZ/archive signatures
    signatures = [
        (b'RTZ', 'RTZ archive'),
        (b'RIFF', 'RIFF container'),
        (b'Yaz0', 'Yaz0 compression'),
        (b'LZ77', 'LZ77 compression'),
        (b'\xFF\xFF\xFF\xFF\x00', 'RTZ terminator'),
        (b'\x00\x00\x00\x00', 'Null padding')
    ]
    
    for sig, desc in signatures:
        positions = []
        pos = 0
        while pos < len(data):
            pos = data.find(sig, pos)
            if pos == -1:
                break
            positions.append(f"0x{pos:X}")
            pos += 1
        
        if positions:
            print(f"   📍 {desc}: {', '.join(positions[:5])}" + 
                  (f" (+{len(positions)-5} more)" if len(positions) > 5 else ""))

def hex_dump_interesting_sections(data):
    """Show hex dump of potentially interesting sections"""
    print("\n🔍 Hex dump of interesting sections:")
    
    # Show first 64 bytes
    print(f"\n📄 First 64 bytes:")
    for i in range(0, min(64, len(data)), 16):
        hex_part = ' '.join(data[i:i+16].hex()[j:j+2] for j in range(0, len(data[i:i+16].hex()), 2))
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
        print(f"   {i:04X}: {hex_part:<48} |{ascii_part}|")
    
    # Look for sections with high byte values (potential compressed/encoded data)
    print(f"\n📄 Searching for text-like sections...")
    
    for start in range(0, len(data) - 32, 32):
        chunk = data[start:start+32]
        
        # Count printable ASCII characters
        printable_count = sum(1 for b in chunk if 32 <= b <= 126)
        
        # If section has reasonable amount of printable chars, show it
        if printable_count >= 8:  # At least 25% printable
            hex_part = ' '.join(chunk.hex()[j:j+2] for j in range(0, len(chunk.hex()), 2))
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            print(f"   {start:04X}: {hex_part} |{ascii_part}|")

def main():
    """Main advanced analysis"""
    print("🎮 ADVANCED FIGHTER INFO ANALYSIS")
    print("=" * 50)
    
    file_path = Path('RomFS/fight/fighter_info.rtz')
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"📄 File: {file_path}")
    print(f"📊 Size: {len(data):,} bytes")
    
    # Analyze file structure
    analyze_file_structure(data)
    
    # Search for Japanese text patterns
    patterns = search_for_japanese_patterns(data)
    
    if patterns:
        print(f"\n✅ Found {len(patterns)} potential Japanese text patterns:")
        print("=" * 50)
        
        for i, pattern in enumerate(patterns[:10], 1):  # Show first 10
            print(f"[{i}] {pattern['position']} ({pattern['encoding']}): '{pattern['text']}'")
        
        if len(patterns) > 10:
            print(f"... and {len(patterns) - 10} more patterns")
            
    else:
        print("\n⚠️  No clear Japanese text patterns found")
        print("   This suggests the file might be:")
        print("   - Compressed with unknown format")
        print("   - Using different text storage method") 
        print("   - Primarily containing binary/image data")
    
    # Show hex dump of interesting sections
    hex_dump_interesting_sections(data)
    
    print(f"\n💡 RECOMMENDATIONS:")
    if patterns:
        print(f"   ✅ Try extracting text using best encoding found")
        print(f"   🔧 Focus on positions with readable Japanese text")  
        print(f"   📝 This file likely contains character interface text")
    else:
        print(f"   🔧 Try analyzing other candidate files:")
        print(f"      → fight/sys_menu.rtz (system menu)")
        print(f"      → system/standup.rtz (character setup)")
        print(f"      → fight/card_menu.rtz (card/character menu)")
        print(f"   📝 fighter_info.rtz might be binary data, not text")

if __name__ == "__main__":
    main()