import gzip
import struct
from pathlib import Path
import argparse

def decompress_single_rtz(rtz_path, output_dir=None):
    """Decompress a single RTZ file"""
    
    if not rtz_path.exists():
        print(f"❌ File not found: {rtz_path}")
        return False
    
    with open(rtz_path, 'rb') as f:
        # Read the 4-byte size header
        size_data = f.read(4)
        if len(size_data) < 4:
            print(f"❌ File too small: {rtz_path}")
            return False
        
        uncompressed_size = struct.unpack('<I', size_data)[0]
        
        # Read the rest as gzip data
        gzip_data = f.read()
        
        print(f"📄 {rtz_path.name}")
        print(f"   Expected size: {uncompressed_size:,} bytes")
        print(f"   Compressed: {len(gzip_data):,} bytes")
        
        try:
            # Decompress the gzip data
            decompressed = gzip.decompress(gzip_data)
            
            if len(decompressed) != uncompressed_size:
                print(f"   ⚠️ Size mismatch: got {len(decompressed)}, expected {uncompressed_size}")
            
            # Save decompressed file
            if output_dir:
                output_path = output_dir / f"{rtz_path.stem}.bin"
            else:
                output_path = rtz_path.parent / f"{rtz_path.stem}.bin"
            
            output_path.write_bytes(decompressed)
            print(f"   ✅ Decompressed to: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"   ❌ Decompression failed: {e}")
            return False

def decompress_rtz_directory(rtz_dir, output_dir=None):
    """Decompress all RTZ files in a directory"""
    
    rtz_dir = Path(rtz_dir)
    if not rtz_dir.exists():
        print(f"❌ Directory not found: {rtz_dir}")
        return []
    
    # Create output directory
    if output_dir is None:
        output_dir = rtz_dir.parent / f"{rtz_dir.name}_decompressed"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Find all RTZ files
    rtz_files = list(rtz_dir.rglob('*.rtz'))
    
    print(f"🗜️ DECOMPRESSING RTZ FILES")
    print(f"   Source: {rtz_dir}")
    print(f"   Output: {output_dir}")
    print(f"   Files: {len(rtz_files)}")
    print("=" * 50)
    
    successful = []
    failed = []
    
    for rtz_file in rtz_files:
        # Maintain directory structure
        relative_path = rtz_file.relative_to(rtz_dir)
        file_output_dir = output_dir / relative_path.parent
        file_output_dir.mkdir(parents=True, exist_ok=True)
        
        result = decompress_single_rtz(rtz_file, file_output_dir)
        if result:
            successful.append(result)
        else:
            failed.append(rtz_file)
    
    print(f"\n📊 DECOMPRESSION RESULTS:")
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(failed)}")
    
    if failed:
        print(f"\n❌ FAILED FILES:")
        for f in failed[:5]:  # Show first 5 failures
            print(f"   {f}")
    
    return successful

def main():
    """Main decompression function"""
    
    parser = argparse.ArgumentParser(description='Decompress RTZ files')
    parser.add_argument('input', help='RTZ file or directory to decompress')
    parser.add_argument('-o', '--output', help='Output directory')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        decompress_single_rtz(input_path, Path(args.output) if args.output else None)
    elif input_path.is_dir():
        decompress_rtz_directory(input_path, args.output)
    else:
        print(f"❌ Invalid input: {input_path}")

if __name__ == "__main__":
    main()