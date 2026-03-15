"""Main CLI interface for the GitHub AI Agent"""
import click
import json
from datetime import datetime
from typing import Optional
from src.agents import ChangeReviewAgent, CoordinatorAgent
from src.tools import GitOps
from src.config import settings


@click.group()
def cli():
    """GitHub AI Agent - Personalized repository management"""
    pass


@cli.command()
@click.option(
    "--ref1",
    default=None,
    help="First reference (branch/commit) for comparison"
)
@click.option(
    "--ref2",
    default=None,
    help="Second reference (branch/commit) for comparison"
)
@click.option(
    "--staged",
    is_flag=True,
    help="Only review staged changes"
)
def review(ref1: Optional[str], ref2: Optional[str], staged: bool):
    """Task 1: Review repository changes and recommend action"""
    click.echo("[*] Starting Change Review Agent...\n")

    try:
        # Validate configuration
        settings.validate()

        # Initialize agent
        agent = ChangeReviewAgent()

        # Review changes
        click.echo("[+] Analyzing git changes...")
        result = agent.review_changes(ref1=ref1, ref2=ref2, staged_only=staged)

        if result["status"] == "error":
            click.secho(f"[!] Error: {result['error']}", fg="red")
            return

        if result["status"] == "no_changes":
            click.secho("[OK] No changes detected", fg="yellow")
            return

        # Display results
        diff_stats = result["diff_analysis"]
        click.secho("\n[+] Diff Statistics:", fg="cyan")
        click.echo(f"  Files changed: {diff_stats['files_changed']}")
        click.echo(f"  Insertions: +{diff_stats['insertions']}")
        click.echo(f"  Deletions: -{diff_stats['deletions']}")

        # Display agent analysis
        click.secho("\n[*] Agent Analysis:", fg="cyan")
        execution = result["agent_execution"]
        reflection = execution.get("reflection", {})
        click.echo(f"  Type: {reflection.get('summary', 'N/A')[:100]}...")
        click.echo(f"  Analysis: {reflection.get('analysis', 'N/A')[:150]}...")

        # Display recommendation
        recommendation = result["recommendation"]
        click.secho("\n[*] Recommendation:", fg="cyan")
        click.echo(f"  Action: {recommendation['action']}")
        click.echo(f"  Risk Level: {recommendation['risk'].upper()}")
        click.echo(f"  Change Type: {recommendation['type']}")

        # Output full result as JSON
        click.secho("\n[*] Full Analysis (JSON):", fg="cyan")
        click.echo(json.dumps({
            "diff_analysis": result["diff_analysis"],
            "recommendation": recommendation,
            "reflection": reflection
        }, indent=2))

    except Exception as e:
        click.secho(f"[!] Error: {str(e)}", fg="red")
        raise


