#!/usr/bin/env python3
"""
CF Vanguard RTZ Translation Injection
Injects translated dialogue back into tutorial RTZ files
"""
import struct
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import shutil

class RTZInjector:
    def __init__(self):
        self.TERMINATOR = b'\xFF\xFF\xFF\xFF\x00'
        
    def encode_text_segment(self, text: str) -> bytes:
        """Encode English text as UTF-16LE segment"""
        if not text:
            return b''
            
        # Convert newlines back to special character
        text = text.replace('\n', '†')
        
        # Encode as UTF-16LE
        utf16_bytes = text.encode('utf-16le')
        
        # Calculate length in UTF-16 units (2-byte units)
        utf16_length = len(utf16_bytes) // 2
        
        # Create segment: [4 unknown bytes] + [1 length byte] + [UTF-16 data]
        # Using common pattern from extracted data
        prefix = b'\x00\x00\x00\x00'  # Common prefix pattern
        length_byte = struct.pack('B', utf16_length)
        
        return prefix + length_byte + utf16_bytes
    
    def find_text_segments(self, data: bytes, start_offset: int = 0) -> List[Tuple[int, int, int]]:
        """Find all text segments in RTZ data
        Returns: List of (prefix_pos, content_start, content_end)
        """
        segments = []
        pos = start_offset
        
        while pos + 5 <= len(data):
            # Check for terminator
            if data[pos:pos+5] == self.TERMINATOR:
                break
                
            # Read length byte
            length = data[pos + 4]
            byte_length = length * 2
            
            content_start = pos + 5
            content_end = content_start + byte_length
            
            if content_end > len(data):
                break
                
            segments.append((pos, content_start, content_end))
            pos = content_end
            
        return segments
    
    def inject_translations(self, original_rtz: Path, translations: Dict[int, str], output_rtz: Path) -> bool:
        """Inject translations into RTZ file"""
        try:
            # Read original RTZ
            with open(original_rtz, 'rb') as f:
                data = bytearray(f.read())
            
            print(f"📂 Processing {original_rtz.name}")
            print(f"   Original size: {len(data):,} bytes")
            
            # Find existing segments
            segments = self.find_text_segments(data)
            print(f"   Found {len(segments)} text segments")
            
            if not segments:
                print("   ⚠️  No text segments found, copying original")
                shutil.copy2(original_rtz, output_rtz)
                return False
            
            # Build new data
            new_data = bytearray()
            
            # Copy data before first segment
            if segments:
                new_data.extend(data[:segments[0][0]])
            
            translated_count = 0
            total_size_change = 0
            
            # Process each segment
            for i, (prefix_pos, content_start, content_end) in enumerate(segments):
                segment_id = i + 1
                
                if segment_id in translations and translations[segment_id]:
                    # Use translation
                    translated_text = translations[segment_id]
                    new_segment = self.encode_text_segment(translated_text)
                    translated_count += 1
                    
                    # Size change tracking
                    original_size = content_end - prefix_pos
                    size_change = len(new_segment) - original_size
                    total_size_change += size_change
                    
                    print(f"   [{segment_id}] Translated: {len(translated_text)} chars -> {len(new_segment)} bytes (Δ{size_change:+d})")
                else:
                    # Keep original
                    new_segment = data[prefix_pos:content_end]
                    print(f"   [{segment_id}] Kept original: {content_end - prefix_pos} bytes")
                
                new_data.extend(new_segment)
                
                # Copy data between segments
                if i < len(segments) - 1:
                    next_start = segments[i + 1][0]
                    new_data.extend(data[content_end:next_start])
            
            # Copy remaining data after last segment
            if segments:
                last_end = segments[-1][2]
                new_data.extend(data[last_end:])
            
            # Write new RTZ file
            with open(output_rtz, 'wb') as f:
                f.write(new_data)
            
            print(f"   ✅ Saved: {len(new_data):,} bytes (Δ{total_size_change:+d})")
            print(f"   📊 Translated: {translated_count}/{len(segments)} segments")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error injecting {original_rtz.name}: {e}")
            return False
    
    def process_all_tutorials(self, translations_csv: Path, tutorial_bin_dir: Path, output_dir: Path):
        """Process all tutorial files with translations"""
        print("🎮 CF Vanguard RTZ Translation Injection")
        print("=" * 50)
        
        # Load translations
        if not translations_csv.exists():
            print(f"❌ Translations file not found: {translations_csv}")
            return
        
        print(f"📊 Loading translations from {translations_csv}")
        df = pd.read_csv(translations_csv)
        
        # Filter for translated content only
        df_translated = df[
            (df['status'] == 'TRANSLATED') & 
            (df['quality_tier'].isin(['HIGH', 'MEDIUM']))
        ].copy()
        
        print(f"   Found {len(df_translated)} high-quality translations")
        
        # Group by file
        file_translations = {}
        for _, row in df_translated.iterrows():
            file_name = row['file']
            segment_id = row['segment_id'] 
            translation = row['english_translation']
            
            if file_name not in file_translations:
                file_translations[file_name] = {}
            
            file_translations[file_name][segment_id] = translation
        
        print(f"   Translations for {len(file_translations)} files")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each tutorial file
        processed_files = 0
        successful_files = 0
        
        for file_name, translations in file_translations.items():
            # Convert .txt file name back to .bin
            bin_name = file_name.replace('.txt', '.bin')
            original_bin = tutorial_bin_dir / bin_name
            output_bin = output_dir / bin_name
            
            if not original_bin.exists():
                print(f"⚠️  Original file not found: {original_bin}")
                continue
                
            processed_files += 1
            
            if self.inject_translations(original_bin, translations, output_bin):
                successful_files += 1
        
        # Copy untranslated files
        print(f"\n📋 Copying untranslated tutorial files...")
        for bin_file in tutorial_bin_dir.glob("*.bin"):
            output_file = output_dir / bin_file.name
            if not output_file.exists():
                shutil.copy2(bin_file, output_file)
                print(f"   📄 Copied: {bin_file.name}")
        
        # Summary
        print(f"\n📊 INJECTION SUMMARY")
        print("=" * 20)
        print(f"Files processed: {processed_files}")
        print(f"Successful injections: {successful_files}")
        print(f"Output directory: {output_dir}")
        
        if successful_files > 0:
            print(f"\n✅ Ready for testing!")
            print(f"   1. Copy translated .bin files to romfs/fe/ directory")
            print(f"   2. Rebuild ROM using makerom")
            print(f"   3. Test in Citra emulator")
        else:
            print(f"\n❌ No files successfully processed")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Inject translated dialogue into RTZ files')
    parser.add_argument('--test', action='store_true', help='Use small test dataset instead of full dataset')
    args = parser.parse_args()
    
    # Paths
    base_dir = Path("files/rtz_extracted/tutorials")
    if args.test:
        translations_file = base_dir / "tutorial_test_translated.csv"
        tutorial_bins = Path("romfs/fe")  # Decompressed .bin files (lowercase)
        output_dir = Path("modified/romfs/fe_test")    # Test translated .bin files
        print("🧪 TESTING MODE - Processing test dataset only")
    else:
        translations_file = base_dir / "tutorial_translated.csv"
        tutorial_bins = Path("romfs/fe")  # Decompressed .bin files (lowercase)
        output_dir = Path("modified/romfs/fe")    # Full translated .bin files
        print("🎯 FULL MODE - Processing complete dataset")
    
    injector = RTZInjector()
    injector.process_all_tutorials(translations_file, tutorial_bins, output_dir)

if __name__ == "__main__":
    main()