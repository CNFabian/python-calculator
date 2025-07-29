#!/usr/bin/env python3
import sys
import struct
import re
import json

def extract_dialogue_segments(filename, offset=0):
    """Extract dialogue segments from RTZ file"""
    
    with open(filename, 'rb') as f:
        f.seek(offset)
        data = f.read()
    
    print(f"\n=== Extracting dialogue from {filename} ===")
    print(f"File size: {len(data)} bytes")
    
    # The file appears to have segments with length prefixes
    # Based on your error output, segments start with:
    # prefix@0xXXX: L=YYY → ZZZ bytes
    
    segments = []
    pos = offset
    segment_num = 1
    
    while pos < len(data) - 4:
        try:
            # Try to read as UTF-16LE with null terminators
            chunk = data[pos:pos+2000]  # Read chunk
            
            # Look for Japanese text patterns
            # Convert chunk to string
            try:
                text = chunk.decode('utf-16le', errors='ignore')
            except:
                pos += 1
                continue
            
            # Find dialogue patterns
            # Look for Japanese sentences ending with punctuation
            dialogue_pattern = r'[ぁ-んァ-ヶー一-龠０-９Ａ-Ｚａ-ｚ\s\n<>\|]+[。！？、]'
            matches = re.findall(dialogue_pattern, text)
            
            for match in matches:
                # Clean up the match
                clean = match.strip()
                if len(clean) > 5 and not clean.startswith('/'):  # Skip file paths
                    # Check if this looks like actual dialogue
                    if any(char in clean for char in 'のはがをにでと'):  # Common particles
                        segments.append({
                            'id': segment_num,
                            'offset': f'0x{pos:X}',
                            'japanese': clean,
                            'translation': ''  # To be filled later
                        })
                        segment_num += 1
            
            pos += 100  # Move forward
            
        except Exception as e:
            pos += 1
            continue
    
    return segments

def save_segments(segments, output_file):
    """Save extracted segments to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(segments)} segments to {output_file}")

def display_sample(segments, count=10):
    """Display sample of extracted segments"""
    print(f"\n== Sample of extracted dialogue ({count} of {len(segments)}) ==")
    for seg in segments[:count]:
        print(f"\n[{seg['id']}] @ {seg['offset']}")
        print(f"JP: {seg['japanese']}")
        if seg['translation']:
            print(f"EN: {seg['translation']}")

def extract_with_original_method(filename, offset=0):
    """Use the original script's method to extract"""
    print("\n=== Using original extraction method ===")
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Based on your error output, the game text contains patterns like:
    # この<|時|とき|>、ドライブチェックと<|同|おな|>じように
    
    # Try to decode as UTF-16LE
    try:
        text = data.decode('utf-16le', errors='ignore')
    except:
        text = data.decode('utf-8', errors='ignore')
    
    # Extract text with furigana markers
    furigana_pattern = r'([^<>\n]+(?:<\|[^|]+\|[^|]+\|>[^<>\n]*)*[。！？])'
    matches = re.findall(furigana_pattern, text)
    
    segments = []
    for i, match in enumerate(matches):
        if len(match) > 10:  # Meaningful text only
            # Clean up the furigana for display
            display_text = re.sub(r'<\|([^|]+)\|([^|]+)\|>', r'\1(\2)', match)
            segments.append({
                'id': i + 1,
                'raw': match,
                'display': display_text,
                'translation': ''
            })
    
    return segments

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_rtz_dialogue.py <filename> [output.json]")
        sys.exit(1)
    
    filename = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else filename.replace('.bin', '_dialogue.json')
    
    # Try original method first (based on your error output)
    segments = extract_with_original_method(filename)
    
    if segments:
        print(f"\nFound {len(segments)} dialogue segments!")
        display_sample(segments)
        save_segments(segments, output_file)
    else:
        print("\nTrying alternative extraction method...")
        segments = extract_dialogue_segments(filename)
        if segments:
            display_sample(segments)
            save_segments(segments, output_file)
        else:
            print("\nNo dialogue found. The file might need different extraction method.")
            print("Try using the original extract_rtz_content.py script.")