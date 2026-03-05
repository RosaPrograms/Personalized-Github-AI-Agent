"""Git operations for analyzing repository changes"""
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DiffAnalysis:
    """Result of git diff analysis"""
    files_changed: int
    insertions: int
    deletions: int
    files: List[Dict[str, str]]
    raw_diff: str


class GitOps:
    """Git operations handler"""

    @staticmethod
    def get_current_branch() -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get current branch: {e}")

    @staticmethod
    def get_diff(ref1: Optional[str] = None, ref2: Optional[str] = None) -> str:
        """
        Get git diff between two refs
        If ref1 and ref2 are None, returns diff with HEAD
        """
        try:
            if ref1 and ref2:
                cmd = ["git", "diff", ref1, ref2]
            elif ref1:
                cmd = ["git", "diff", ref1]
            else:
                cmd = ["git", "diff", "HEAD"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get git diff: {e}")

    @staticmethod
    def get_staged_diff() -> str:
        """Get diff of staged changes"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get staged diff: {e}")

    @staticmethod
    def get_changed_files() -> List[str]:
        """Get list of changed files"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get changed files: {e}")

    @staticmethod
    def parse_diff(diff_text: str) -> DiffAnalysis:
        """Parse git diff and extract statistics"""
        files_changed = 0
        insertions = 0
        deletions = 0
        files = []

        lines = diff_text.split("\n")
        current_file = None

        for line in lines:
            if line.startswith("diff --git"):
                parts = line.split(" ")
                current_file = {
                    "from": parts[2],
                    "to": parts[3],
                    "changes": 0
                }
                files_changed += 1
            elif line.startswith("+++") or line.startswith("---"):
                continue
            elif line.startswith("+") and not line.startswith("+++"):
                insertions += 1
                if current_file:
                    current_file["changes"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
                if current_file:
                    current_file["changes"] += 1

            if current_file and current_file not in files:
                files.append(current_file)

        return DiffAnalysis(
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            files=files,
            raw_diff=diff_text
        )

    @staticmethod
    def get_commit_log(count: int = 5) -> List[Dict[str, str]]:
        """Get recent commit log"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%H|%h|%s|%b"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|", 3)
                    commits.append({
                        "hash": parts[0],
                        "short_hash": parts[1],
                        "subject": parts[2],
                        "body": parts[3] if len(parts) > 3 else ""
                    })
            return commits
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get commit log: {e}")
