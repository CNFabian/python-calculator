import struct
from pathlib import Path

def find_3ds_file():
    """Find .3ds file in current directory"""
    files = list(Path('.').glob('*.3ds'))
    if files:
        return files[0]
    return None

def extract_cci_partitions(file_path):
    """Extract partitions from CCI (3DS) file"""
    print(f"📂 Analyzing CCI file: {file_path}")
    
    with open(file_path, 'rb') as f:
        # Read CCI header
        header = f.read(0x4000)  # CCI header is 16KB
        
        if len(header) < 0x4000:
            print("❌ File too small to be valid CCI")
            return False
        
        # Look for NCCH partitions in the header
        partitions = []
        
        # CCI can have up to 8 partitions, check offsets in header
        for i in range(8):
            offset_pos = 0x120 + (i * 8)
            size_pos = 0x120 + (i * 8) + 4
            
            if offset_pos + 8 <= len(header):
                partition_offset = struct.unpack('<I', header[offset_pos:offset_pos+4])[0]
                partition_size = struct.unpack('<I', header[size_pos:size_pos+4])[0]
                
                if partition_offset > 0 and partition_size > 0:
                    # Convert from media units (0x200 bytes) to actual bytes
                    actual_offset = partition_offset * 0x200
                    actual_size = partition_size * 0x200
                    
                    partitions.append({
                        'index': i,
                        'offset': actual_offset,
                        'size': actual_size
                    })
        
        print(f"📊 Found {len(partitions)} partitions:")
        for p in partitions:
            print(f"   Partition {p['index']}: offset=0x{p['offset']:X}, size={p['size']:,} bytes")
        
        # Extract the first partition (main game)
        if partitions:
            main_partition = partitions[0]
            print(f"\n🎯 Extracting main partition (index {main_partition['index']})...")
            
            f.seek(main_partition['offset'])
            partition_data = f.read(main_partition['size'])
            
            if len(partition_data) < main_partition['size']:
                print(f"⚠️ Warning: Expected {main_partition['size']} bytes, got {len(partition_data)}")
            
            # Check if this is NCCH
            if partition_data[:4] == b'NCCH':
                print("✅ Found NCCH partition!")
                return extract_ncch_from_data(partition_data)
            else:
                print(f"❌ Partition doesn't start with NCCH: {partition_data[:8]}")
                return False
        else:
            print("❌ No valid partitions found")
            return False

def extract_ncch_from_data(ncch_data):
    """Extract components from NCCH data"""
    print("🔍 Extracting NCCH components...")
    
    if len(ncch_data) < 0x200:
        print("❌ NCCH data too small")
        return False
    
    # Parse NCCH header
    header = ncch_data[:0x200]
    
    # Get component info from header
    content_size = struct.unpack('<I', header[0x04:0x08])[0] * 0x200
    exheader_size = struct.unpack('<I', header[0x180:0x184])[0]
    exefs_offset = struct.unpack('<I', header[0x1A0:0x1A4])[0] * 0x200
    exefs_size = struct.unpack('<I', header[0x1A4:0x1A8])[0] * 0x200
    romfs_offset = struct.unpack('<I', header[0x1B0:0x1B4])[0] * 0x200
    romfs_size = struct.unpack('<I', header[0x1B4:0x1B8])[0] * 0x200
    
    print(f"📊 NCCH Structure:")
    print(f"   Content size: {content_size:,} bytes")
    print(f"   ExHeader size: {exheader_size} bytes")
    print(f"   ExeFS offset: 0x{exefs_offset:X}, size: {exefs_size:,} bytes")
    print(f"   RomFS offset: 0x{romfs_offset:X}, size: {romfs_size:,} bytes")
    
    success = True
    
    # Extract ExHeader
    if exheader_size > 0:
        if len(ncch_data) >= 0x200 + exheader_size:
            exheader_data = ncch_data[0x200:0x200 + exheader_size]
            Path('exheader.bin').write_bytes(exheader_data)
            print(f"✅ Extracted exheader.bin ({len(exheader_data)} bytes)")
        else:
            print("❌ Not enough data for ExHeader")
            success = False
    
    # Extract ExeFS (contains code.bin)
    if exefs_offset > 0 and exefs_size > 0:
        if len(ncch_data) >= exefs_offset + exefs_size:
            exefs_data = ncch_data[exefs_offset:exefs_offset + exefs_size]
            Path('exefs.bin').write_bytes(exefs_data)
            print(f"✅ Extracted exefs.bin ({len(exefs_data)} bytes)")
            
            # Extract code.bin from ExeFS
            extract_code_from_exefs(exefs_data)
        else:
            print("❌ Not enough data for ExeFS")
            success = False
    
    # Extract RomFS
    if romfs_offset > 0 and romfs_size > 0:
        if len(ncch_data) >= romfs_offset + romfs_size:
            romfs_data = ncch_data[romfs_offset:romfs_offset + romfs_size]
            Path('romfs.bin').write_bytes(romfs_data)
            print(f"✅ Extracted romfs.bin ({len(romfs_data)} bytes)")
        else:
            print("❌ Not enough data for RomFS")
            success = False
    
    return success

