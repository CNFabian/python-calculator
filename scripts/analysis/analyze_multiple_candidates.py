#!/usr/bin/env python3
"""
Analyze multiple character select candidate files
Try to find readable Japanese text in the most promising files
"""

import gzip
import struct
import re
from pathlib import Path

def is_japanese_text(text):
    """Check if text contains Japanese characters"""
    if not text or len(text.strip()) < 2:
        return False
        
    japanese_chars = 0
    total_chars = 0
    
    for char in text:
        if char.isprintable():
            total_chars += 1
            if (
                '\u3040' <= char <= '\u309F' or  # Hiragana
                '\u30A0' <= char <= '\u30FF' or  # Katakana
                '\u4E00' <= char <= '\u9FAF' or  # CJK Unified Ideographs
                '\uFF00' <= char <= '\uFFEF'     # Halfwidth/Fullwidth Forms
            ):
                japanese_chars += 1
    
    if total_chars == 0:
        return False
        
    japanese_ratio = japanese_chars / total_chars
    return japanese_ratio >= 0.3

def contains_character_terms(text):
    """Check for character/UI related terms"""
    terms = [
        # Japanese UI terms
        'キャラクター', 'ファイター', 'プレイヤー', '選手', '名前', 'キャラ', 
        'クラン', '選択', '決定', '確認', 'メニュー', '画面', 'ボタン',
        # Vanguard character names
        'アイチ', 'カムイ', 'ミサキ', 'カイ', '先導', 'レン', 'アサカ',
        # English terms
        'character', 'fighter', 'player', 'name', 'clan', 'select', 'confirm',
        'menu', 'button', 'screen', 'aichi', 'kamui', 'misaki', 'kai'
    ]
    
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in terms)

