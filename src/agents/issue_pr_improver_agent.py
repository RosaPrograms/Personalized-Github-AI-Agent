"""Issue/PR Improver Agent - Task 3: Improve existing Issues/PRs with suggestions"""
from src.agents.base_agent import BaseAgent
from src.tools import GitHubOps, OllamaClient
from typing import Dict, Any, Optional


class IssueImproverAgent(BaseAgent):
    """
    Analyzes and improves existing GitHub Issues or Pull Requests.

    Implements:
    - Planning: Analyze current content, identify weaknesses
    - Tool Use: GitHub API to fetch tickets
    - Reflection: Generate improvement suggestions
    - Multi-agent ready: Suggests changes, user approves
    """

    def __init__(self):
        super().__init__("IssueImproverAgent", model="ministral")
        self.github = GitHubOps()

    def get_system_prompt(self) -> str:
        return """You are a GitHub Issue/PR Quality Improver.
Your job is to:
1. Analyze existing issues/PRs for clarity and completeness
2. Identify areas that need improvement
3. Suggest better wording and structure
4. Recommend missing elements
5. Ensure content follows GitHub best practices

Make constructive suggestions that enhance communication."""

    def get_available_tools(self) -> str:
        return """AVAILABLE TOOLS:
1. ANALYZE_CONTENT - Review title, description, labels
2. CHECK_CLARITY - Assess how clear the content is
3. IDENTIFY_GAPS - Find missing information
4. SUGGEST_REWRITES - Propose improved text
5. VALIDATE_LABELS - Ensure appropriate labels
6. GENERATE_SUMMARY - Create concise summaries"""

    def improve_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Analyze and suggest improvements for an issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            Analysis with improvement suggestions
        """
        try:
            # Fetch issue details
            issue_data = self.github.get_issue(issue_number)

            if "error" in issue_data:
                return {
                    "status": "error",
                    "error": issue_data["error"]
                }

            # Create analysis task
            task = f"""Analyze this GitHub Issue and suggest improvements:

Current Title: {issue_data.get('title', '')}
Current Description:
{issue_data.get('body', '')}

Current Labels: {', '.join(issue_data.get('labels', []))}
Current State: {issue_data.get('state', 'open')}

Provide constructive suggestions for:
1. Title clarity and specificity
2. Description structure and completeness
3. Missing information (context, requirements, etc)
4. Label accuracy
5. Overall presentation

Format your response as:
ANALYSIS:
[current state assessment]

ISSUES_FOUND:
1. [Issue 1]
2. [Issue 2]
...

SUGGESTED_IMPROVEMENTS:
- Title: [improved title if needed]
- Description: [improved description or key sections to add]
- Labels: [updated label list]
- Other: [other recommendations]

DETAILED_SUGGESTIONS:
[explain each suggestion why it improves the issue]"""

            # Execute agent workflow
            execution = self.execute(task)

            # Parse suggestions
            suggestions = self._parse_improvements(execution)

            return {
                "status": "success",
                "issue_number": issue_number,
                "current": issue_data,
                "suggestions": suggestions,
                "full_analysis": execution
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def improve_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """
        Analyze and suggest improvements for a pull request.

        Args:
            pr_number: GitHub PR number

        Returns:
            Analysis with improvement suggestions
        """
        try:
            # Fetch PR details
            pr_data = self.github.get_pull_request(pr_number)

            if "error" in pr_data:
                return {
                    "status": "error",
                    "error": pr_data["error"]
                }

            # Create analysis task
            task = f"""Analyze this GitHub Pull Request and suggest improvements:

Current Title: {pr_data.get('title', '')}
Current Description:
{pr_data.get('body', '')}

Branch: {pr_data.get('head', '')} -> {pr_data.get('base', '')}
Current Labels: {', '.join(pr_data.get('labels', []))}
Current State: {pr_data.get('state', 'open')}

Provide constructive suggestions for:
1. Title clarity (what was changed and why)
2. Description sections (What, Why, Testing, Risk)
3. Missing implementation details
4. Testing documentation
5. Breaking changes documentation
6. Label accuracy
7. Overall clarity

