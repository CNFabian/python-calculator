#!/usr/bin/env python3
"""
Prepare tutorial data for translation by converting the extracted
all_tutorial_japanese.txt into a structured CSV format
"""
import re
import pandas as pd
from pathlib import Path

def parse_tutorial_file(file_path: Path) -> list:
    """Parse the all_tutorial_japanese.txt file into structured data"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by file sections (=== filename.bin ===)
    file_sections = re.split(r'=== (\w+\.bin) \(\d+ segments\) ===', content)
    
    data = []
    current_file = None
    
    for i, section in enumerate(file_sections):
        if i == 0:
            continue  # Skip the first empty section
            
        if i % 2 == 1:  # Odd indices are filenames
            current_file = section
        else:  # Even indices are content
            if current_file is None:
                continue
                
            # Extract segments with [X] pattern
            segments = re.findall(r'\[(\d+)\]\s*([^\[]*?)(?=\[\d+\]|$)', section, re.DOTALL)
            
            for seg_id_str, text in segments:
                seg_id = int(seg_id_str)
                text = text.strip()
                
                if text:  # Only include non-empty segments
                    data.append({
                        'file': current_file,
                        'segment_id': seg_id,
                        'japanese_text': text
                    })
    
    return data

def main():
    print("🎮 CF Vanguard Tutorial Data Preparation")
    print("=" * 50)
    
    # Input and output paths
    input_file = Path("files/rtz_extracted/tutorials/all_tutorial_japanese.txt")
    output_file = Path("files/rtz_extracted/tutorials/tutorial_for_translation.csv")
    test_output_file = Path("files/rtz_extracted/tutorials/tutorial_test_small.csv")
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    print(f"📂 Reading tutorial data from: {input_file}")
    
    # Parse the file
    data = parse_tutorial_file(input_file)
    
    if not data:
        print("❌ No tutorial data found!")
        return
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Statistics
    file_counts = df['file'].value_counts()
    total_segments = len(df)
    total_files = len(file_counts)
    
    print(f"📊 Parsed {total_segments} segments from {total_files} files")
    print(f"\nTop files by segment count:")
    for file_name, count in file_counts.head(10).items():
        print(f"  {file_name}: {count} segments")
    
    # Show sample data
    print(f"\n📝 Sample data:")
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        text_preview = row['japanese_text'][:50] + "..." if len(row['japanese_text']) > 50 else row['japanese_text']
        print(f"  {row['file']}:{row['segment_id']} - {text_preview}")
    
    # Save full dataset
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n✅ Full dataset saved to: {output_file}")
    
    # Create SMALL TEST dataset (first 20 segments from 2-3 files for testing)
    print(f"\n🧪 Creating small test dataset...")
    test_files = ['tuto_001.bin', 'tuto_002.bin', 'fe0001.bin']  # Pick files with good data
    test_df = df[df['file'].isin(test_files)].head(20).copy()
    
    test_df.to_csv(test_output_file, index=False, encoding='utf-8')
    print(f"✅ TEST dataset saved to: {test_output_file}")
    print(f"   Contains {len(test_df)} segments from {test_df['file'].nunique()} files")
    
    # Show test data preview
    print(f"\n📝 Test dataset preview:")
    for i in range(min(5, len(test_df))):
        row = test_df.iloc[i]
        text_preview = row['japanese_text'][:40] + "..." if len(row['japanese_text']) > 40 else row['japanese_text']
        print(f"  {row['file']}:{row['segment_id']} - {text_preview}")
    
    print(f"\n🔄 Next steps:")
    print(f"  1. Run: python assess_tutorial_quality.py --test")
    print(f"  2. Run: python translate_tutorials.py --test")
    print(f"  3. Run: python inject_rtz_translations.py --test")
    print(f"  4. Once working, remove --test flag for full dataset")

if __name__ == "__main__":
    main()