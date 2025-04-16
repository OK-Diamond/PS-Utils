'''
Combines multiple files.
'''
import os
import argparse
import fnmatch
from datetime import datetime

# pylint: disable=R0913
def combine_code_files(root_dir, output_file, exclude_patterns=None, include_patterns=None,exclude_dirs=None, include_dirs=None, max_file_size_mb=10):
    '''
    Combines code files from a directory into a single file.
    '''
    exclude_patterns = exclude_patterns or [] # Cool new tech I've learned about or with non-bools
    include_patterns = include_patterns or []
    exclude_dirs = exclude_dirs or []
    max_file_size_bytes = max_file_size_mb * 1024 * 1024

    # Normalize directory paths
    if include_dirs:
        include_dirs = [os.path.normpath(os.path.join(root_dir, d)) for d in include_dirs]

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Write header
        outfile.write(f"# COMBINED CODE FILES FROM {os.path.abspath(root_dir)}\n")
        outfile.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        file_count = 0
        skipped_count = 0

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Filter directories
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

            # Skip if not in included directories
            if include_dirs and not any(dirpath.startswith(d) for d in include_dirs):
                continue

            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, root_dir)

                # Check if file should be excluded based on patterns
                if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns):
                    skipped_count += 1
                    continue

                # Check if file should be included based on patterns
                if include_patterns and not any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns):
                    skipped_count += 1
                    continue

                # Check file size
                try:
                    file_size = os.path.getsize(filepath)
                    if file_size > max_file_size_bytes:
                        print(f"Skipping large file: {rel_path} ({file_size / 1024 / 1024:.2f} MB)")
                        skipped_count += 1
                        continue

                    # Try to read the file
                    try:
                        with open(filepath, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                    except UnicodeDecodeError:
                        try:
                            # Try with different encoding
                            with open(filepath, 'r', encoding='latin-1') as infile:
                                content = infile.read()
                        except UnicodeDecodeError:
                            print(f"Skipping binary or unreadable file: {rel_path}")
                            skipped_count += 1
                            continue

                    # Write file header
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"# FILE: {rel_path}\n")
                    outfile.write(f"{'='*80}\n\n")

                    # Write file content
                    outfile.write(content)
                    outfile.write("\n\n")
                    file_count += 1

                except (OSError, IOError) as e:
                    print(f"Error processing {rel_path}: {str(e)}")
                    skipped_count += 1

        # Write summary
        outfile.write(f"\n{'='*80}\n")
        outfile.write(f"# SUMMARY: Combined {file_count} files (skipped {skipped_count})\n")
        outfile.write(f"{'='*80}\n")

    print(f"Combined {file_count} files into {output_file} (skipped {skipped_count})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine code files into a single file")
    parser.add_argument("root_dir", help="Root directory to search for code files")
    parser.add_argument("output_file", help="Output file path")
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[
            "*.pyc",
            "*.pyo",
            "*.so",
            "*.o",
            "*.a",
            "*.lib",
            "*.dll",
            "*.exe",
            "*.bin",
            "*.dat",
            "*.db",
            "*.sqlite", 
            "*.sqlite3",
            "*.log",
            "*.jpg",
            "*.jpeg",
            "*.png",
            "*.gif",
            "*.pdf",
            ".env"
        ],
        help="File patterns to exclude."
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=[],
        help="File patterns to include (e.g., '*.py' '*.js'). Skipped if left empty."
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=[
            ".git",
            ".svn",
            "__pycache__",
            "node_modules", 
            "venv", 
            "env", 
            ".venv",
            ".env",
            "bin",
            "obj",
            "build",
            "dist"
        ],
        help="Directories to exclude."
    )
    parser.add_argument(
        "--include-dirs",
        nargs="*",
        default=[],
        help="Only include these directories (relative to root). Skipped if left empty."
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=10,
        help="Skip files larger than this size in MB"
    )

    args = parser.parse_args()

    combine_code_files(
        args.root_dir,
        args.output_file,
        exclude_patterns=args.exclude,
        include_patterns=args.include,
        exclude_dirs=args.exclude_dirs,
        include_dirs=args.include_dirs,
        max_file_size_mb=args.max_size
    )
