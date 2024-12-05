import os
import json
import hashlib
import shutil
import fnmatch
from typing import Optional


class Versionix:
    """Versionix"""
    def __init__(self, path: str = '.'):
        """
        Initialize a new version control repository

        :param path: Path to the repository root
        """

        self.repo_path = os.path.abspath(path)
        self.vsx_dir = os.path.join(path, '.vsx')

        if not os.path.exists(self.vsx_dir):
            os.makedirs(self.vsx_dir)
            os.makedirs(os.path.join(self.vsx_dir, 'objects'))
            os.makedirs(os.path.join(self.vsx_dir, 'branches'))

            with open(os.path.join(self.vsx_dir, 'HEAD'), 'w') as f:
                f.write('main')

            with open(os.path.join(self.vsx_dir, 'commits'), 'w') as f:
                json.dump([], f)

            with open(os.path.join(self.vsx_dir, 'stage'), 'w') as f:
                json.dump([], f)

            with open(os.path.join(path, '.vsxignore'), 'w') as f:
                f.write('.vsx\n.vsxignore\n')

    @staticmethod
    def _hash_file(file_path: str) -> str:
        """
        Generate a hash for a file's content

        :param file_path: Path to the file
        :return: SHA-256 hash of the file content
        """
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _is_ignored(self, filepath: str) -> bool:
        """
        Check if a file should be ignored based on .vsxignore

        :param filepath: Path to the file
        :return: Whether the file is ignored
        """
        ignore_path = os.path.join(self.repo_path, '.vsxignore')
        if not os.path.exists(ignore_path):
            return False

        rel_path = os.path.relpath(filepath, self.repo_path)

        with open(ignore_path, 'r') as f:
            ignore_patterns = [line.strip() for line in f if line.strip()]

        for pattern in ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        return False

    def add(self, filepath: str):
        """
        Stage a file for commit

        :param filepath: Path to the file to stage
        """
        full_path = os.path.join(self.repo_path, filepath)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {filepath}")

        if self._is_ignored(full_path):
            print(f"File {filepath} is ignored and cannot be staged.")
            return

        # Read current staging area
        with open(os.path.join(self.vsx_dir, 'stage'), 'r') as f:
            staged_files = json.load(f)

        file_hash = self._hash_file(full_path)
        object_path = os.path.join(self.vsx_dir, 'objects', file_hash)
        shutil.copy(full_path, object_path)

        staged_files = [f for f in staged_files if f['path'] != filepath]
        staged_files.append({
            'path': filepath,
            'hash': file_hash
        })

        with open(os.path.join(self.vsx_dir, 'stage'), 'w') as f:
            json.dump(staged_files, f)

        print(f"Added {filepath} to staging area")

    def commit(self, message: str):
        """
        Commit staged changes

        :param message: Commit message
        """

        with open(os.path.join(self.vsx_dir, 'stage'), 'r') as f:
            staged_files = json.load(f)

        if not staged_files:
            print("No changes to commit.")
            return

        with open(os.path.join(self.vsx_dir, 'commits'), 'r') as f:
            commits = json.load(f)

        commit = {
            'id': hashlib.sha256(message.encode()).hexdigest(),
            'message': message,
            'files': staged_files,
            'parent': commits[-1]['id'] if commits else None
        }

        commits.append(commit)

        with open(os.path.join(self.vsx_dir, 'commits'), 'w') as f:
            json.dump(commits, f)

        with open(os.path.join(self.vsx_dir, 'stage'), 'w') as f:
            json.dump([], f)

        print(f"Committed with message: {message}")

    def log(self):
        """Display commit history"""
        with open(os.path.join(self.vsx_dir, 'commits'), 'r') as f:
            commits = json.load(f)

        if not commits:
            print("No commits yet.")
            return

        for commit in reversed(commits):
            print(f"Commit {commit['id'][:7]}")
            print(f"Message: {commit['message']}")
            print("Files:")
            for file in commit['files']:
                print(f"  {file['path']} (hash: {file['hash'][:7]})")
            print()

    def branch(self, branch_name: Optional[str] = None):
        """
        Create or list branches

        :param branch_name: Name of the branch to create (optional)
        """
        branches_dir = os.path.join(self.vsx_dir, 'branches')

        if branch_name is None:
            branches = [f for f in os.listdir(branches_dir) if os.path.isfile(os.path.join(branches_dir, f))]
            print("Branches:")
            for b in branches:
                print(f"  {b}")
            return

        branch_path = os.path.join(branches_dir, branch_name)

        with open(os.path.join(self.vsx_dir, 'commits'), 'r') as f:
            commits = json.load(f)

        current_commit = commits[-1]['id'] if commits else None

        with open(branch_path, 'w') as f:
            f.write(current_commit or '')

        print(f"Created branch {branch_name}")

    def diff(self, branch1: str, branch2: str):
        """
        Show differences between two branches

        :param branch1: First branch name
        :param branch2: Second branch name
        """
        branches_dir = os.path.join(self.vsx_dir, 'branches')

        # Read commits for both branches
        with open(os.path.join(self.vsx_dir, 'commits'), 'r') as f:
            all_commits = json.load(f)

        # Get branch commit IDs
        with open(os.path.join(branches_dir, branch1), 'r') as f:
            branch1_commit = f.read().strip()

        with open(os.path.join(branches_dir, branch2), 'r') as f:
            branch2_commit = f.read().strip()

        branch1_commits = [c for c in all_commits if c['id'] == branch1_commit]
        branch2_commits = [c for c in all_commits if c['id'] == branch2_commit]

        if not branch1_commits or not branch2_commits:
            print("Invalid branch or no commits.")
            return

        branch1_files = {f['path']: f['hash'] for f in branch1_commits[0]['files']}
        branch2_files = {f['path']: f['hash'] for f in branch2_commits[0]['files']}

        print(f"Differences between {branch1} and {branch2}:")

        # Files in branch1 but not in branch2
        for path, hash in branch1_files.items():
            if path not in branch2_files:
                print(f"  File added in {branch1}: {path}")
            elif branch2_files[path] != hash:
                print(f"  File changed: {path}")

        # Files in branch2 but not in branch1
        for path in branch2_files:
            if path not in branch1_files:
                print(f"  File added in {branch2}: {path}")

    def clone(self, destination: str):
        """
        Clone the repository to a new location

        :param destination: Path to clone the repository
        """
        shutil.copytree(self.repo_path, destination, ignore=shutil.ignore_patterns('.vsx'))
        print(f"Cloned repository to {destination}")