@cli.command()
@click.option(
    "--type",
    "create_type",
    type=click.Choice(["pr", "issue"]),
    default="pr",
    help="Type of ticket to create (pr or issue)"
)
@click.option(
    "--branch",
    default=None,
    help="Branch name for PR (required for pull requests)"
)
@click.option(
    "--ref1",
    default=None,
    help="First ref (branch/commit) for comparison"
)
@click.option(
    "--ref2",
    default=None,
    help="Second ref (branch/commit) for comparison"
)
@click.option(
    "--staged",
    is_flag=True,
    help="Review only staged changes"
)
@click.option(
    "--yes",
    "auto",
    is_flag=True,
    help="Automatically create the ticket without asking"
)
def create(create_type: str, branch: Optional[str], ref1: Optional[str], ref2: Optional[str], staged: bool, auto: bool):
    """Task 2: Review changes and create a GitHub Issue or PR"""
    click.echo("[*] Starting Create workflow...\n")

    try:
        settings.validate()
        coordinator = CoordinatorAgent()

        if create_type == "pr" and not branch:
            try:
                branch = GitOps.get_current_branch()
            except Exception:
                branch = "feature/draft"

        click.echo("[+] Reviewing changes and drafting content...")
        workflow = coordinator.review_and_create_workflow(
            create_type=create_type,
            ref1=ref1,
            ref2=ref2,
            staged_only=staged,
            branch_name=branch,
        )

        if workflow["status"] == "error":
            click.secho(f"[!] Error: {workflow['error']}", fg="red")
            return

        if workflow["status"] == "no_action":
            click.secho("[OK] No changes detected.", fg="yellow")
            return

        draft = workflow.get("draft", {})
        click.secho(f"\n[*] {create_type.upper()} Draft:", fg="cyan")
        click.echo("="*60)
        click.secho(f"Title: {draft.get('title', '')}", fg="yellow")
        click.echo("-"*60)
        click.echo(draft.get("description", "N/A")[:500])
        if len(draft.get("description", "")) > 500:
            click.echo("...\n[Content truncated for preview]")
        click.echo("-"*60)
        if draft.get("labels"):
            click.echo(f"Labels: {', '.join(draft.get('labels', []))}")
        if draft.get("reviewers"):
            click.echo(f"Suggested Reviewers: {', '.join(draft.get('reviewers', []))}")
        click.echo("="*60)

        # Save draft for approval
        draft_data = {
            "type": create_type,
            "draft": draft,
            "branch": branch,
            "ref1": ref1,
            "ref2": ref2,
            "staged": staged,
            "timestamp": str(datetime.now())
        }
        with open(".draft.json", "w") as f:
            json.dump(draft_data, f, indent=2)

        if auto:
            click.echo("[+] Auto-creating ticket...")
            result = coordinator.create_after_review(
                create_type=create_type,
                title=draft.get("title", ""),
                description=draft.get("description", ""),
                branch_name=branch,
                labels=draft.get("labels", [])
            )

            if result["status"] == "success":
                click.secho(f"\n[OK] {create_type.upper()} created successfully!", fg="green")
                click.echo(f"URL: {result['url']}")
                click.echo(f"Number: {result['number']}")
                import os
                os.remove(".draft.json")
            else:
                click.secho(f"\n[!] Failed to create: {result.get('error', 'Unknown')}", fg="red")
                click.secho("[!] You can still approve the draft with 'agent approve --yes'", fg="yellow")
        else:
            click.secho(
                f"\n[OK] Draft saved. Use 'agent approve --yes' to create or 'agent approve --no' to discard.", fg="green"
            )

    except Exception as e:
        click.secho(f"[!] Error: {str(e)}", fg="red")
        raise


@cli.command()
@click.option("--issue", "is_issue", is_flag=True, help="Draft an issue (default: PR)")
@click.argument("instruction")
def draft(is_issue: bool, instruction: str):
    """Task 2a: Draft Issue or PR based on explicit instruction"""
    click.echo("[*] Starting Draft Agent...\n")

    try:
        settings.validate()
        coordinator = CoordinatorAgent()

        ticket_type = "issue" if is_issue else "pr"
        click.echo(
            f"[+] Step 1: Drafting {ticket_type.upper()} from instruction...")

        # Draft based on instruction
        draft_result = coordinator.draft_from_instruction(
            instruction=instruction,
            is_issue=is_issue
        )

        if draft_result["status"] == "error":
            click.secho(f"[!] Error: {draft_result['error']}", fg="red")
            return

        # Display draft
        draft = draft_result["draft"]
        click.secho(f"\n[*] {ticket_type.upper()} Draft:", fg="cyan")
        click.echo("="*60)
        click.secho(f"Title: {draft['title']}", fg="yellow")
        click.echo("-"*60)
        click.echo(draft.get("description", "N/A")[:500])
        if len(draft.get("description", "")) > 500:
            click.echo("...\n[Content truncated for preview]")
        click.echo("-"*60)
        if draft.get("labels"):
            click.echo(f"Labels: {', '.join(draft['labels'])}")
        if draft.get("reviewers"):
            click.echo(f"Suggested Reviewers: {', '.join(draft['reviewers'])}")
        click.echo("="*60)

        # Save draft for approval
        draft_data = {
            "type": ticket_type,
            "draft": draft,
            "instruction": instruction,
            "timestamp": str(datetime.now())
        }
        with open(".draft.json", "w") as f:
            json.dump(draft_data, f, indent=2)

        click.secho(
            f"\n[OK] Draft saved. Use 'agent approve --yes' to create or 'agent approve --no' to discard.", fg="green")

    except Exception as e:
        click.secho(f"[!] Error: {str(e)}", fg="red")
        raise


