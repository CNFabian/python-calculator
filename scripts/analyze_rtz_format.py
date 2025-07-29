from pathlib import Path
import struct

def analyze_rtz_headers():
    """Analyze RTZ file headers to understand the format"""
    
    print("🔍 RTZ FILE FORMAT ANALYSIS")
    print("=" * 50)
    
    # Get a few RTZ files from different categories
    test_files = []
    
    categories = [
        ('Tutorial', 'fe/tuto_007.rtz'),
        ('Fight', 'fight/send_comment.rtz'), 
        ('Script', 'script/EV_CR_05.rtz'),
        ('System', 'system/pl_menu.rtz')
    ]
    
    for category, path in categories:
        full_path = Path('RomFS') / path
        if full_path.exists():
            test_files.append((category, full_path))
    
    for category, rtz_file in test_files:
        print(f"\n📄 {category}: {rtz_file.name}")
        analyze_single_rtz(rtz_file)

def analyze_single_rtz(rtz_path):
    """Analyze a single RTZ file structure"""
    
    with open(rtz_path, 'rb') as f:
        # Read first 64 bytes for analysis
        header = f.read(64)
        file_size = rtz_path.stat().st_size
        
        print(f"   📊 File size: {file_size:,} bytes")
        print(f"   🔢 First 16 bytes: {header[:16].hex().upper()}")
        print(f"   📝 First 4 bytes as uint32: {struct.unpack('<I', header[:4])[0] if len(header) >= 4 else 'N/A'}")
        
        # Check for common compression signatures
        signatures = {
            b'Yaz0': 'Yaz0 compression',
            b'LZ77': 'LZ77 compression', 
            b'\x78\x9c': 'zlib compression',
            b'\x1f\x8b': 'gzip compression',
            b'LZSS': 'LZSS compression'
        }
        
        found_compression = None
        for sig, name in signatures.items():
            if header.startswith(sig):
                found_compression = name
                break
        
        if found_compression:
            print(f"   ✅ Compression: {found_compression}")
        else:
            print(f"   ❓ Unknown format - not standard compression")
        
        # Look for text patterns (UTF-16 Japanese characters)
        text_positions = []
        for i in range(0, min(len(header) - 1, 60), 2):
            try:
                char_bytes = header[i:i+2]
                if len(char_bytes) == 2:
                    char_code = struct.unpack('<H', char_bytes)[0]
                    # Check if it's in Japanese Unicode ranges
                    if (0x3040 <= char_code <= 0x309F or  # Hiragana
                        0x30A0 <= char_code <= 0x30FF or  # Katakana
                        0x4E00 <= char_code <= 0x9FAF):   # Kanji
                        text_positions.append(i)
            except:
                pass
        
        if text_positions:
            print(f"   📝 Possible text at offsets: {text_positions[:5]}")
        else:
            print(f"   📄 No obvious text in header")
        
        # Try to find patterns that might indicate structure
        if len(header) >= 8:
            # Check if first 4 bytes might be uncompressed size
            potential_size = struct.unpack('<I', header[:4])[0]
            if potential_size > file_size and potential_size < file_size * 100:
                print(f"   🔍 Potential uncompressed size: {potential_size:,} bytes")

def try_alternative_decompression():
    """Try alternative decompression methods"""
    
    print(f"\n🔧 TESTING ALTERNATIVE DECOMPRESSION METHODS")
    print("-" * 50)
    
    # Get a small tutorial file to test
    test_file = Path('RomFS/fe/tuto_007.rtz')
    if not test_file.exists():
        print("❌ Test file not found")
        return
    
    with open(test_file, 'rb') as f:
        data = f.read()
    
    print(f"📄 Testing with: {test_file.name} ({len(data)} bytes)")
    
    # Method 1: Try treating as raw binary and looking for text
    print(f"\n1. Scanning for raw UTF-16 text...")
    find_utf16_text(data)
    
    # Method 2: Try custom decompression based on first bytes
    print(f"\n2. Trying custom decompression...")
    try_custom_decompression(data)

def find_utf16_text(data):
    """Scan data for UTF-16 text patterns"""
    
    text_segments = []
    
    for i in range(0, len(data) - 1, 2):
        try:
            # Try to read as UTF-16LE
            if i + 10 <= len(data):  # Need at least 10 bytes for a meaningful string
                text_chunk = data[i:i+20]  # Try 10 characters
                text = text_chunk.decode('utf-16le', errors='ignore')
                
                # Check if it contains Japanese characters
                if (len(text.strip()) >= 2 and 
                    any(0x3040 <= ord(c) <= 0x309F or 0x30A0 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FAF for c in text)):
                    text_segments.append((i, text.strip()))
        except:
            pass
    
    if text_segments:
        print(f"   ✅ Found {len(text_segments)} potential text segments:")
        for offset, text in text_segments[:5]:  # Show first 5
            print(f"      0x{offset:04X}: \"{text[:30]}{'...' if len(text) > 30 else ''}\"")
    else:
        print(f"   ❌ No UTF-16 text found")

def try_custom_decompression(data):
    """Try custom decompression based on file structure"""
    
    if len(data) < 8:
        print("   ❌ File too small for custom decompression")
        return
    
    # Check if first 4 bytes indicate size
    potential_size = struct.unpack('<I', data[:4])[0]
    
    if potential_size > len(data) and potential_size < len(data) * 100:
        print(f"   🔍 First 4 bytes suggest uncompressed size: {potential_size}")
        
        # Try simple decompression starting from offset 4
        try:
            # This is a placeholder - we'd need to reverse engineer the actual format
            compressed_data = data[4:]  # Skip potential size header
            print(f"   📊 Compressed data: {len(compressed_data)} bytes")
            
            # For now, just try to find patterns in the compressed data
            find_utf16_text(compressed_data)
            
        except Exception as e:
            print(f"   ❌ Custom decompression failed: {e}")
    else:
        print(f"   ❌ First 4 bytes don't look like size indicator")

def main():
    """Main RTZ format analysis"""
    
    analyze_rtz_headers()
    try_alternative_decompression()
    
    print(f"\n💡 FINDINGS SUMMARY:")
    print(f"   • RTZ files are NOT gzip compressed")
    print(f"   • They use a custom/proprietary compression format")
    print(f"   • Need to reverse engineer the decompression algorithm")
    print(f"   • Or find existing tools that can handle this format")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Research FuRyu game file formats")
    print(f"   2. Look for existing RTZ decompression tools")
    print(f"   3. Reverse engineer the compression algorithm")
    print(f"   4. Check if project has working RTZ tools")

if __name__ == "__main__":
    main()