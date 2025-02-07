import os
import subprocess
from collections import defaultdict
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import unicodedata


def normalize_name(name):
    """
    Normalize the given name by applying Unicode normalization (NFKC),
    stripping whitespace, and converting to lowercase.

    :param name: The input name as a string.
    :return: Normalized name as a string.
    """
    return unicodedata.normalize('NFKC', name.strip().lower())


def load_grouping_mapping(grouping_file_path):
    """
    Load the author grouping mapping from a specified file.

    :param grouping_file_path: Path to the grouping file.
    :return: Dictionary mapping author aliases to group names.
    """
    mapping = {}
    if not os.path.isfile(grouping_file_path):
        print(f"Warning: Grouping file not found: {grouping_file_path}")
        return mapping
    try:
        with open(grouping_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Ignore empty lines and comments
                if ':' not in line:
                    continue  # Ignore malformed lines
                group_name, aliases_str = line.split(":", 1)
                group_name = group_name.strip()
                aliases = [alias.strip() for alias in aliases_str.split(",") if alias.strip()]
                for alias in aliases:
                    mapping[normalize_name(alias)] = group_name
    except Exception as e:
        print(f"Failed to open grouping file {grouping_file_path}: {e}")
        return {}
    return mapping


def main(repo_path, grouping_file=None):
    """
    Analyze the Git repository to determine the number of lines contributed
    by each author, with optional author grouping.

    :param repo_path: Path to the Git repository.
    :param grouping_file: Optional path to the grouping file for author mapping.
    """
    if not os.path.isdir(repo_path):
        raise ValueError(f"Path {repo_path} is not a valid directory")
    
    git_dir = os.path.join(repo_path, '.git')
    if not os.path.isdir(git_dir):
        raise ValueError(f"Path {repo_path} is not a Git repository")

    original_dir = os.getcwd()
    os.chdir(repo_path)

    if grouping_file:
        grouping_file_path = grouping_file
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        grouping_file_path = os.path.join(script_dir, "grouping.txt")
    
    print(f"Looking for grouping file at: {grouping_file_path}")
    group_mapping = load_grouping_mapping(grouping_file_path)
    print(f"Loaded {len(group_mapping)} mappings")
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to get list of files: " + result.stderr)
        
        files = result.stdout.splitlines()
        total_files = len(files)
        print(f"Found {total_files} files to analyze.")

        author_counts = defaultdict(int)

        for index, file_path in enumerate(files, start=1):
            if index % 100 == 0 or index == total_files:
                print(f"Processing file {index}/{total_files}: {file_path}")
            try:
                cmd = ['git', 'blame', '-p', '--', file_path]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                if result.returncode != 0 or not result.stdout.strip():
                    continue

                for line in result.stdout.splitlines():
                    if line.startswith('\t'):
                        continue
                    if line.startswith('author '):
                        author = line[len('author '):].strip()
                        author_counts[author] += 1
            except Exception:
                continue

        print("Processing complete.")

        if not author_counts:
            print("No data available for statistics.")
            return

        grouped_counts = defaultdict(int)
        for author, count in author_counts.items():
            group = group_mapping.get(normalize_name(author), author)
            grouped_counts[group] += count

        df = pd.DataFrame(list(grouped_counts.items()), columns=['Author', 'Lines'])
        df = df.sort_values(by='Lines', ascending=False).reset_index(drop=True)

        print("\nLines of Code per Author/Group:")
        print(df.to_string(index=False))

        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.bar(df['Author'], df['Lines'], color='skyblue')
        plt.title('Lines of Code per Author/Group')
        plt.xlabel('Author/Group')
        plt.ylabel('Lines')
        plt.xticks(rotation=45, ha='right')

        plt.subplot(1, 2, 2)
        plt.pie(df['Lines'], labels=df['Author'], autopct='%1.1f%%', startangle=90)
        plt.title('Percentage Distribution')

        plt.tight_layout()
        plt.show()

    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Analyze Git repository line contributions with optional grouping.'
    )
    parser.add_argument('repo_path', help='Path to Git repository')
    parser.add_argument(
        '--grouping-file',
        help='Path to grouping mapping file (default: grouping.txt in the script directory)',
        default=None
    )
    args = parser.parse_args()
    
    main(args.repo_path, args.grouping_file)