Format your response as:
ANALYSIS:
[current state assessment]

ISSUES_FOUND:
1. [Issue 1]
2. [Issue 2]
...

SUGGESTED_IMPROVEMENTS:
- Title: [improved title if needed]
- Description: [improved description with key sections]
- Testing: [testing improvements]
- Labels: [updated label list]
- Other: [other recommendations]

DETAILED_SUGGESTIONS:
[explain each suggestion and why it improves the PR]"""

            # Execute agent workflow
            execution = self.execute(task)

            # Parse suggestions
            suggestions = self._parse_improvements(execution)

            return {
                "status": "success",
                "pr_number": pr_number,
                "current": pr_data,
                "suggestions": suggestions,
                "full_analysis": execution
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def apply_improvements(
        self,
        issue_or_pr_number: int,
        new_title: Optional[str] = None,
        new_body: Optional[str] = None,
        is_pr: bool = False
    ) -> Dict[str, Any]:
        """
        Apply improvements to an issue or PR.

        Args:
            issue_or_pr_number: GitHub issue/PR number
            new_title: Improved title
            new_body: Improved description
            is_pr: Whether it's a PR (True) or issue (False)

        Returns:
            Result of update
        """
        try:
            if is_pr:
                result = self.github.update_pull_request(
                    issue_or_pr_number,
                    title=new_title,
                    body=new_body
                )
            else:
                result = self.github.update_issue(
                    issue_or_pr_number,
                    title=new_title,
                    body=new_body
                )

            if result.get("success"):
                return {
                    "status": "success",
                    "message": "✅ Improvements applied successfully!",
                    "ticket_type": "PR" if is_pr else "Issue",
                    "number": issue_or_pr_number
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def add_improvement_comment(
        self,
        issue_or_pr_number: int,
        suggestions: str,
        is_pr: bool = False
    ) -> Dict[str, Any]:
        """
        Add improvement suggestions as a comment (doesn't edit directly).

        Args:
            issue_or_pr_number: GitHub issue/PR number
            suggestions: Suggested improvements text
            is_pr: Whether it's a PR (True) or issue (False)

        Returns:
            Result of comment creation
        """
        try:
            comment_body = f"""### 💡 Improvement Suggestions

{suggestions}

---
*This is a suggestion for improvement. Review and decide if you'd like to apply these changes.*"""

            result = self.github.add_comment(
                issue_or_pr_number,
                comment_body,
                is_pr=is_pr
            )

            if result.get("success"):
                return {
                    "status": "success",
                    "message": "✅ Suggestion comment added!",
                    "comment_url": result.get("url", "")
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _parse_improvements(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        """Parse improvement suggestions from agent response"""
        reflection = execution.get("reflection", {})
        decision = reflection.get("decision", "")

        improvements = {
            "analysis": "",
            "issues": [],
            "suggestions": {
                "title": None,
                "description": None,
                "labels": None,
                "other": None
            },
            "details": ""
        }

        # Extract sections
        lines = decision.split("\n")
        current_section = None

        for line in lines:
            if "ANALYSIS:" in line:
                current_section = "analysis"
                improvements["analysis"] = line.split("ANALYSIS:")[1].strip()
            elif "ISSUES_FOUND:" in line:
                current_section = "issues"
            elif "SUGGESTED_IMPROVEMENTS:" in line:
                current_section = "suggestions"
            elif "DETAILED_SUGGESTIONS:" in line:
                current_section = "details"
            elif current_section == "issues" and line.strip().startswith("-"):
                improvements["issues"].append(line.strip())
            elif current_section == "suggestions":
                if "Title:" in line:
                    improvements["suggestions"]["title"] = line.split("Title:")[
                        1].strip()
                elif "Description:" in line:
                    improvements["suggestions"]["description"] = line.split("Description:")[
                        1].strip()
                elif "Labels:" in line:
                    improvements["suggestions"]["labels"] = line.split("Labels:")[
                        1].strip()
                elif "Other:" in line:
                    improvements["suggestions"]["other"] = line.split("Other:")[
                        1].strip()
            elif current_section == "details" and line.strip():
                improvements["details"] += line + "\n"

        return improvements
