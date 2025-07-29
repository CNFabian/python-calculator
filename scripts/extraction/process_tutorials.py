#!/usr/bin/env python3
"""
CF Vanguard Stride to Victory - Tutorial Text Extraction
Processes all tutorial .bin files and extracts clean Japanese text
"""

import os
import sys
import json
import csv
from pathlib import Path
import subprocess
from dataclasses import dataclass
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

@dataclass
class TutorialResult:
    filename: str
    total_segments: int
    valid_segments: int
    japanese_text: List[str]
    success: bool = True
    error: str = ""

def process_single_tutorial(bin_file: Path, output_dir: Path) -> TutorialResult:
    """Process a single tutorial file and extract Japanese text"""
    result = TutorialResult(
        filename=bin_file.name,
        total_segments=0,
        valid_segments=0,
        japanese_text=[]
    )
    
    try:
        # Use the filtered extraction script
        script_path = PROJECT_ROOT / "scripts/extraction/extract_rtz_filtered.py"
        cmd = [
            sys.executable, 
            str(script_path), 
            str(bin_file), 
            "0x0"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        process_result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60,
            cwd=PROJECT_ROOT
        )
        
        if process_result.returncode != 0:
            result.success = False
            result.error = f"Script failed (code {process_result.returncode}): {process_result.stderr}"
            return result
        
        # Parse the output to extract valid text
        output = process_result.stdout
        
        # Extract segment counts
        for line in output.split('\n'):
            if "Total segments extracted:" in line:
                try:
                    result.total_segments = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif "Valid Japanese segments:" in line:
                try:
                    result.valid_segments = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
        
        # Extract the Japanese text segments
        in_valid_section = False
        for line in output.split('\n'):
            if "== Valid Japanese Text Segments ==" in line:
                in_valid_section = True
                continue
            elif in_valid_section and line.startswith('['):
                # Extract the quoted text
                try:
                    # Handle both single and double quotes
                    if "'" in line:
                        parts = line.split("'")
                        if len(parts) >= 3:
                            text = parts[1]
                            if text.strip():
                                result.japanese_text.append(text)
                    elif '"' in line:
                        parts = line.split('"')
                        if len(parts) >= 3:
                            text = parts[1]
                            if text.strip():
                                result.japanese_text.append(text)
                except Exception as e:
                    print(f"Warning: Could not parse line: {line[:50]}... ({e})")
        
        # Save individual results
        output_file = output_dir / f"{bin_file.stem}_extracted.txt"
        with output_file.open('w', encoding='utf-8') as f:
            f.write(f"=== {bin_file.name} ===\n")
            f.write(f"Total segments: {result.total_segments}\n")
            f.write(f"Valid segments: {result.valid_segments}\n\n")
            
            if result.success:
                f.write("=== Japanese Text ===\n")
                for i, text in enumerate(result.japanese_text, 1):
                    f.write(f"[{i}] {text}\n")
            else:
                f.write(f"ERROR: {result.error}\n")
            
            f.write("\n=== Raw Output ===\n")
            f.write(output)
        
        print(f"✓ {bin_file.name}: {result.valid_segments} valid segments")
        
    except subprocess.TimeoutExpired:
        result.success = False
        result.error = "Timeout during processing (60s)"
        print(f"✗ {bin_file.name}: Timeout")
    except Exception as e:
        result.success = False
        result.error = str(e)
        print(f"✗ {bin_file.name}: {e}")
    
    return result

