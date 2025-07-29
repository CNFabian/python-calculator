from pathlib import Path
import gzip

def analyze_romfs_structure():
    """Analyze the dumped RomFS structure"""
    
    romfs_path = Path('RomFS')
    if not romfs_path.exists():
        print("❌ RomFS folder not found")
        return False
    
    print("🎮 ROMFS CONTENT ANALYSIS")
    print("=" * 50)
    
    # Find all RTZ files
    rtz_files = list(romfs_path.rglob('*.rtz'))
    
    print(f"📊 Found {len(rtz_files)} RTZ files:")
    
    # Categorize RTZ files
    categories = {
        'story': [],
        'tutorial': [],
        'fight': [], 
        'ui': [],
        'other': []
    }
    
    for rtz_file in rtz_files:
        relative_path = rtz_file.relative_to(romfs_path)
        
        # Categorize based on path and filename
        if 'script' in str(relative_path).lower() or 'ev_' in rtz_file.name.lower():
            categories['story'].append(relative_path)
        elif 'tuto' in rtz_file.name.lower():
            categories['tutorial'].append(relative_path)
        elif 'fight' in str(relative_path).lower() or 'battle' in str(relative_path).lower():
            categories['fight'].append(relative_path)
        elif any(ui_term in str(relative_path).lower() for ui_term in ['menu', 'ui', 'interface']):
            categories['ui'].append(relative_path)
        else:
            categories['other'].append(relative_path)
    
    # Display categorized results
    for category, files in categories.items():
        if files:
            print(f"\n📁 {category.upper()} FILES ({len(files)}):")
            for f in files[:5]:  # Show first 5
                print(f"   {f}")
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more")
    
    return rtz_files

def test_rtz_decompression(rtz_files):
    """Test RTZ file decompression"""
    
    print(f"\n🗜️ TESTING RTZ DECOMPRESSION:")
    print("-" * 30)
    
    for i, rtz_file in enumerate(rtz_files[:3]):  # Test first 3
        print(f"Testing {rtz_file.name}...")
        
        try:
            # RTZ files are gzip compressed
            with gzip.open(rtz_file, 'rb') as f:
                decompressed = f.read()
            
            print(f"   ✅ Decompressed: {len(decompressed):,} bytes")
            
            # Look for text content
            text_sample = decompressed[:200]
            if any(0x3040 <= b <= 0x309F or 0x30A0 <= b <= 0x30FF or 0x4E00 <= b <= 0x9FAF for b in text_sample):
                print(f"   📝 Contains Japanese text")
            else:
                print(f"   📄 Binary/structured data")
                
        except Exception as e:
            print(f"   ❌ Decompression failed: {e}")
        
        if i >= 2:  # Only test first 3
            break

def identify_high_value_targets(rtz_files):
    """Identify the most valuable RTZ files for translation"""
    
    print(f"\n🎯 HIGH-VALUE TRANSLATION TARGETS:")
    print("-" * 40)
    
    priorities = {
        'CRITICAL': [],
        'HIGH': [],
        'MEDIUM': [],
        'LOW': []
    }
    
    for rtz_file in rtz_files:
        filename = rtz_file.name.lower()
        path = str(rtz_file).lower()
        
        # Prioritize based on content type
        if any(pattern in filename for pattern in ['tuto', 'tutorial']):
            priorities['CRITICAL'].append((rtz_file, "Tutorial - essential for new players"))
        elif any(pattern in filename for pattern in ['ev_', 'script']):
            priorities['HIGH'].append((rtz_file, "Story dialogue - main content"))
        elif any(pattern in filename for pattern in ['fight', 'battle']):
            priorities['HIGH'].append((rtz_file, "Battle interface - core gameplay"))
        elif any(pattern in filename for pattern in ['menu', 'title']):
            priorities['MEDIUM'].append((rtz_file, "UI elements - navigation"))
        else:
            priorities['LOW'].append((rtz_file, "Other content"))
    
    for priority, files in priorities.items():
        if files:
            print(f"\n{priority} PRIORITY ({len(files)} files):")
            for rtz_file, description in files[:3]:  # Show first 3
                rel_path = rtz_file.relative_to(Path('RomFS'))
                print(f"   📄 {rel_path}")
                print(f"      → {description}")

def main():
    """Main RomFS analysis"""
    
    rtz_files = analyze_romfs_structure()
    
    if rtz_files:
        test_rtz_decompression(rtz_files)
        identify_high_value_targets(rtz_files)
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Process tutorial RTZ files first (easiest wins)")
        print(f"   2. Work on story dialogue (biggest impact)")
        print(f"   3. Tackle battle interface (gameplay critical)")
        
        print(f"\n💡 RTZ files contain MORE text than code.bin!")
        print(f"   This is where the real translation work happens.")
    
    return rtz_files

if __name__ == "__main__":
    main()