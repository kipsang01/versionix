import os
import json
import hashlib
import shutil
import fnmatch
import time
from typing import Optional

from versionix.branches import BranchManager


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

            with open(os.path.join(self.vsx_dir, 'config'), 'w') as f:
                f.write('')

            with open(os.path.join(path, '.vsxignore'), 'w') as f:
                f.write('.vsx\n.vsxignore\n')

            main_branch_path = os.path.join(self.vsx_dir, 'branches', 'main')
            main_branch_metadata = {
                'name': 'main',
                'base_commit': None,
                'head': None,
                'created_at': time.time(),
                'commit_history': [],
                'parent_branch': None
            }

            with open(main_branch_path, 'w') as f:
                json.dump(main_branch_metadata, f, indent=2)

            print("Initialized empty Versionix repository")

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

    def add(self, filepath: str, operation: str = 'add'):
        """
        Stage a file for commit, supporting add, modify, and delete operations

        :param filepath: Path to the file to stage
        :param operation: Type of operation (add, modify, delete)
        """
        full_path = os.path.join(self.repo_path, filepath)

        if operation not in ['add', 'modify', 'delete']:
            raise ValueError("Operation must be 'add', 'modify', or 'delete'")

        if operation != 'delete' and not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {filepath}")

        if operation != 'delete' and self._is_ignored(full_path):
            print(f"File {filepath} is ignored and cannot be staged.")
            return

        with open(os.path.join(self.vsx_dir, 'stage'), 'r') as f:
            staged_files = json.load(f)

        staged_files = [f for f in staged_files if f['path'] != filepath]

        if operation in ['add', 'modify']:
            file_hash = self._hash_file(full_path)
            object_path = os.path.join(self.vsx_dir, 'objects', file_hash)
            shutil.copy(full_path, object_path)

            staged_files.append({
                'path': filepath,
                'hash': file_hash,
                'operation': operation
            })
        elif operation == 'delete':
            branch_manager = BranchManager(self.repo_path)
            current_branch = branch_manager.get_current_branch()
            branch_path = os.path.join(self.vsx_dir, 'branches', current_branch)

            with open(branch_path, 'r') as f:
                branch_metadata = json.load(f)

            with open(os.path.join(self.vsx_dir, 'commits'), 'r') as f:
                commits = json.load(f)

            head_commit = next((c for c in commits if c['id'] == branch_metadata['head']), None)

            if head_commit:
                tracked_file = next((f for f in head_commit.get('files', []) if f['path'] == filepath), None)

                if not tracked_file:
                    print(f"File {filepath} is not tracked and cannot be deleted.")
                    return

            staged_files.append({
                'path': filepath,
                'operation': 'delete'
            })

        with open(os.path.join(self.vsx_dir, 'stage'), 'w') as f:
            json.dump(staged_files, f)

        print(f"{operation.capitalize()}d {filepath} to staging area")

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

        branch_manager = BranchManager(self.repo_path)
        current_branch = branch_manager.get_current_branch()

        branch_path = os.path.join(self.vsx_dir, 'branches', current_branch)
        with open(branch_path, 'r') as f:
            branch_metadata = json.load(f)

        commit_files = []
        for staged_file in staged_files:
            commit_file = {
                'path': staged_file['path'],
                'operation': staged_file.get('operation', 'add')
            }

            if staged_file.get('operation') != 'delete':
                commit_file['hash'] = staged_file['hash']

            commit_files.append(commit_file)

        commit = {
            'id': hashlib.sha256(message.encode() + str(time.time()).encode()).hexdigest(),
            'message': message,
            'files': commit_files,
            'parent': branch_metadata['head']
        }

        commits.append(commit)

        with open(os.path.join(self.vsx_dir, 'commits'), 'w') as f:
            json.dump(commits, f, indent=2)

        branch_metadata['head'] = commit['id']
        branch_metadata.setdefault('commit_history', []).append(commit['id'])

        with open(branch_path, 'w') as f:
            json.dump(branch_metadata, f, indent=2)

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

        branch_manager = BranchManager(self.repo_path)

        if branch_name is None:
            branches = branch_manager.list_branches()
            if not branches:
                print("No branches yet.")
                return
            print("Branches:")
            for b in branches:
                print(f"  {b}")
            return

        branch_manager.create_branch(branch_name)

    def diff(self, branch1: str, branch2: str):
        """
        Show differences between two branches

        :param branch1: First branch name
        :param branch2: Second branch name
        """
        branches_dir = os.path.join(self.vsx_dir, 'branches')

        if not os.path.exists(os.path.join(branches_dir, branch1)):
            print(f"Branch {branch1} does not exist.")
            return

        if not os.path.exists(os.path.join(branches_dir, branch2)):
            print(f"Branch {branch2} does not exist.")
            return

        with open(os.path.join(self.vsx_dir, 'commits'), 'r') as f:
            all_commits = json.load(f)

        with open(os.path.join(branches_dir, branch1), 'r') as f:
            branch1_metadata = json.load(f)

        with open(os.path.join(branches_dir, branch2), 'r') as f:
            branch2_metadata = json.load(f)

        branch1_commit = next((c for c in all_commits if c['id'] == branch1_metadata['head']), None)
        branch2_commit = next((c for c in all_commits if c['id'] == branch2_metadata['head']), None)

        if not branch1_commit or not branch2_commit:
            print("No commits found for one or both branches.")
            return

        branch1_files = {f['path']: f['hash'] for f in branch1_commit['files']}
        branch2_files = {f['path']: f['hash'] for f in branch2_commit['files']}

        print(f"Differences between {branch1} and {branch2}:")

        only_in_branch1 = set(branch1_files.keys()) - set(branch2_files.keys())
        if only_in_branch1:
            print(f"\nFiles only in {branch1}:")
            for path in only_in_branch1:
                print(f"  + {path}")

        only_in_branch2 = set(branch2_files.keys()) - set(branch1_files.keys())
        if only_in_branch2:
            print(f"\nFiles only in {branch2}:")
            for path in only_in_branch2:
                print(f"  + {path}")

        common_files = set(branch1_files.keys()) & set(branch2_files.keys())
        modified_files = [
            path for path in common_files
            if branch1_files[path] != branch2_files[path]
        ]

        if modified_files:
            print("\nModified files:")
            for path in modified_files:
                print(f"  ~ {path}")
                print(f"    Previous hash: {branch1_files[path][:7]}")
                print(f"    Current hash:  {branch2_files[path][:7]}")

        if not (only_in_branch1 or only_in_branch2 or modified_files):
            print("No differences found between the branches.")

    def clone(self, destination: str):
        """
        Clone the repository to a new location

        :param destination: Path to clone the repository
        """
        shutil.copytree(self.repo_path, destination, ignore=shutil.ignore_patterns('.vsx'))
        print(f"Cloned repository to {destination}")

    def checkout(self, branch_name: str):
        """
        Checkout a branch

        :param branch_name: Name of the branch to checkout
        """

        branch_manager = BranchManager(self.repo_path)
        branch_manager.switch_branch(branch_name)

    def unstage(self, filepath: str):
        """
        Remove a file from the staging area

        :param filepath: Path to the file to remove
        """
        with open(os.path.join(self.vsx_dir, 'stage'), 'r') as f:
            staged_files = json.load(f)

        staged_files = [f for f in staged_files if f['path'] != filepath]

        with open(os.path.join(self.vsx_dir, 'stage'), 'w') as f:
            json.dump(staged_files, f)

    def status(self):
        """
        Display the status of the repository
        """
        self.log()

        with open(os.path.join(self.vsx_dir, 'stage'), 'r') as f:
            staged_files = json.load(f)

        print("Staged files:")
        for file in staged_files:
            print(f"  {file['path']} (hash: {file['hash'][:7]})")
        print()

        print("Unstaged files:")
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                full_path = os.path.join(root, file)
                if not self._is_ignored(full_path):
                    print(f"  {full_path}")
        print()

        print("Ignored files:")
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                full_path = os.path.join(root, file)
                if self._is_ignored(full_path):
                    print(f"  {full_path}")
        print()

    def _get_current_branch(self):
        """
        Get the current active branch

        :return: Current branch name
        """
        with open(os.path.join(self.vsx_dir, 'HEAD'), 'r') as f:
            return f.read().strip()

    def _update_branch_head(self, branch_name, commit_id):
        """
        Update the head of a specific branch

        :param branch_name: Name of the branch
        :param commit_id: ID of the new commit
        """
        branch_path = os.path.join(self.vsx_dir, 'branches', branch_name)

        try:
            with open(branch_path, 'r') as f:
                branch_metadata = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            branch_metadata = {
                'name': branch_name,
                'base_commit': None,
                'head': None,
                'created_at': time.time(),
                'merge_history': []
            }

        branch_metadata['head'] = commit_id

        if branch_metadata['base_commit'] is None:
            branch_metadata['base_commit'] = commit_id

        with open(branch_path, 'w') as f:
            json.dump(branch_metadata, f, indent=2)