def try_decompress_file(file_path):
    """Try to decompress file if it's compressed"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Check for gzip signature
        if data.startswith(b'\x1f\x8b'):
            try:
                with gzip.open(file_path, 'rb') as f:
                    decompressed = f.read()
                return decompressed, "gzip"
            except:
                pass
        
        # Check for other compression signatures
        if data.startswith(b'Yaz0'):
            return None, "yaz0 (unsupported)"
        elif data.startswith(b'LZ77'):
            return None, "lz77 (unsupported)"
        
        # Return as-is if not compressed
        return data, "uncompressed"
        
    except Exception as e:
        return None, f"error: {e}"

def extract_text_segments(data, max_segments=20):
    """Extract text segments from RTZ data"""
    if not data:
        return []
    
    segments = []
    
    # Look for RTZ terminator
    terminator = b'\xFF\xFF\xFF\xFF\x00'
    terminator_pos = data.find(terminator)
    search_end = terminator_pos if terminator_pos != -1 else len(data)
    
    pos = 0
    found_count = 0
    
    while pos < search_end - 5 and found_count < max_segments:
        if pos + 5 <= len(data):
            length_byte = data[pos + 4]
            
            if 1 <= length_byte <= 200:  # Reasonable text length
                text_start = pos + 5
                text_end = text_start + (length_byte * 2)
                
                if text_end <= len(data):
                    try:
                        text_bytes = data[text_start:text_end]
                        text = text_bytes.decode('utf-16le', errors='ignore')
                        clean = ''.join(c for c in text if c.isprintable() or c in '\n\r\t†').strip()
                        
                        if (len(clean) >= 2 and 
                            (is_japanese_text(clean) or 
                             contains_character_terms(clean) or
                             any(c.isalpha() for c in clean))):
                            
                            segments.append({
                                'pos': f"0x{pos:X}",
                                'length': length_byte,
                                'text': clean,
                                'is_japanese': is_japanese_text(clean),
                                'has_char_terms': contains_character_terms(clean)
                            })
                            
                            found_count += 1
                            pos = text_end
                            continue
                    except:
                        pass
        pos += 1
    
    return segments

def analyze_single_file(file_path):
    """Analyze a single candidate file"""
    print(f"\n📄 Analyzing: {file_path.name}")
    print(f"   📊 Size: {file_path.stat().st_size:,} bytes")
    
    # Try to read/decompress the file
    data, compression_type = try_decompress_file(file_path)
    
    if data is None:
        print(f"   ❌ Could not read file ({compression_type})")
        return []
    
    print(f"   🔍 Format: {compression_type}")
    if compression_type.startswith("gzip"):
        print(f"   📊 Decompressed size: {len(data):,} bytes")
    
    # Extract text segments
    segments = extract_text_segments(data)
    
    if segments:
        print(f"   ✅ Found {len(segments)} text segments")
        
        # Show most promising segments
        character_segments = [s for s in segments if s['has_char_terms']]
        japanese_segments = [s for s in segments if s['is_japanese']]
        
        if character_segments:
            print(f"   🎯 {len(character_segments)} segments contain character/UI terms:")
            for seg in character_segments[:3]:  # Show first 3
                print(f"      → '{seg['text'][:60]}'")
        
        elif japanese_segments:
            print(f"   🈯 {len(japanese_segments)} segments contain Japanese text:")
            for seg in japanese_segments[:3]:  # Show first 3
                print(f"      → '{seg['text'][:60]}'")
        
        else:
            print(f"   📝 Sample text segments:")
            for seg in segments[:3]:  # Show first 3
                print(f"      → '{seg['text'][:60]}'")
    
    else:
        print(f"   ⚠️  No readable text segments found")
    
    return segments

def main():
    """Analyze multiple character select candidate files"""
    print("🎮 MULTIPLE CHARACTER SELECT CANDIDATES ANALYSIS")
    print("=" * 60)
    
    # Define candidate files in priority order
    candidates = [
        'RomFS/fight/sys_menu.rtz',
        'RomFS/fight/card_menu.rtz', 
        'RomFS/system/standup.rtz',
        'RomFS/system/deck_list.rtz',
        'RomFS/system/option.rtz',
        'RomFS/system/shop.rtz',
        'RomFS/system/commu_list.rtz'
    ]
    
    all_results = []
    
    for candidate_path in candidates:
        file_path = Path(candidate_path)
        
        if file_path.exists():
            segments = analyze_single_file(file_path)
            
            if segments:
                # Score the file based on text quality
                character_score = len([s for s in segments if s['has_char_terms']]) * 10
                japanese_score = len([s for s in segments if s['is_japanese']]) * 5
                total_score = character_score + japanese_score + len(segments)
                
                all_results.append({
                    'file': file_path,
                    'segments': segments,
                    'score': total_score,
                    'character_segments': len([s for s in segments if s['has_char_terms']]),
                    'japanese_segments': len([s for s in segments if s['is_japanese']])
                })
        else:
            print(f"\n📄 {Path(candidate_path).name}: ❌ File not found")
    
    # Show results summary
    print(f"\n🏆 ANALYSIS SUMMARY")
    print("=" * 40)
    
    if all_results:
        # Sort by score (best first)
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"📊 Analyzed {len(all_results)} files successfully:")
        print()
        
        for i, result in enumerate(all_results, 1):
            file = result['file']
            segments = result['segments']
            char_segs = result['character_segments']
            jp_segs = result['japanese_segments']
            
            print(f"[{i}] {file.name}")
            print(f"    📊 Score: {result['score']} points")
            print(f"    📝 {len(segments)} total segments")
            if char_segs > 0:
                print(f"    🎯 {char_segs} character/UI segments")
            if jp_segs > 0:
                print(f"    🈯 {jp_segs} Japanese segments")
            print()
        
        # Recommend best file
        best_file = all_results[0]
        print(f"💡 RECOMMENDATION:")
        print(f"   🥇 Best candidate: {best_file['file'].name}")
        print(f"   📝 Contains {len(best_file['segments'])} text segments")
        
        if best_file['character_segments'] > 0:
            print(f"   🎯 {best_file['character_segments']} segments likely contain character interface text")
            print(f"   🔧 This file is ready for translation extraction!")
        elif best_file['japanese_segments'] > 0:
            print(f"   🈯 {best_file['japanese_segments']} segments contain Japanese text")
            print(f"   🔧 May contain character names or interface text")
        else:
            print(f"   ⚠️  No obvious character-related text found")
    
    else:
        print("❌ No files contained readable text")
        print("   🔧 Character select text might be stored in:")
        print("      - Different file format")
        print("      - Code.bin (already extracted)")
        print("      - Image/graphics files")
    
    return all_results

if __name__ == "__main__":
    main()