@cli.command()
@click.option("--yes", "approve", is_flag=True, help="Approve and create the draft")
@click.option("--no", "reject", is_flag=True, help="Reject and discard the draft")
def approve(approve: bool, reject: bool):
    """Task 2b: Approve or reject the current draft"""
    click.echo("[*] Checking draft status...\n")

    try:
        if not approve and not reject:
            click.secho("[!] Must specify --yes or --no", fg="red")
            return

        if approve and reject:
            click.secho("[!] Cannot specify both --yes and --no", fg="red")
            return

        # Load draft
        try:
            with open(".draft.json", "r") as f:
                draft_data = json.load(f)
        except FileNotFoundError:
            click.secho(
                "[!] No draft found. Use 'agent draft' first.", fg="red")
            return

        ticket_type = draft_data["type"]
        draft = draft_data["draft"]

        if approve:
            click.echo("[OK] Approved! Creating...")
            settings.validate()
            coordinator = CoordinatorAgent()

            if ticket_type == "issue":
                result = coordinator.create_issue_from_draft(draft)
            else:
                result = coordinator.create_pr_from_draft(draft)

            if result["status"] == "success":
                click.secho(
                    f"\n[OK] {ticket_type.upper()} created successfully!", fg="green")
                click.echo(f"URL: {result['url']}")
                click.echo(f"Number: {result['number']}")
                # Clean up draft
                import os
                os.remove(".draft.json")
            else:
                click.secho(f"\n[!] Failed to create: {result.get('error')}", fg="red")
                click.secho("[DEBUG] Full result:")
                click.echo(json.dumps(result, indent=2))
        else:
            click.secho("\n[X] Rejected. Draft discarded.", fg="yellow")
            # Clean up draft
            import os
            os.remove(".draft.json")

    except Exception as e:
        click.secho(f"[!] Error: {str(e)}", fg="red")
        raise


