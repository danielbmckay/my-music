#!/usr/bin/env python3
"""Manage, organize, and search audio samples.

Usage:
    python sample_manager.py scan <directory>              # Scan and catalog samples
    python sample_manager.py search <query>                # Search catalog by name
    python sample_manager.py duplicates <directory>        # Find duplicate audio files
    python sample_manager.py unused <project.als> <dir>    # Find samples not used in ALS
    python sample_manager.py catalog <directory> -o out.json  # Export full catalog
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict

AUDIO_EXTENSIONS = {'.aif', '.aiff', '.wav', '.mp3', '.flac', '.ogg', '.m4a', '.alc'}
IGNORE_EXTENSIONS = {'.asd', '.ds_store'}


def hash_file(filepath: str, chunk_size: int = 8192) -> str:
    """Compute MD5 hash of a file for duplicate detection."""
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def scan_directory(directory: str) -> list:
    """Scan a directory recursively for audio files."""
    path = Path(directory)
    samples = []

    for f in sorted(path.rglob('*')):
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS:
            samples.append({
                'name': f.stem,
                'filename': f.name,
                'path': str(f),
                'extension': f.suffix.lower(),
                'size_kb': round(f.stat().st_size / 1024, 1),
                'parent': f.parent.name,
            })

    return samples


def find_duplicates(directory: str) -> dict:
    """Find duplicate audio files by content hash."""
    path = Path(directory)
    hashes = defaultdict(list)

    files = [f for f in path.rglob('*') if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS]
    print(f"Hashing {len(files)} files...")

    for f in files:
        file_hash = hash_file(str(f))
        hashes[file_hash].append(str(f))

    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    return duplicates


def find_unused_samples(als_path: str, sample_dir: str) -> list:
    """Find samples in a directory that aren't referenced in an ALS file."""
    import gzip
    import xml.etree.ElementTree as ET

    with gzip.open(als_path, 'rb') as f:
        xml_data = f.read()
    root = ET.fromstring(xml_data)

    # Extract all file references from the ALS
    referenced = set()
    for file_ref in root.findall('.//FileRef'):
        name = file_ref.find('Name')
        if name is not None:
            referenced.add(name.get('Value', '').lower())

    for rel_path in root.findall('.//RelativePath'):
        for dir_el in rel_path.findall('RelativePathElement'):
            val = dir_el.get('Dir', '')
            if val:
                referenced.add(val.lower())

    # Find samples not in the reference list
    samples = scan_directory(sample_dir)
    unused = [s for s in samples if s['filename'].lower() not in referenced]
    return unused


def search_catalog(directory: str, query: str) -> list:
    """Search for samples matching a query string."""
    samples = scan_directory(directory)
    query_lower = query.lower()
    return [s for s in samples if query_lower in s['name'].lower() or query_lower in s['parent'].lower()]


def print_scan_results(samples: list):
    """Pretty-print scan results."""
    print(f"\nFound {len(samples)} audio files:\n")

    by_type = defaultdict(list)
    for s in samples:
        by_type[s['extension']].append(s)

    for ext, files in sorted(by_type.items()):
        total_mb = sum(f['size_kb'] for f in files) / 1024
        print(f"  {ext}: {len(files)} files ({total_mb:.1f} MB)")

    print(f"\n  Total: {len(samples)} files "
          f"({sum(s['size_kb'] for s in samples) / 1024:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description='Sample management tools')
    subparsers = parser.add_subparsers(dest='command')

    scan_p = subparsers.add_parser('scan', help='Scan and catalog samples')
    scan_p.add_argument('directory', help='Directory to scan')

    search_p = subparsers.add_parser('search', help='Search samples by name')
    search_p.add_argument('query', help='Search query')
    search_p.add_argument('--dir', default='.', help='Directory to search')

    dup_p = subparsers.add_parser('duplicates', help='Find duplicate files')
    dup_p.add_argument('directory', help='Directory to check')

    unused_p = subparsers.add_parser('unused', help='Find unused samples')
    unused_p.add_argument('als_file', help='ALS file to check against')
    unused_p.add_argument('sample_dir', help='Sample directory')

    catalog_p = subparsers.add_parser('catalog', help='Export full catalog')
    catalog_p.add_argument('directory', help='Directory to catalog')
    catalog_p.add_argument('-o', '--output', required=True, help='Output JSON file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'scan':
        samples = scan_directory(args.directory)
        print_scan_results(samples)

    elif args.command == 'search':
        results = search_catalog(args.dir, args.query)
        if results:
            print(f"\nFound {len(results)} matches for '{args.query}':\n")
            for s in results:
                print(f"  {s['filename']}  ({s['size_kb']} KB)  [{s['parent']}]")
        else:
            print(f"No samples matching '{args.query}'")

    elif args.command == 'duplicates':
        dupes = find_duplicates(args.directory)
        if dupes:
            print(f"\nFound {len(dupes)} sets of duplicates:\n")
            for h, paths in dupes.items():
                print(f"  Hash: {h[:12]}...")
                for p in paths:
                    print(f"    - {p}")
                print()
        else:
            print("No duplicates found.")

    elif args.command == 'unused':
        unused = find_unused_samples(args.als_file, args.sample_dir)
        if unused:
            print(f"\n{len(unused)} unused samples:\n")
            for s in unused:
                print(f"  {s['filename']}  ({s['size_kb']} KB)")
        else:
            print("All samples are referenced in the project.")

    elif args.command == 'catalog':
        samples = scan_directory(args.directory)
        Path(args.output).write_text(json.dumps(samples, indent=2))
        print(f"Catalog saved: {len(samples)} samples -> {args.output}")


if __name__ == '__main__':
    main()
