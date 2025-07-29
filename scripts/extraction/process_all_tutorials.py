#!/usr/bin/env python3
import os
import sys
import json
import csv
from pathlib import Path
import subprocess
from dataclasses import dataclass
from typing import List, Dict

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
        # Run the filtered extraction script
        cmd = [
            sys.executable, 
            "scripts/extract_rtz_filtered.py", 
            str(bin_file), 
            "0x0"
        ]
        
        process_result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if process_result.returncode != 0:
            result.success = False
            result.error = f"Script failed: {process_result.stderr}"
            return result
        
        # Parse the output to extract valid text
        output = process_result.stdout
        
        # Extract segment counts
        for line in output.split('\n'):
            if "Total segments extracted:" in line:
                result.total_segments = int(line.split(':')[1].strip())
            elif "Valid Japanese segments:" in line:
                result.valid_segments = int(line.split(':')[1].strip())
        
        # Extract the Japanese text segments
        in_valid_section = False
        for line in output.split('\n'):
            if "== Valid Japanese Text Segments ==" in line:
                in_valid_section = True
                continue
            elif in_valid_section and line.startswith('['):
                # Extract the quoted text
                if "'" in line:
                    text = line.split("'", 1)[1].rsplit("'", 1)[0]
                    if text.strip():
                        result.japanese_text.append(text)
        
        # Save individual results
        output_file = output_dir / f"{bin_file.stem}_extracted.txt"
        with output_file.open('w', encoding='utf-8') as f:
            f.write(f"=== {bin_file.name} ===\n")
            f.write(f"Total segments: {result.total_segments}\n")
            f.write(f"Valid segments: {result.valid_segments}\n\n")
            f.write("=== Japanese Text ===\n")
            for i, text in enumerate(result.japanese_text, 1):
                f.write(f"[{i}] {text}\n")
        
        print(f"✓ {bin_file.name}: {result.valid_segments} valid segments")
        
    except subprocess.TimeoutExpired:
        result.success = False
        result.error = "Timeout during processing"
    except Exception as e:
        result.success = False
        result.error = str(e)
    
    return result

def create_summary_report(results: List[TutorialResult], output_dir: Path):
    """Create summary files of all extracted content"""
    
    # CSV summary
    csv_file = output_dir / "tutorial_summary.csv"
    with csv_file.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'total_segments', 'valid_segments', 'success', 'error'])
        for result in results:
            writer.writerow([
                result.filename,
                result.total_segments,
                result.valid_segments,
                result.success,
                result.error
            ])
    
    # All Japanese text in one file
    all_text_file = output_dir / "all_tutorial_text.txt"
    with all_text_file.open('w', encoding='utf-8') as f:
        f.write("=== CF VANGUARD STRIDE TO VICTORY - TUTORIAL TEXT ===\n\n")
        
        total_valid = 0
        for result in results:
            if not result.success:
                continue
                
            f.write(f"=== {result.filename} ===\n")
            f.write(f"Segments: {result.valid_segments}\n\n")
            
            for i, text in enumerate(result.japanese_text, 1):
                f.write(f"[{i}] {text}\n")
            f.write("\n" + "="*50 + "\n\n")
            
            total_valid += result.valid_segments
        
        f.write(f"TOTAL VALID TEXT SEGMENTS: {total_valid}\n")
    
    # JSON for programmatic use
    json_file = output_dir / "tutorial_data.json"
    with json_file.open('w', encoding='utf-8') as f:
        json.dump([
            {
                'filename': r.filename,
                'total_segments': r.total_segments,
                'valid_segments': r.valid_segments,
                'japanese_text': r.japanese_text,
                'success': r.success,
                'error': r.error
            }
            for r in results
        ], f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Summary report saved to {output_dir}")
    print(f"  - CSV: {csv_file.name}")
    print(f"  - All text: {all_text_file.name}")
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
        return
    
    tutorial_files.sort()
    print(f"Found {len(tutorial_files)} tutorial files to process")
    
    # Process each file
    results = []
    for bin_file in tutorial_files:
        print(f"Processing {bin_file.name}...", end=" ")
        result = process_single_tutorial(bin_file, output_dir)
        results.append(result)
        
        if not result.success:
            print(f"✗ ERROR: {result.error}")
    
    # Create summary
    create_summary_report(results, output_dir)
    
    # Print final stats
    successful = [r for r in results if r.success]
    total_valid = sum(r.valid_segments for r in successful)
    
    print(f"\n=== PROCESSING COMPLETE ===")
    print(f"Files processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Total valid text segments: {total_valid}")
    
    if total_valid > 0:
        print(f"\nNext steps:")
        print(f"1. Review: files/rtz_extracted/tutorials/all_tutorial_text.txt")
        print(f"2. Translate: Use the filtered extractor with 'translate' flag")
        print(f"3. Test: Rebuild ROM and test in emulator")

if __name__ == "__main__":
    main()