import os
import json
import shutil
import time
from typing import Dict, List, Optional


class BranchManager:
    """ Branch management for a repository"""

    def __init__(self, repo_path: str):
        """
        Initialize branch management for a repository

        :param repo_path: Root path of the repository
        """
        self.repo_path = repo_path
        self.vsx_dir = os.path.join(repo_path, '.vsx')
        self.branches_dir = os.path.join(self.vsx_dir, 'branches')
        self.commits_file = os.path.join(self.vsx_dir, 'commits')
        self.head_file = os.path.join(self.vsx_dir, 'HEAD')

        os.makedirs(self.branches_dir, exist_ok=True)

    def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> Dict:
        """
        Create a new branch, inheriting commits from a base branch

        :param branch_name: Name of the new branch
        :param base_branch: Branch to inherit commits from (defaults to current branch)
        :return: Branch metadata
        """
        if base_branch is None:
            base_branch = self.get_current_branch()

        base_branch_path = os.path.join(self.branches_dir, base_branch)
        if not os.path.exists(base_branch_path):
            raise ValueError(f"Base branch {base_branch} does not exist")

        with open(base_branch_path, 'r') as f:
            base_branch_metadata = json.load(f)

        base_commit_id = base_branch_metadata['head']

        branch_metadata = {
            'name': branch_name,
            'base_commit': base_commit_id,
            'head': base_commit_id,
            'created_at': time.time(),
            'commit_history': [],
            'parent_branch': base_branch
        }

        branch_path = os.path.join(self.branches_dir, branch_name)
        with open(branch_path, 'w') as f:
            json.dump(branch_metadata, f, indent=2)

        print(f"Created branch {branch_name} based on {base_branch}")
        return branch_metadata

    @staticmethod
    def _get_commit_history(all_commits: List[Dict], start_commit_id: str) -> List[str]:
        """
        Trace the commit history from a given commit

        :param all_commits: List of all commits
        :param start_commit_id: Commit ID to start tracing from
        :return: List of commit IDs in order
        """
        commit_history = []
        current_commit_id = start_commit_id

        while current_commit_id:
            commit = next((c for c in all_commits if c['id'] == current_commit_id), None)
            if not commit:
                break

            commit_history.append(current_commit_id)
            current_commit_id = commit.get('parent')

        return commit_history

    def list_branches(self) -> List[str]:
        """
        List all branches in the repository

        :return: List of branch names
        """
        try:
            return [f for f in os.listdir(self.branches_dir) if os.path.isfile(os.path.join(self.branches_dir, f))]
        except FileNotFoundError:
            return []

    def get_current_branch(self) -> str:
        """
        Get the current active branch

        :return: Current branch name
        """
        try:
            with open(self.head_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return 'main'

    def switch_branch(self, branch_name: str):
        """
        Switch to a specified branch

        :param branch_name: Name of the branch to switch to
        """
        branch_path = os.path.join(self.branches_dir, branch_name)

        if not os.path.exists(branch_path):
            raise ValueError(f"Branch {branch_name} does not exist")

        with open(branch_path, 'r') as f:
            branch_metadata = json.load(f)

        with open(self.commits_file, 'r') as f:
            all_commits = json.load(f)

        target_commit_id = branch_metadata['head']
        target_commit = next((c for c in all_commits if c['id'] == target_commit_id), None)

        if not target_commit:
            raise ValueError(f"No commit found for branch {branch_name}")

        self._restore_branch_state(branch_metadata)

        with open(self.head_file, 'w') as f:
            f.write(branch_name)

        print(f"Switched to branch {branch_name}")

    def _restore_branch_state(self, branch_metadata: Dict):
        """
        Recursively restore repository state based on branch metadata and commits,
        including parent branch commits up to the specified head commit.

        :param branch_metadata: Metadata of the branch being checked out
        """
        self._clear_tracked_files()
        processed_commits = set()

        def restore_branch_commits(current_branch_metadata: Dict, max_commit_id: str = None):
            """
            Recursively restore commits for a branch and its parent branches

            :param current_branch_metadata: Metadata of the current branch
            :param max_commit_id: Maximum commit ID to restore in parent branches
            """
            with open(self.commits_file, 'r') as f:
                all_commits = json.load(f)

            for commit_id in current_branch_metadata['commit_history']:
                if commit_id not in processed_commits:
                    commit = next((c for c in all_commits if c['id'] == commit_id), None)
                    if commit:
                        _restore_single_commit_files(commit)
                        processed_commits.add(commit_id)

            if current_branch_metadata.get('parent_branch'):
                parent_branch_path = os.path.join(self.branches_dir, current_branch_metadata['parent_branch'])

                if os.path.exists(parent_branch_path):
                    with open(parent_branch_path, 'r') as f:
                        parent_branch_metadata = json.load(f)

                    if max_commit_id is None:
                        max_commit_id = current_branch_metadata.get('base_commit')

                    try:
                        max_commit_index = parent_branch_metadata['commit_history'].index(max_commit_id)
                        parent_commits_to_restore = parent_branch_metadata['commit_history'][:max_commit_index + 1]

                        limited_parent_metadata = parent_branch_metadata.copy()
                        limited_parent_metadata['commit_history'] = parent_commits_to_restore

                        restore_branch_commits(limited_parent_metadata)

                    except ValueError:
                        print(f"Warning: Commit {max_commit_id} not found in parent branch history")

        def _restore_single_commit_files(commit: Dict):
            """
            Restore files for a single commit

            :param commit: Commit dictionary
            """
            for file_info in commit.get('files', []):
                source_path = os.path.join(self.vsx_dir, 'objects', file_info['hash'])
                dest_path = os.path.join(self.repo_path, file_info['path'])

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                shutil.copy(source_path, dest_path)

        restore_branch_commits(branch_metadata)

        print("Branch state restored, including limited parent branch files")

    def _clear_tracked_files(self):
        """
        Remove all previously tracked files from the repository
        """
        with open(self.commits_file, 'r') as f:
            all_commits = json.load(f)

        all_tracked_files = set()
        for commit in all_commits:
            all_tracked_files.update(f['path'] for f in commit.get('files', []))

        for tracked_file in all_tracked_files:
            full_path = os.path.join(self.repo_path, tracked_file)
            if os.path.exists(full_path):
                os.remove(full_path)

    def _restore_commit_state(self, commit: Dict):
        """
        Restore repository state to a specific commit,
        only modifying files that were previously tracked

        :param commit: Commit dictionary
        """
        tracked_files = {file_info['path'] for file_info in commit.get('files', [])}

        for file_info in commit.get('files', []):
            source_path = os.path.join(self.vsx_dir, 'objects', file_info['hash'])
            dest_path = os.path.join(self.repo_path, file_info['path'])

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            shutil.copy(source_path, dest_path)

        with open(os.path.join(self.vsx_dir, 'commits'), 'r') as f:
            all_commits = json.load(f)

        all_tracked_files = set()
        for previous_commit in all_commits:
            all_tracked_files.update(f['path'] for f in previous_commit.get('files', []))

        for tracked_file in all_tracked_files:
            if tracked_file not in tracked_files:
                full_path = os.path.join(self.repo_path, tracked_file)
                if os.path.exists(full_path):
                    os.remove(full_path)

    def merge_branches(self, source_branch: str, target_branch: str):
        """
        Merge one branch into another

        :param source_branch: Branch to merge from
        :param target_branch: Branch to merge into
        """
        print(f"Merging {source_branch} into {target_branch}")
        #TODO: Implement merge
