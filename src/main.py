"""Main CLI interface for the GitHub AI Agent"""
import click
import json
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
@click.option(
    "--approve",
    is_flag=True,
    help="Auto-approve and create issue/PR (use with caution)"
)
def review(ref1: Optional[str], ref2: Optional[str], staged: bool, approve: bool):
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

        # Ask for user approval if not auto-approved
        if recommendation["action"] != "NO_ACTION" and not approve:
            click.echo("\n" + "="*60)
            click.secho("Human Approval Required", fg="yellow", bold=True)
            click.echo("="*60)

            if click.confirm("Create this issue/PR?"):
                click.secho(
                    "\n[OK] Approved! Proceeding with creation...", fg="green")
                # TODO: Call create_issue or create_pull_request
            else:
                click.secho("\n[X] Rejected. No action taken.", fg="yellow")
                return

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
@click.option("--ref1", default=None, help="First reference for comparison")
@click.option("--ref2", default=None, help="Second reference for comparison")
@click.option("--type", "create_type", type=click.Choice(["issue", "pr"]), default="pr", help="Create issue or PR")
@click.option("--branch", default=None, help="Branch name (required for PR)")
def create(ref1: Optional[str], ref2: Optional[str], create_type: str, branch: Optional[str]):
    """Task 2: Review changes and create GitHub Issue or PR with approval"""
    click.echo("[*] Starting Review + Create Workflow...\n")

    try:
        settings.validate()
        coordinator = CoordinatorAgent()

        # Step 1: Review and get draft
        click.echo("[+] Step 1: Analyzing changes...")
        workflow = coordinator.review_and_create_workflow(
            create_type=create_type,
            ref1=ref1,
            ref2=ref2,
            branch_name=branch
        )

        if workflow["status"] == "error":
            click.secho(f"[!] Error: {workflow['error']}", fg="red")
            return

        if workflow["status"] == "no_action":
            click.secho("[OK] No changes detected", fg="yellow")
            return

        # Display workflow status
        status_info = coordinator.get_workflow_status(workflow)
        click.secho("\n[*] Workflow Status:", fg="cyan")
        click.echo(status_info["log"])

        # Display draft content
        draft = workflow["draft"]
        click.secho(f"\n[*] {create_type.upper()} Draft:", fg="cyan")
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

        # Get approval
        click.echo()
        if click.confirm(f"Create this {create_type}?"):
            click.echo("[OK] Approved! Creating...")

            # Create the ticket
            result = coordinator.create_after_review(
                create_type=create_type,
                title=draft["title"],
                description=draft["description"],
                branch_name=branch,
                labels=draft.get("labels")
            )

            if result["status"] == "success":
                click.secho(
                    f"\n[OK] {create_type.upper()} created successfully!", fg="green")
                click.echo(f"URL: {result['url']}")
                click.echo(f"Number: {result['number']}")
            else:
                click.secho(
                    f"\n[!] Failed to create: {result['error']}", fg="red")
        else:
            click.secho("\n[X] Cancelled.", fg="yellow")

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

        # Display workflow status
        status_info = coordinator.get_workflow_status(workflow)
        click.secho("\n[*] Workflow Status:", fg="cyan")
        click.echo(status_info["log"])

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
            click.echo("Issues found:")
            for issue in suggestions["issues"]:
                click.echo(f"  {issue}")

        click.echo("\nRecommendations:")
        if suggestions["suggestions"].get("title"):
            click.secho(
                f"  Title: {suggestions['suggestions']['title']}", fg="yellow")
        if suggestions["suggestions"].get("description"):
            desc = suggestions['suggestions']['description']
            click.echo(f"  Description improvements: {desc[:150]}...")
        if suggestions["suggestions"].get("labels"):
            click.echo(f"  Labels: {suggestions['suggestions']['labels']}")

        click.echo("\nDetailed explanation:")
        click.echo(suggestions["details"][:300])
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
    ollama_model = click.prompt("Ollama model name", default="ministral")

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
