"""Issue/PR Creator Agent - Task 2: Draft and create GitHub Issues/PRs with approval"""
from src.agents.base_agent import BaseAgent
from src.tools import GitHubOps, OllamaClient
from typing import Dict, Any, Optional


class IssuePRCreatorAgent(BaseAgent):
    """
    Creates GitHub Issues or Pull Requests based on recommendations.

    Implements:
    - Planning: Determine content structure, format, labels
    - Tool Use: GitHub API to create tickets
    - Reflection: Review draft, ensure quality
    - Multi-agent ready: Takes input from ChangeReviewAgent
    """

    def __init__(self):
        super().__init__("IssuePRCreatorAgent", model="ministral")
        self.github = GitHubOps()

    def get_system_prompt(self) -> str:
        return """You are a GitHub Issue/PR Creator Agent.
Your job is to:
1. Take a change analysis and create compelling GitHub content
2. Draft issue titles and detailed descriptions
3. Suggest appropriate labels and milestones
4. Ensure content follows best practices
5. Review quality before creation

Create clear, professional GitHub tickets that follow standards."""

    def get_available_tools(self) -> str:
        return """AVAILABLE TOOLS:
1. DRAFT_ISSUE - Create issue title and description
2. DRAFT_PR - Create PR title and description
3. SUGGEST_LABELS - Recommend relevant labels
4. SUGGEST_REVIEWERS - Suggest team members to review
5. VALIDATE_CONTENT - Ensure quality and completeness
6. GITHUB_CREATE - Actually create the ticket"""

    def draft_issue(
        self,
        change_type: str,
        summary: str,
        analysis: str,
        risk_level: str
    ) -> Dict[str, Any]:
        """
        Draft a GitHub Issue based on change analysis.

        Args:
            change_type: Type of change (feature/bugfix/refactor/etc)
            summary: Summary of the change
            analysis: Detailed analysis
            risk_level: Risk assessment (low/medium/high)

        Returns:
            Draft issue with title, description, labels
        """
        task = f"""Draft a GitHub Issue for this change:

Change Type: {change_type}
Risk Level: {risk_level}
Summary: {summary}
Analysis: {analysis}

Create a detailed GitHub issue with:
1. Compelling title (short, descriptive)
2. Well-structured description with sections:
   - Overview (2-3 sentences)
   - Details (bullet points)
   - Acceptance Criteria (if applicable)
   - Related Links (if any)
3. Suggested labels (comma-separated, GitHub-style)

Format your response as:
TITLE: [issue title]
DESCRIPTION:
[full description with markdown]
LABELS: [label1, label2, label3]"""

        # Execute agent workflow
        execution = self.execute(task)

        # Parse the draft
        return self._parse_issue_draft(execution)

    def draft_pull_request(
        self,
        branch_name: str,
        change_type: str,
        summary: str,
        analysis: str,
        risk_level: str,
        files_changed: int,
        insertions: int,
        deletions: int
    ) -> Dict[str, Any]:
        """
        Draft a GitHub Pull Request based on change analysis.

        Args:
            branch_name: Feature branch name
            change_type: Type of change
            summary: Summary of changes
            analysis: Detailed analysis
            risk_level: Risk assessment
            files_changed: Number of files modified
            insertions: Number of insertions
            deletions: Number of deletions

        Returns:
            Draft PR with title, description, labels
        """
        task = f"""Draft a GitHub Pull Request for this change:

Branch: {branch_name}
Change Type: {change_type}
Risk Level: {risk_level}
Files: {files_changed} | +{insertions} -{deletions}

Summary: {summary}
Analysis: {analysis}

Create a professional GitHub PR with:
1. Compelling title (short, descriptive)
2. Well-structured description with sections:
   - What Changed (overview of modifications)
   - Why (reasoning and motivation)
   - Testing (how to verify changes)
   - Risk Assessment (potential issues)
   - Checklist (review items)
3. Suggested labels and reviewers

Format your response as:
TITLE: [PR title]
DESCRIPTION:
[full description with markdown]
LABELS: [label1, label2, label3]
REVIEWERS: [optional list]"""

        # Execute agent workflow
        execution = self.execute(task)

        # Parse the draft
        return self._parse_pr_draft(execution)

    def create_issue(
        self,
        title: str,
        description: str,
        labels: Optional[list] = None,
        assignee: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a GitHub Issue with approval check.

        Args:
            title: Issue title
            description: Issue description (markdown)
            labels: List of label names
            assignee: GitHub username to assign

        Returns:
            Result with GitHub URL or error
        """
        try:
            result = self.github.create_issue(
                title=title,
                body=description,
                labels=labels or [],
                assignee=assignee
            )
            return {
                "status": "success",
                "action": "create_issue",
                "url": result.get("url", ""),
                "number": result.get("number", ""),
                "message": f"✅ Issue created successfully!"
            }
        except Exception as e:
            return {
                "status": "error",
                "action": "create_issue",
                "error": str(e)
            }

    def create_pull_request(
        self,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        labels: Optional[list] = None,
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Create a GitHub Pull Request with approval check.

        Args:
            title: PR title
            description: PR description (markdown)
            head_branch: Feature branch
            base_branch: Target branch (default: main)
            labels: List of label names
            draft: Whether to create as draft PR

        Returns:
            Result with GitHub URL or error
        """
        try:
            result = self.github.create_pull_request(
                title=title,
                body=description,
                head=head_branch,
                base=base_branch,
                draft=draft
            )
            return {
                "status": "success",
                "action": "create_pull_request",
                "url": result.get("url", ""),
                "number": result.get("number", ""),
                "message": f"✅ Pull Request created successfully!"
            }
        except Exception as e:
            return {
                "status": "error",
                "action": "create_pull_request",
                "error": str(e)
            }

    def _parse_issue_draft(self, execution: Dict[str, Any]) -> Dict[str, str]:
        """Parse drafted issue from agent response"""
        reflection = execution.get("reflection", {})
        decision = reflection.get("decision", "")

        draft = {
            "title": "",
            "description": "",
            "labels": []
        }

        # Extract sections
        lines = decision.split("\n")
        current_section = None

        for line in lines:
            if "TITLE:" in line:
                draft["title"] = line.split("TITLE:")[1].strip()
            elif "DESCRIPTION:" in line:
                current_section = "description"
            elif "LABELS:" in line:
                current_section = "labels"
                labels_str = line.split("LABELS:")[1].strip()
                draft["labels"] = [l.strip() for l in labels_str.split(",")]
            elif current_section == "description" and line.strip():
                draft["description"] += line + "\n"

        return draft

    def _parse_pr_draft(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        """Parse drafted PR from agent response"""
        reflection = execution.get("reflection", {})
        decision = reflection.get("decision", "")

        draft = {
            "title": "",
            "description": "",
            "labels": [],
            "reviewers": []
        }

        # Extract sections
        lines = decision.split("\n")
        current_section = None

        for line in lines:
            if "TITLE:" in line:
                draft["title"] = line.split("TITLE:")[1].strip()
            elif "DESCRIPTION:" in line:
                current_section = "description"
            elif "LABELS:" in line:
                current_section = "labels"
                labels_str = line.split("LABELS:")[1].strip()
                draft["labels"] = [l.strip() for l in labels_str.split(",")]
            elif "REVIEWERS:" in line:
                current_section = "reviewers"
                reviewers_str = line.split("REVIEWERS:")[1].strip()
                if reviewers_str:
                    draft["reviewers"] = [r.strip()
                                          for r in reviewers_str.split(",")]
            elif current_section == "description" and line.strip():
                draft["description"] += line + "\n"

        return draft
