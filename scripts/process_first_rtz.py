import gzip
import re
import json
import requests
from pathlib import Path

def find_tutorial_rtz():
    """Find a tutorial RTZ file to start with"""
    
    romfs_path = Path('RomFS')
    
    # Look for tutorial files first (easiest to translate)
    tutorial_patterns = ['tuto', 'tutorial', 'help']
    
    for pattern in tutorial_patterns:
        matches = list(romfs_path.rglob(f'*{pattern}*.rtz'))
        if matches:
            return matches[0]
    
    # If no tutorial files, get any RTZ file
    all_rtz = list(romfs_path.rglob('*.rtz'))
    if all_rtz:
        return all_rtz[0]
    
    return None

def decompress_rtz(rtz_path):
    """Decompress RTZ file"""
    
    try:
        with gzip.open(rtz_path, 'rb') as f:
            decompressed = f.read()
        print(f"✅ Decompressed {rtz_path.name}: {len(decompressed):,} bytes")
        return decompressed
    except Exception as e:
        print(f"❌ Failed to decompress {rtz_path.name}: {e}")
        return None

def extract_text_segments(data, start_offset=0):
    """Extract text segments from RTZ data using the project's method"""
    
    print(f"🔍 Scanning for text segments starting at offset 0x{start_offset:X}")
    
    segments = []
    pos = start_offset
    
    while pos + 5 <= len(data):
        # Look for terminator
        if data[pos:pos+5] == b'\xFF\xFF\xFF\xFF\x00':
            print(f"📍 Found terminator at 0x{pos:X}")
            break
        
        # Try to read segment header (5 bytes)
        if pos + 5 > len(data):
            break
            
        # 5th byte should be UTF-16 character count
        char_count = data[pos + 4]
        if char_count == 0 or char_count > 100:  # Reasonable limits
            pos += 1
            continue
        
        byte_length = char_count * 2
        text_start = pos + 5
        text_end = text_start + byte_length
        
        if text_end > len(data):
            pos += 1
            continue
        
        # Try to decode as UTF-16LE
        try:
            text_bytes = data[text_start:text_end]
            text = text_bytes.decode('utf-16le', errors='ignore')
            
            # Check if it looks like actual text
            if len(text.strip()) > 0 and any(c.isprintable() for c in text):
                segments.append({
                    'offset': pos,
                    'char_count': char_count,
                    'text': text.strip(),
                    'raw_bytes': text_bytes
                })
                
                print(f"📝 Found text at 0x{pos:X}: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
                
                pos = text_end
            else:
                pos += 1
        except:
            pos += 1
    
    return segments

def translate_segments(segments):
    """Translate the extracted text segments"""
    
    print(f"\n🌐 Translating {len(segments)} text segments...")
    
    for i, segment in enumerate(segments):
        # Skip very short segments
        if len(segment['text'].strip()) < 3:
            segment['translation'] = segment['text']
            continue
        
        try:
            # Use your LibreTranslate API
            response = requests.post(
                'http://localhost:5001/translate',
                json={
                    'q': segment['text'],
                    'source': 'ja',
                    'target': 'en',
                    'format': 'text'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                segment['translation'] = result.get('translatedText', segment['text'])
                print(f"✅ [{i+1}] Translated: \"{segment['translation'][:50]}{'...' if len(segment['translation']) > 50 else ''}\"")
            else:
                segment['translation'] = segment['text']
                print(f"❌ [{i+1}] Translation failed")
                
        except Exception as e:
            segment['translation'] = segment['text']
            print(f"❌ [{i+1}] Translation error: {e}")
    
    return segments

def main():
    """Process first RTZ file"""
    
    print("🎮 RTZ FILE PROCESSING TEST")
    print("=" * 40)
    
    # Find RTZ file to process
    rtz_file = find_tutorial_rtz()
    if not rtz_file:
        print("❌ No RTZ files found in RomFS/")
        return
    
    print(f"🎯 Processing: {rtz_file.relative_to(Path('RomFS'))}")
    
    # Decompress
    data = decompress_rtz(rtz_file)
    if not data:
        return
    
    # Extract text segments
    segments = extract_text_segments(data)
    
    if not segments:
        print("❌ No text segments found. May need different offset or method.")
        
        # Try different starting offsets
        for offset in [0x100, 0x200, 0x400, 0x800, 0x1000]:
            print(f"\n🔍 Trying offset 0x{offset:X}...")
            segments = extract_text_segments(data, offset)
            if segments:
                break
    
    if segments:
        # Translate segments
        translated_segments = translate_segments(segments)
        
        # Save results
        output_file = f"rtz_translation_{rtz_file.stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_segments, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ PROCESSING COMPLETE!")
        print(f"   📁 File: {rtz_file.name}")
        print(f"   📝 Text segments: {len(segments)}")
        print(f"   💾 Results saved: {output_file}")
        
    else:
        print("❌ No text segments found. RTZ format may be different than expected.")

if __name__ == "__main__":
    main()