def extract_code_from_exefs(exefs_data):
    """Extract code.bin from ExeFS"""
    print("🔍 Extracting code.bin from ExeFS...")
    
    if len(exefs_data) < 0x200:
        print("❌ ExeFS too small")
        return
    
    # ExeFS has up to 10 file entries in the header
    for i in range(10):
        entry_offset = i * 16
        if entry_offset + 16 > 0x200:
            break
        
        filename_bytes = exefs_data[entry_offset:entry_offset + 8]
        filename = filename_bytes.rstrip(b'\x00').decode('ascii', errors='ignore')
        
        if not filename:
            continue
        
        file_offset = struct.unpack('<I', exefs_data[entry_offset + 8:entry_offset + 12])[0]
        file_size = struct.unpack('<I', exefs_data[entry_offset + 12:entry_offset + 16])[0]
        
        print(f"📄 ExeFS file {i}: {filename}")
        print(f"   Offset: 0x{file_offset:X}, Size: {file_size:,} bytes")
        
        if filename.lower() == 'code' or filename.lower() == '.code':
            # Found code.bin!
            code_start = 0x200 + file_offset
            if code_start + file_size <= len(exefs_data):
                code_data = exefs_data[code_start:code_start + file_size]
                
                # Handle compression
                if len(code_data) >= 4 and code_data[:4] == b'Yaz0':
                    print("🗜️ Code.bin is Yaz0 compressed")
                    # For now, save compressed version - we can handle decompression later
                    Path('code_compressed.bin').write_bytes(code_data)
                    print(f"✅ Saved compressed code as code_compressed.bin")
                    
                    # Try simple decompression
                    try:
                        decompressed_size = struct.unpack('>I', code_data[4:8])[0]
                        print(f"🔍 Decompressed size should be: {decompressed_size:,} bytes")
                        # Save info for later processing
                        with open('compression_info.txt', 'w') as f:
                            f.write(f"Original size: {len(code_data)}\n")
                            f.write(f"Decompressed size: {decompressed_size}\n")
                            f.write(f"Compression: Yaz0\n")
                    except:
                        pass
                else:
                    # Uncompressed code.bin
                    Path('code.bin').write_bytes(code_data)
                    print(f"✅ Extracted code.bin ({len(code_data):,} bytes)")
                
                return
    
    print("❌ code.bin not found in ExeFS")

def main():
    """Main extraction process"""
    print("🎮 CF VANGUARD 3DS EXTRACTION (ROBUST)")
    print("=" * 50)
    
    # Find .3ds file
    rom_file = find_3ds_file()
    if not rom_file:
        print("❌ No .3ds file found in current directory")
        return
    
    print(f"📁 Found ROM: {rom_file}")
    
    # Extract CCI partitions
    if extract_cci_partitions(rom_file):
        print("\n✅ EXTRACTION SUCCESSFUL!")
    else:
        print("\n❌ EXTRACTION FAILED!")
    
    print("\n📂 Checking extracted files:")
    for filename in ['exheader.bin', 'code.bin', 'code_compressed.bin', 'romfs.bin']:
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            print(f"   ✅ {filename}: {size:,} bytes")
        else:
            print(f"   ❌ {filename}: Not found")

if __name__ == "__main__":
    main()