"""Coordinator Agent - Orchestrates multi-agent workflows and complex tasks"""
from src.agents.base_agent import BaseAgent
from src.agents.change_review_agent import ChangeReviewAgent
from src.agents.issue_pr_creator_agent import IssuePRCreatorAgent
from src.agents.issue_pr_improver_agent import IssueImproverAgent
from src.tools import GitOps
from typing import Dict, Any, Optional, List


class CoordinatorAgent(BaseAgent):
    """
    Orchestrates multi-agent workflows.

    Implements:
    - Planning: Design workflow steps
    - Tool Use: Delegate to specialized agents
    - Reflection: Evaluate workflow results
    - Multi-agent: Composes all agents into workflows
    """

    def __init__(self):
        super().__init__("CoordinatorAgent", model="ministral")
        self.change_reviewer = ChangeReviewAgent()
        self.pr_creator = IssuePRCreatorAgent()
        self.pr_improver = IssueImproverAgent()
        self.git = GitOps()

    def get_system_prompt(self) -> str:
        return """You are a Coordinator Agent that orchestrates complex workflows.
Your job is to:
1. Plan multi-step processes
2. Delegate to specialized agents
3. Handle results and decisions
4. Provide status updates
5. Manage error handling and retries

Coordinate agents efficiently and keep user informed."""

    def get_available_tools(self) -> str:
        return """AVAILABLE AGENTS TO DELEGATE:
1. ChangeReviewAgent - Analyze git changes
2. IssuePRCreatorAgent - Draft and create issues/PRs
3. IssueImproverAgent - Improve existing tickets

WORKFLOW PATTERNS:
- Review Only - Just analyze changes
- Review → Create - Analyze then create
- Review → Create → Improve - Full pipeline
- Single Improve - Improve one ticket"""

    def review_and_create_workflow(
        self,
        create_type: str = "pr",
        ref1: Optional[str] = None,
        ref2: Optional[str] = None,
        branch_name: Optional[str] = None,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Full workflow: Review changes → Create Issue or PR

        Args:
            create_type: "issue" or "pr"
            ref1: First ref for comparison
            ref2: Second ref for comparison
            branch_name: Branch for PR (required if create_type="pr")
            auto_approve: Skip approval prompts

        Returns:
            Workflow results from both agents
        """
        workflow_log = []

        try:
            # Step 1: Review changes
            workflow_log.append(
                "Step 1: Analyzing changes with ChangeReviewAgent...")
            review_result = self.change_reviewer.review_changes(
                ref1=ref1,
                ref2=ref2,
                staged_only=False
            )

            if review_result["status"] == "error":
                return {
                    "status": "error",
                    "step": 1,
                    "error": review_result["error"],
                    "workflow_log": workflow_log
                }

            if review_result["status"] == "no_changes":
                return {
                    "status": "no_action",
                    "message": "No changes detected",
                    "workflow_log": workflow_log
                }

            workflow_log.append(f"✓ Change review complete")

            # Extract recommendation
            recommendation = review_result.get("recommendation", {})
            change_type = recommendation.get("type", "unknown")
            risk_level = recommendation.get("risk", "low")
            analysis = recommendation.get("body", "")
            summary = review_result["agent_execution"]["reflection"].get(
                "summary", "")

            diff_stats = review_result["diff_analysis"]

            # Step 2: Draft content
            workflow_log.append(
                f"Step 2: Creating {create_type.upper()} with IssuePRCreatorAgent...")

            if create_type == "pr":
                draft = self.pr_creator.draft_pull_request(
                    branch_name=branch_name or "feature",
                    change_type=change_type,
                    summary=summary,
                    analysis=analysis,
                    risk_level=risk_level,
                    files_changed=diff_stats["files_changed"],
                    insertions=diff_stats["insertions"],
                    deletions=diff_stats["deletions"]
                )
            else:  # issue
                draft = self.pr_creator.draft_issue(
                    change_type=change_type,
                    summary=summary,
                    analysis=analysis,
                    risk_level=risk_level
                )

            workflow_log.append(f"✓ Content drafted")

            # Step 3: Return workflow status
            return {
                "status": "success",
                "workflow": "review_and_create",
                "create_type": create_type,
                "review_result": review_result,
                "draft": draft,
                "workflow_log": workflow_log,
                "ready_to_create": True,
                "next_step": f"Review and approve {create_type} creation"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "workflow_log": workflow_log
            }

    def create_after_review(
        self,
        create_type: str,
        title: str,
        description: str,
        branch_name: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create issue or PR after review workflow.

        Args:
            create_type: "issue" or "pr"
            title: Approved title
            description: Approved description
            branch_name: Branch for PR
            labels: Labels to apply

        Returns:
            Creation result with GitHub URL
        """
        try:
            if create_type == "pr":
                if not branch_name:
                    return {"status": "error", "error": "Branch name required for PR"}

                result = self.pr_creator.create_pull_request(
                    title=title,
                    description=description,
                    head_branch=branch_name,
                    labels=labels
                )
            else:  # issue
                result = self.pr_creator.create_issue(
                    title=title,
                    description=description,
                    labels=labels
                )

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def improve_ticket_workflow(
        self,
        ticket_number: int,
        is_pr: bool = False,
        apply_suggestions: bool = False
    ) -> Dict[str, Any]:
        """
        Workflow: Analyze existing ticket → Suggest improvements

        Args:
            ticket_number: GitHub issue or PR number
            is_pr: True for PR, False for issue
            apply_suggestions: Automatically apply suggestions (dangerous!)

        Returns:
            Analysis with suggestions
        """
        workflow_log = []

        try:
            workflow_log.append(
                "Step 1: Analyzing ticket with IssueImproverAgent...")

            if is_pr:
                improvement_result = self.pr_improver.improve_pull_request(
                    ticket_number)
            else:
                improvement_result = self.pr_improver.improve_issue(
                    ticket_number)

            if improvement_result["status"] == "error":
                return {
                    "status": "error",
                    "error": improvement_result["error"],
                    "workflow_log": workflow_log
                }

            workflow_log.append("✓ Analysis complete")

            # Step 2: Optionally apply improvements
            if apply_suggestions:
                workflow_log.append("Step 2: Applying improvements...")
                suggestions = improvement_result["suggestions"]

                apply_result = self.pr_improver.apply_improvements(
                    ticket_number,
                    new_title=suggestions["suggestions"].get("title"),
                    new_body=suggestions["suggestions"].get("description"),
                    is_pr=is_pr
                )

                if apply_result["status"] == "success":
                    workflow_log.append("✓ Improvements applied")
                else:
                    workflow_log.append(
                        f"✗ Failed to apply: {apply_result['error']}")

            return {
                "status": "success",
                "workflow": "improve_ticket",
                "ticket_type": "PR" if is_pr else "Issue",
                "ticket_number": ticket_number,
                "improvement_result": improvement_result,
                "workflow_log": workflow_log,
                "ready_to_apply": not apply_suggestions
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "workflow_log": workflow_log
            }

    def apply_ticket_improvements(
        self,
        ticket_number: int,
        new_title: Optional[str] = None,
        new_description: Optional[str] = None,
        as_comment: bool = False,
        is_pr: bool = False
    ) -> Dict[str, Any]:
        """
        Apply improvements to a ticket (after review workflow).

        Args:
            ticket_number: GitHub issue or PR number
            new_title: Improved title
            new_description: Improved description
            as_comment: Add as comment instead of editing
            is_pr: True for PR, False for issue

        Returns:
            Application result
        """
        try:
            if as_comment:
                suggestions = f"**Suggested Title:** {new_title or 'No change'}\n\n"
                suggestions += f"**Suggested Description:**\n{new_description or 'No change'}"

                result = self.pr_improver.add_improvement_comment(
                    ticket_number,
                    suggestions,
                    is_pr=is_pr
                )
            else:
                result = self.pr_improver.apply_improvements(
                    ticket_number,
                    new_title=new_title,
                    new_body=new_description,
                    is_pr=is_pr
                )

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_workflow_status(self, workflow_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract human-readable workflow status.

        Args:
            workflow_data: Workflow result

        Returns:
            Status dictionary
        """
        return {
            "status": workflow_data.get("status", "unknown"),
            "workflow": workflow_data.get("workflow", "N/A"),
            "log": "\n".join(workflow_data.get("workflow_log", [])),
            "ready_to_execute": workflow_data.get("ready_to_create", False)
            or workflow_data.get("ready_to_apply", False)
        }
