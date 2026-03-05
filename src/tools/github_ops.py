"""GitHub operations using PyGithub"""
from typing import Dict, Optional, Tuple
from github import Github, GithubException
from src.config import settings


class GitHubOps:
    """GitHub API operations handler"""

    def __init__(self):
        self.gh = Github(settings.GITHUB_PAT)
        self.repo = self.gh.get_user(settings.GITHUB_REPO_OWNER).get_repo(
            settings.GITHUB_REPO_NAME
        )

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list] = None,
        assignee: Optional[str] = None
    ) -> Dict:
        """Create a GitHub issue"""
        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels or [],
                assignee=assignee
            )
            return {
                "success": True,
                "url": issue.html_url,
                "number": issue.number,
                "id": issue.id
            }
        except GithubException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False
    ) -> Dict:
        """Create a GitHub pull request"""
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
                draft=draft
            )
            return {
                "success": True,
                "url": pr.html_url,
                "number": pr.number,
                "id": pr.id
            }
        except GithubException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_issue(self, issue_number: int) -> Dict:
        """Get issue details"""
        try:
            issue = self.repo.get_issue(issue_number)
            return {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "url": issue.html_url
            }
        except GithubException as e:
            return {"error": str(e)}

    def get_pull_request(self, pr_number: int) -> Dict:
        """Get pull request details"""
        try:
            pr = self.repo.get_pull(pr_number)
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "labels": [label.name for label in pr.labels],
                "url": pr.html_url,
                "head": pr.head.ref,
                "base": pr.base.ref
            }
        except GithubException as e:
            return {"error": str(e)}

    def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict:
        """Update an issue"""
        try:
            issue = self.repo.get_issue(issue_number)
            if title:
                issue.edit(title=title)
            if body:
                issue.edit(body=body)
            if state:
                issue.edit(state=state)
            return {"success": True}
        except GithubException as e:
            return {"success": False, "error": str(e)}

    def update_pull_request(
        self,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict:
        """Update a pull request"""
        try:
            pr = self.repo.get_pull(pr_number)
            if title:
                pr.edit(title=title)
            if body:
                pr.edit(body=body)
            if state:
                pr.edit(state=state)
            return {"success": True}
        except GithubException as e:
            return {"success": False, "error": str(e)}

    def add_comment(self, issue_or_pr_number: int, body: str, is_pr: bool = False) -> Dict:
        """Add a comment to issue or PR"""
        try:
            if is_pr:
                pr = self.repo.get_pull(issue_or_pr_number)
                comment = pr.create_issue_comment(body)
            else:
                issue = self.repo.get_issue(issue_or_pr_number)
                comment = issue.create_comment(body)
            return {
                "success": True,
                "comment_id": comment.id,
                "url": comment.html_url
            }
        except GithubException as e:
            return {"success": False, "error": str(e)}
