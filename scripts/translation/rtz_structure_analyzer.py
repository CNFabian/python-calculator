"""
RTZ File Structure Analyzer
Finds where actual dialogue text is located in the .bin files
"""

import sys
from pathlib import Path

def find_text_segments(file_path):
    """Find text segments using the 5-byte prefix pattern"""
    data = file_path.read_bytes()
    print(f"📁 Analyzing: {file_path.name} ({len(data):,} bytes)")
    
    # Look for the terminator pattern that marks text sections
    terminator = b'\xFF\xFF\xFF\xFF\x00'
    terminator_pos = data.find(terminator)
    
    if terminator_pos != -1:
        print(f"🔍 Found terminator at: 0x{terminator_pos:X}")
        
        # Look backwards from terminator for text segments
        # Text segments have 5-byte prefix: [4 bytes] + [length byte]
        search_start = max(0, terminator_pos - 5000)  # Search 5KB before terminator
        
        print(f"🔍 Searching for text segments from 0x{search_start:X} to 0x{terminator_pos:X}")
        
        segments_found = []
        pos = search_start
        
        while pos < terminator_pos - 5:
            # Check if this could be a 5-byte prefix
            if pos + 5 < len(data):
                length_byte = data[pos + 4]  # 5th byte is text length
                
                # Reasonable text length (1-200 UTF-16 characters)
                if 1 <= length_byte <= 200:
                    text_start = pos + 5
                    text_end = text_start + (length_byte * 2)  # UTF-16LE is 2 bytes per char
                    
                    if text_end <= len(data):
                        try:
                            # Try to decode as UTF-16LE
                            text_bytes = data[text_start:text_end]
                            text = text_bytes.decode('utf-16le', errors='ignore')
                            
                            # Check if it looks like meaningful text
                            if len(text.strip()) > 0 and any(c.isprintable() for c in text):
                                segments_found.append({
                                    'prefix_pos': pos,
                                    'text_pos': text_start,
                                    'length': length_byte,
                                    'text': text.strip()[:50]  # First 50 chars
                                })
                                
                                print(f"📝 Segment at 0x{pos:X}: len={length_byte} → '{text.strip()[:50]}'")
                        except:
                            pass
            
            pos += 1
        
        print(f"\n📊 Found {len(segments_found)} potential text segments")
        return segments_found
    else:
        print("⚠️  No terminator pattern found - checking alternative structure")
        
        # Alternative: look for UTF-16LE text patterns throughout file
        print("🔍 Scanning for UTF-16LE text patterns...")
        
        text_patterns = []
        for i in range(0, len(data) - 10, 2):
            if data[i + 1] == 0x00 and 32 <= data[i] <= 126:  # Potential UTF-16LE
                # Check if this starts a longer text sequence
                try:
                    chunk = data[i:i+40]
                    text = chunk.decode('utf-16le', errors='ignore')
                    clean_text = ''.join(c for c in text if c.isprintable()).strip()
                    
                    if len(clean_text) > 5 and not clean_text.startswith('.'):
                        text_patterns.append({
                            'position': i,
                            'text': clean_text[:30]
                        })
                        
                        if len(text_patterns) <= 10:  # Show first 10
                            print(f"📝 Text at 0x{i:X}: '{clean_text[:30]}'")
                except:
                    pass
        
        print(f"\n📊 Found {len(text_patterns)} text patterns")
        return text_patterns

def main():
    print("🔍 RTZ File Structure Analyzer")
    print("=" * 50)
    
    # Analyze both tutorial files
    files_to_analyze = [
        "romfs/fe/tuto_001.bin",
        "romfs/fe/tuto_008.bin"
    ]
    
    for file_path in files_to_analyze:
        path_obj = Path(file_path)
        if path_obj.exists():
            segments = find_text_segments(path_obj)
            print("\n" + "="*60 + "\n")
        else:
            print(f"❌ File not found: {file_path}")
    
    print("💡 Next Steps:")
    print("   - If text segments found: Your translation injection may have worked")
    print("   - If no segments found: Check if translation script ran correctly")
    print("   - Test in Citra emulator to see actual results")

if __name__ == "__main__":
    main()