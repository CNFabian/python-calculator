#!/usr/bin/env python3
"""
Decompress fighter_info.rtz and extract Japanese character text
The file is gzip compressed, so we need to decompress it first
"""

import gzip
import struct
import re
from pathlib import Path

def decompress_rtz_file(file_path):
    """Decompress gzip-compressed RTZ file"""
    print(f"🔓 Decompressing {file_path.name}...")
    
    try:
        with gzip.open(file_path, 'rb') as f:
            decompressed_data = f.read()
        
        print(f"✅ Decompression successful!")
        print(f"📊 Original size: {file_path.stat().st_size:,} bytes")
        print(f"📊 Decompressed size: {len(decompressed_data):,} bytes")
        print(f"📊 Compression ratio: {file_path.stat().st_size / len(decompressed_data):.2f}x")
        
        return decompressed_data
        
    except Exception as e:
        print(f"❌ Decompression failed: {e}")
        print("   File might not be gzip compressed or might be corrupted")
        return None

def is_japanese_text(text):
    """Check if text contains Japanese characters"""
    if not text or len(text.strip()) < 2:
        return False
        
    japanese_chars = 0
    total_chars = 0
    
    for char in text:
        if char.isprintable():
            total_chars += 1
            # Check for Japanese character ranges
            if (
                '\u3040' <= char <= '\u309F' or  # Hiragana
                '\u30A0' <= char <= '\u30FF' or  # Katakana
                '\u4E00' <= char <= '\u9FAF' or  # CJK Unified Ideographs
                '\uFF00' <= char <= '\uFFEF'     # Halfwidth/Fullwidth Forms
            ):
                japanese_chars += 1
    
    if total_chars == 0:
        return False
        
    # Text should be at least 30% Japanese characters
    japanese_ratio = japanese_chars / total_chars
    return japanese_ratio >= 0.3

def contains_character_terms(text):
    """Check for character/fighter related terms"""
    character_terms = [
        # Japanese character terms
        'キャラクター', 'ファイター', 'プレイヤー', '選手', '名前', 'キャラ', 
        'クラン', '選択', '決定', '確認', 'せんたく', 'けってい', 'かくにん',
        # Common Vanguard character names (partial)
        'アイチ', 'カムイ', 'ミサキ', 'カイ', '先導', 'せんどう', 'アイチ',
        # English terms
        'character', 'fighter', 'player', 'name', 'clan', 'select', 'confirm',
        'aichi', 'kamui', 'misaki', 'kai',
        # UI terms
        'ボタン', 'メニュー', '画面', 'がめん', 'ぼたん', 'めにゅー'
    ]
    
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in character_terms)

def extract_text_segments_from_decompressed(data):
    """Extract text segments from decompressed RTZ data"""
    print(f"\n🔍 Extracting text from decompressed data...")
    print(f"📊 Data size: {len(data):,} bytes")
    
    # Look for RTZ terminator pattern
    terminator = b'\xFF\xFF\xFF\xFF\x00'
    terminator_pos = data.find(terminator)
    
    if terminator_pos != -1:
        print(f"✅ Found RTZ terminator at: 0x{terminator_pos:X}")
        search_end = terminator_pos
    else:
        print("⚠️  No RTZ terminator found, searching entire file")
        search_end = len(data)
    
    segments = []
    pos = 0
    segment_count = 0
    
    print(f"🔍 Searching for text segments from 0x0 to 0x{search_end:X}")
    
    while pos < search_end - 5:
        # Look for 5-byte prefix pattern: [4 bytes] + [length byte]
        if pos + 5 <= len(data):
            length_byte = data[pos + 4]  # 5th byte is text length in UTF-16 units
            
            # Reasonable text length (1-200 UTF-16 characters)
            if 1 <= length_byte <= 200:
                text_start = pos + 5
                text_end = text_start + (length_byte * 2)  # UTF-16LE is 2 bytes per char
                
                if text_end <= len(data):
                    try:
                        # Try to decode as UTF-16LE
                        text_bytes = data[text_start:text_end]
                        text = text_bytes.decode('utf-16le', errors='ignore')
                        
                        # Clean the text
                        clean = ''.join(c for c in text if c.isprintable() or c in '\n\r\t†')
                        clean = clean.strip()
                        
                        # Check if it looks like meaningful text
                        if (len(clean) >= 2 and 
                            (is_japanese_text(clean) or 
                             contains_character_terms(clean) or
                             any(c.isalpha() for c in clean))):
                            
                            segment_count += 1
                            segments.append({
                                'index': segment_count,
                                'prefix_pos': f"0x{pos:X}",
                                'text_pos': f"0x{text_start:X}",
                                'length': length_byte,
                                'raw_text': text,
                                'clean_text': clean,
                                'is_japanese': is_japanese_text(clean),
                                'has_char_terms': contains_character_terms(clean)
                            })
                            
                            print(f"📝 Segment {segment_count} at 0x{pos:X}: len={length_byte} → '{clean[:80]}'")
                            
                            # Move to next potential segment
                            pos = text_end
                            continue
                    except:
                        pass
        
        pos += 1
    
    print(f"\n📊 Found {len(segments)} text segments")
    return segments

