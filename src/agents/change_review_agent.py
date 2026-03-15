"""Change Review Agent - Task 1: Review repository changes"""
from src.agents.base_agent import BaseAgent
from src.tools import GitOps, OllamaClient
from typing import Dict, Any, Optional


class ChangeReviewAgent(BaseAgent):
    """
    Analyzes git changes and decides whether to create Issue, PR, or no action.

    Implements:
    - Planning: Break down change analysis into steps
    - Tool Use: Git operations to extract and analyze diffs
    - Reflection: Categorize, assess risk, and make decision
    - Multi-agent ready: Returns structured decision for coordinator
    """

    def __init__(self):
        super().__init__("ChangeReviewAgent")
        self.git = GitOps()

    def get_system_prompt(self) -> str:
        return """You are a Code Review Agent that analyzes git changes.
Your job is to:
1. Analyze the diff and understand what changed
2. Identify the type of change (feature, bugfix, refactor, docs, test, etc.)
3. Assess risk level (low/medium/high)
4. Identify potential issues or improvements
5. Recommend action: CREATE_ISSUE, CREATE_PR, or NO_ACTION

Be thorough but concise. Focus on actionable insights."""

    def get_available_tools(self) -> str:
        return """AVAILABLE TOOLS:
1. GIT_DIFF - Analyze changes in the repository
2. CATEGORIZE_CHANGE - Determine change type (feature/bugfix/refactor/docs/test)
3. ASSESS_RISK - Evaluate risk level (low/medium/high)
4. IDENTIFY_ISSUES - Find potential problems or improvements
5. RECOMMEND_ACTION - Generate recommendation with reasoning"""

    def review_changes(
        self,
        ref1: Optional[str] = None,
        ref2: Optional[str] = None,
        staged_only: bool = False
    ) -> Dict[str, Any]:
        """
        Review changes in the repository.

        Args:
            ref1: First reference (branch/commit)
            ref2: Second reference (branch/commit)
            staged_only: If True, only review staged changes

        Returns:
            Structured review with recommendation
        """
        try:
            # Get the diff
            if staged_only:
                diff = self.git.get_staged_diff()
            else:
                diff = self.git.get_diff(ref1, ref2)

            if not diff.strip():
                return {
                    "status": "no_changes",
                    "message": "No changes detected",
                    "recommendation": "NO_ACTION"
                }

            # Parse diff to get statistics
            diff_analysis = self.git.parse_diff(diff)

            # Create detailed task for agent
            task = f"""Review these git changes:

FILES CHANGED: {diff_analysis.files_changed}
INSERTIONS: {diff_analysis.insertions}
DELETIONS: {diff_analysis.deletions}

DIFF PREVIEW:
{diff[:3000]}...

Analyze this change and provide:
1. Change type
2. Risk assessment
3. Issues or improvements identified
4. Recommendation (CREATE_ISSUE, CREATE_PR, or NO_ACTION)
5. Suggested issue or PR content if needed"""

            # Execute agent workflow
            execution = self.execute(task)

            # Extract structured recommendation
            recommendation = self._extract_recommendation(execution)

            return {
                "status": "success",
                "diff_analysis": {
                    "files_changed": diff_analysis.files_changed,
                    "insertions": diff_analysis.insertions,
                    "deletions": diff_analysis.deletions,
                },
                "agent_execution": execution,
                "recommendation": recommendation
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _extract_recommendation(self, execution: Dict[str, Any]) -> Dict[str, str]:
        """Extract structured recommendation from agent execution"""
        reflection = execution.get("reflection", {})
        decision = reflection.get("decision", "")

        recommendation = {
            "action": "NO_ACTION",
            "title": "",
            "body": "",
            "risk": "low",
            "type": "unknown"
        }

        # Parse decision for action
        decision_upper = decision.upper()
        if "CREATE_ISSUE" in decision_upper:
            recommendation["action"] = "CREATE_ISSUE"
        elif "CREATE_PR" in decision_upper:
            recommendation["action"] = "CREATE_PR"

        # Extract risk level
        if "HIGH RISK" in decision_upper or "HIGH_RISK" in decision_upper:
            recommendation["risk"] = "high"
        elif "MEDIUM RISK" in decision_upper or "MEDIUM_RISK" in decision_upper:
            recommendation["risk"] = "medium"
        else:
            recommendation["risk"] = "low"

        # Extract change type
        for change_type in ["feature", "bugfix", "refactor", "docs", "test"]:
            if change_type.upper() in decision_upper:
                recommendation["type"] = change_type
                break

        # Use analysis and decision for content
        analysis = reflection.get("analysis", "")
        if analysis and recommendation["action"] != "NO_ACTION":
            recommendation["body"] = analysis + "\n\n" + decision

        return recommendation
