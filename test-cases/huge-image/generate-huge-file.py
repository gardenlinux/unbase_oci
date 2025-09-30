import os
import argparse

def generate_huge_file(filename, size_bytes, chunk_size=1024*1024):
    with open(filename, 'wb') as f:
        remaining = size_bytes
        while remaining > 0:
            write_size = min(chunk_size, remaining)
            f.write(os.urandom(write_size))
            remaining -= write_size

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a large file with random binary content.")
    parser.add_argument("filename", help="Output file name")
    parser.add_argument("size", type=int, help="Size of the file in bytes")
    args = parser.parse_args()

    generate_huge_file(args.filename, args.size)