def analyze_decompressed_fighter_info():
    """Main analysis function for decompressed fighter info"""
    print("🎮 DECOMPRESSED FIGHTER INFO ANALYSIS")
    print("=" * 50)
    
    file_path = Path('RomFS/fight/fighter_info.rtz')
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return []
    
    # Decompress the file
    decompressed_data = decompress_rtz_file(file_path)
    
    if decompressed_data is None:
        return []
    
    # Show first few bytes of decompressed data
    print(f"\n🔍 First 32 bytes of decompressed data:")
    header = decompressed_data[:32]
    print(f"   Hex: {header.hex().upper()}")
    print(f"   Raw: {repr(header)}")
    
    # Extract text segments
    segments = extract_text_segments_from_decompressed(decompressed_data)
    
    if segments:
        print(f"\n📝 EXTRACTED CHARACTER TEXT")
        print("=" * 40)
        
        character_related = []
        japanese_text = []
        other_text = []
        
        for segment in segments:
            if segment['has_char_terms']:
                character_related.append(segment)
            elif segment['is_japanese']:
                japanese_text.append(segment)
            else:
                other_text.append(segment)
        
        # Show character-related text first (highest priority)
        if character_related:
            print(f"\n🎯 CHARACTER-RELATED TEXT ({len(character_related)} segments):")
            for segment in character_related:
                print(f"[{segment['index']}] {segment['prefix_pos']}: '{segment['clean_text']}'")
                print(f"    → Contains character/fighter terms")
                print()
        
        # Show Japanese text
        if japanese_text:
            print(f"\n🈯 JAPANESE TEXT ({len(japanese_text)} segments):")
            for segment in japanese_text[:10]:  # Show first 10
                print(f"[{segment['index']}] {segment['prefix_pos']}: '{segment['clean_text']}'")
            
            if len(japanese_text) > 10:
                print(f"    ... and {len(japanese_text) - 10} more Japanese text segments")
        
        # Show other text
        if other_text:
            print(f"\n📄 OTHER TEXT ({len(other_text)} segments):")
            for segment in other_text[:5]:  # Show first 5
                print(f"[{segment['index']}] {segment['prefix_pos']}: '{segment['clean_text']}'")
            
            if len(other_text) > 5:
                print(f"    ... and {len(other_text) - 5} more text segments")
    
    else:
        print("\n⚠️  No text segments found even after decompression")
        print("   This might indicate:")
        print("   - Different RTZ text storage format")
        print("   - File contains binary data, not text")
        print("   - Different text encoding method")
    
    return segments

def main():
    """Main function"""
    segments = analyze_decompressed_fighter_info()
    
    if segments:
        character_segments = [s for s in segments if s['has_char_terms'] or s['is_japanese']]
        
        print(f"\n💡 ANALYSIS RESULTS:")
        print(f"   ✅ Successfully decompressed fighter_info.rtz")
        print(f"   📝 Found {len(segments)} total text segments")
        
        if character_segments:
            print(f"   🎯 Found {len(character_segments)} character-related text segments")
            print(f"   📄 This file contains character select interface text!")
            print(f"   🔧 Ready for translation extraction and injection")
        else:
            print(f"   ⚠️  No character-specific text found")
            print(f"   🔧 Try analyzing other candidate files")
    else:
        print(f"\n⚠️  No text extracted")
        print(f"   🔧 Try other character select candidate files:")
        print(f"      → fight/sys_menu.rtz")
        print(f"      → system/standup.rtz") 
        print(f"      → fight/card_menu.rtz")
    
    return segments

if __name__ == "__main__":
    main()