@cli.command()
@click.argument("number", type=int)
@click.option("--pr", "is_pr", is_flag=True, help="This is a PR (default: issue)")
@click.option("--as-comment", is_flag=True, help="Add suggestions as comment (don't edit)")
def improve(number: int, is_pr: bool, as_comment: bool):
    """Task 3: Analyze and improve existing GitHub Issues or PRs"""
    click.echo("[*] Starting Issue/PR Improver Agent...\n")

    try:
        settings.validate()
        coordinator = CoordinatorAgent()

        ticket_type = "PR" if is_pr else "Issue"
        click.echo(f"[+] Step 1: Analyzing {ticket_type} #{number}...")

        # Start improvement workflow
        workflow = coordinator.improve_ticket_workflow(
            ticket_number=number,
            is_pr=is_pr,
            apply_suggestions=False
        )

        if workflow["status"] == "error":
            click.secho(f"[!] Error: {workflow['error']}", fg="red")
            return

        # Helper to safely echo text in terminals with limited unicode support
        def safe_echo(text: str):
            try:
                click.echo(text)
            except UnicodeEncodeError:
                click.echo(text.encode("ascii", errors="replace").decode("ascii"))

        # Display workflow status
        status_info = coordinator.get_workflow_status(workflow)
        click.secho("\n[*] Workflow Status:", fg="cyan")
        safe_echo(status_info.get("log", ""))

        # Display current content
        current = workflow["improvement_result"]["current"]
        click.secho(f"\n[-] Current {ticket_type}:", fg="cyan")
        click.echo("="*60)
        click.secho(f"Title: {current['title']}", fg="blue")
        click.echo("-"*60)
        click.echo(current.get("body", "N/A")[:400])
        click.echo("="*60)

        # Display suggestions
        suggestions = workflow["improvement_result"]["suggestions"]
        click.secho(f"\n[*] Improvement Suggestions:", fg="green")
        click.echo("="*60)

        if suggestions["issues"]:
            safe_echo("Issues found:")
            for issue in suggestions["issues"]:
                safe_echo(f"  {issue}")

        safe_echo("\nRecommendations:")
        if suggestions["suggestions"].get("title"):
            click.secho(
                f"  Title: {suggestions['suggestions']['title']}", fg="yellow")
        if suggestions["suggestions"].get("description"):
            desc = suggestions['suggestions']['description']
            safe_echo(f"  Description improvements: {desc[:150]}...")
        if suggestions["suggestions"].get("labels"):
            safe_echo(f"  Labels: {suggestions['suggestions']['labels']}")

        safe_echo("\nDetailed explanation:")
        safe_echo(suggestions["details"][:300])

        click.echo("="*60)

        # Get user decision
        click.echo()
        action = click.prompt(
            "What would you like to do?",
            type=click.Choice(["apply", "comment", "ignore"]),
            default="comment"
        )

        if action == "apply":
            click.echo("[*] Applying improvements to title and description...")
            result = coordinator.apply_ticket_improvements(
                ticket_number=number,
                new_title=suggestions["suggestions"].get("title"),
                new_description=suggestions["suggestions"].get("description"),
                as_comment=False,
                is_pr=is_pr
            )

            if result["status"] == "success":
                click.secho(f"\n[OK] {result['message']}", fg="green")
            else:
                click.secho(f"\n[!] Failed: {result['error']}", fg="red")

        elif action == "comment":
            click.echo("[*] Adding suggestions as a comment...")
            result = coordinator.apply_ticket_improvements(
                ticket_number=number,
                new_title=suggestions["suggestions"].get("title"),
                new_description=suggestions["suggestions"].get("description"),
                as_comment=True,
                is_pr=is_pr
            )

            if result["status"] == "success":
                click.secho(f"\n[OK] {result['message']}", fg="green")
                click.echo(f"Comment URL: {result.get('comment_url', 'N/A')}")
            else:
                click.secho(f"\n[!] Failed: {result['error']}", fg="red")

        else:
            click.secho("\n[OK] No changes made.", fg="yellow")

    except Exception as e:
        click.secho(f"[!] Error: {str(e)}", fg="red")
        raise


@cli.command()
def status():
    """Check system status and connectivity"""
    click.echo("[*] Checking system status...\n")

    try:
        # Check Ollama
        from src.tools import OllamaClient
        ollama = OllamaClient()
        if ollama.check_health():
            click.secho("[OK] Ollama: Connected", fg="green")
        else:
            click.secho("[!] Ollama: Not available", fg="red")

        # Check Git
        try:
            branch = GitOps.get_current_branch()
            click.secho(f"[OK] Git: Ready (branch: {branch})", fg="green")
        except:
            click.secho("[!] Git: Not available", fg="red")

        # Check GitHub
        try:
            settings.validate()
            click.secho("[OK] GitHub: Configured", fg="green")
        except:
            click.secho("[!] GitHub: Not configured", fg="red")

    except Exception as e:
        click.secho(f"[!] Error: {str(e)}", fg="red")


@cli.command()
def init():
    """Initialize agent configuration"""
    click.echo("[*] GitHub AI Agent Setup\n")

    github_pat = click.prompt("GitHub Personal Access Token")
    github_owner = click.prompt("GitHub username/org")
    github_repo = click.prompt("Repository name")
    ollama_url = click.prompt(
        "Ollama API URL", default="http://localhost:11434")
    ollama_model = click.prompt("Ollama model name", default="ministral-3:3b")

    env_content = f"""# GitHub Configuration
GITHUB_PAT={github_pat}
GITHUB_REPO_OWNER={github_owner}
GITHUB_REPO_NAME={github_repo}

# Ollama Configuration
OLLAMA_API_URL={ollama_url}
OLLAMA_MODEL={ollama_model}

# Agent Configuration
AGENT_MAX_ITERATIONS=5
AGENT_TEMPERATURE=0.3
"""

    try:
        with open(".env", "w") as f:
            f.write(env_content)
        click.secho("[OK] Configuration saved to .env", fg="green")
    except Exception as e:
        click.secho(f"[!] Error saving config: {str(e)}", fg="red")


if __name__ == "__main__":
    cli()