def create_summary_report(results: List[TutorialResult], output_dir: Path):
    """Create summary files of all extracted content"""
    
    # CSV summary
    csv_file = output_dir / "tutorial_summary.csv"
    with csv_file.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'total_segments', 'valid_segments', 'text_count', 'success', 'error'])
        for result in results:
            writer.writerow([
                result.filename,
                result.total_segments,
                result.valid_segments,
                len(result.japanese_text),
                result.success,
                result.error
            ])
    
    # All Japanese text in one file for translation
    all_text_file = output_dir / "all_tutorial_japanese.txt"
    translation_csv = output_dir / "tutorial_for_translation.csv"
    
    all_segments = []
    with all_text_file.open('w', encoding='utf-8') as f, \
         translation_csv.open('w', newline='', encoding='utf-8') as csv_f:
        
        csv_writer = csv.writer(csv_f)
        csv_writer.writerow(['file', 'segment_id', 'japanese_text', 'english_text'])
        
        f.write("=== CF VANGUARD STRIDE TO VICTORY - TUTORIAL TEXT ===\n")
        f.write("=== EXTRACTED JAPANESE DIALOGUE ===\n\n")
        
        total_valid = 0
        segment_counter = 1
        
        for result in results:
            if not result.success or not result.japanese_text:
                continue
                
            f.write(f"=== {result.filename} ({len(result.japanese_text)} segments) ===\n")
            
            for i, text in enumerate(result.japanese_text, 1):
                # Clean up the text for better readability
                clean_text = text.replace('\\n', '\n').replace('\\x00', '').strip()
                if clean_text:
                    f.write(f"[{segment_counter}] {clean_text}\n")
                    csv_writer.writerow([result.filename, segment_counter, clean_text, ''])
                    all_segments.append({
                        'file': result.filename,
                        'segment_id': segment_counter,
                        'text': clean_text
                    })
                    segment_counter += 1
            
            f.write("\n" + "="*60 + "\n\n")
            total_valid += len(result.japanese_text)
        
        f.write(f"TOTAL DIALOGUE SEGMENTS: {total_valid}\n")
    
    # JSON for programmatic use
    json_file = output_dir / "tutorial_data.json"
    with json_file.open('w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_files': len(results),
                'successful_files': len([r for r in results if r.success]),
                'total_segments': sum(len(r.japanese_text) for r in results if r.success),
                'extraction_date': str(Path().cwd())
            },
            'files': [
                {
                    'filename': r.filename,
                    'total_segments': r.total_segments,
                    'valid_segments': r.valid_segments,
                    'japanese_text': r.japanese_text,
                    'success': r.success,
                    'error': r.error
                }
                for r in results
            ],
            'all_segments': all_segments
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Summary report saved to {output_dir}")
    print(f"  - CSV summary: {csv_file.name}")
    print(f"  - All Japanese text: {all_text_file.name}")
    print(f"  - Translation template: {translation_csv.name}")
    print(f"  - JSON data: {json_file.name}")

def main():
    # Setup directories
    romfs_fe = Path("RomFS/fe")
    output_dir = Path("files/rtz_extracted/tutorials")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all tutorial files
    tutorial_files = list(romfs_fe.glob("*.bin"))
    if not tutorial_files:
        print("No .bin files found in RomFS/fe/")
        print("Current directory:", Path.cwd())
        print("RomFS/fe exists:", romfs_fe.exists())
        return
    
    tutorial_files.sort()
    print(f"Found {len(tutorial_files)} tutorial files to process")
    print("Tutorial files:", [f.name for f in tutorial_files[:5]], "..." if len(tutorial_files) > 5 else "")
    
    # Process each file
    results = []
    for i, bin_file in enumerate(tutorial_files, 1):
        print(f"\n[{i}/{len(tutorial_files)}] Processing {bin_file.name}...", end=" ")
        result = process_single_tutorial(bin_file, output_dir)
        results.append(result)
    
    # Create summary
    create_summary_report(results, output_dir)
    
    # Print final stats
    successful = [r for r in results if r.success]
    total_valid = sum(len(r.japanese_text) for r in successful)
    
    print(f"\n=== PROCESSING COMPLETE ===")
    print(f"Files processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Total Japanese dialogue segments: {total_valid}")
    
    if total_valid > 0:
        print(f"\n=== NEXT STEPS ===")
        print(f"1. Review: files/rtz_extracted/tutorials/all_tutorial_japanese.txt")
        print(f"2. Translate: files/rtz_extracted/tutorials/tutorial_for_translation.csv")
        print(f"3. Use LibreTranslate or improve translations manually")
        print(f"4. Test: Inject translations and rebuild ROM")
    else:
        print("\n⚠ No Japanese text extracted. Check the extraction script.")

if __name__ == "__main__":
    main()