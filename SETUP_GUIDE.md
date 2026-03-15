# Phase 1 Setup Guide

## What We Built

A complete Python CLI agent system with:

✅ **Base Agent Class** - Implements Planning, Tool Use, Reflection patterns
✅ **Change Review Agent** - Analyzes git diffs and recommends actions
✅ **Git Operations Module** - Analyzes diffs, tracks changes
✅ **GitHub API Integration** - Create/update issues and PRs
✅ **Ollama LLM Integration** - Uses local Ministral 3B model
✅ **Click CLI Interface** - User-friendly command system
✅ **Configuration Management** - Environment-based setup

## File Structure

```
Personalized-Github-AI-Agent/
├── agent.py                    # Entry point
├── requirements.txt            # Dependencies
├── .env.example               # Configuration template
├── README.md                  # Full documentation
├── SETUP_GUIDE.md            # This file
│
└── src/
    ├── main.py               # CLI commands
    ├── __init__.py
    │
    ├── agents/
    │   ├── base_agent.py     # Planning + Tool Use + Reflection
    │   ├── change_review_agent.py  # Task 1 - Review changes
    │   └── __init__.py
    │
    ├── tools/
    │   ├── git_ops.py        # Git diff analysis
    │   ├── github_ops.py     # GitHub API wrapper
    │   ├── ollama_client.py  # Ollama LLM client
    │   └── __init__.py
    │
    └── config/
        ├── settings.py       # Settings management
        └── __init__.py
```

## Installation Steps

### Step 1: Create Python Virtual Environment

```bash
cd "c:\Users\hjros\HJR Projecs\Personalized GitHub Agent\Personalized-Github-AI-Agent"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:

- `click`: CLI framework
- `requests`: HTTP requests
- `PyGithub`: GitHub API
- `python-dotenv`: Environment configuration
- `ollama`: Ollama SDK
- `pydantic`: Data validation

### Step 3: Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Or use the interactive setup:

```bash
python agent.py init
```

Edit `.env` with your values:

```env
GITHUB_PAT=ghp_xxxxxxxxxxxxx
GITHUB_REPO_OWNER=your_username
GITHUB_REPO_NAME=your_repo

OLLAMA_API_URL=http://localhost:11434
# Use the exact model name shown by `ollama list`, e.g. ministral-3:3b
OLLAMA_MODEL=ministral-3:3b

AGENT_TEMPERATURE=0.3
AGENT_MAX_ITERATIONS=5
```

### Step 4: Verify Setup

```bash
python agent.py status
```

Expected output:

```
✓ Ollama: Connected
✓ Git: Ready (branch: main)
✓ GitHub: Configured
```

## Design Patterns Explained

### 1. Planning Pattern

```python
# Agent breaks task into steps
plan = agent.plan(task)
# Output: "1. Extract diff\n2. Analyze changes\n3. Assess risk..."
```

### 2. Tool Use Pattern

```python
# Agent calls available tools
- GitOps: git diff, parse changes
- GitHubOps: create issue/PR
- OllamaClient: LLM inference
```

### 3. Reflection Pattern

```python
# Agent analyzes results
reflection = agent.reflect(task, results)
# Output: {"summary": "...", "analysis": "...", "decision": "..."}
```

### 4. Multi-Agent Pattern

```python
# Multiple agents work on different tasks
ChangeReviewAgent    -> Analyzes changes
IssueCreatorAgent    -> Creates tickets (Phase 2)
IssueImproverAgent   -> Improves existing (Phase 3)
CoordinatorAgent     -> Orchestrates all (Phase 4)
```

## Usage Examples

### Example 1: Review Current Changes

```bash
python agent.py review
```

Shows:

- Diff statistics (files, insertions, deletions)
- Agent analysis (type, risk, issues)
- Recommendation (CREATE_ISSUE, CREATE_PR, NO_ACTION)
- Asks for human approval

### Example 2: Review Specific Commit Range

```bash
python agent.py review --ref1 main --ref2 HEAD
```

Analyzes differences between main and current branch.

### Example 3: Review Only Staged Changes

```bash
python agent.py review --staged
```

Analyzes only git-staged changes (before commit).

### Example 4: Auto-Approve (Development Only)

```bash
python agent.py review --approve
```

**Warning**: Skips human approval. Use only for testing.

## Agent Execution Flow

```
User runs: python agent.py review
                    ↓
        [CLI Interface]
                    ↓
        Initialize ChangeReviewAgent
                    ↓
        ┌───────────────────────────┐
        │   PHASE 1: PLANNING       │
        │ Break analysis into steps │
        └────────────┬──────────────┘
                     ↓
        ┌───────────────────────────┐
        │  PHASE 2: TOOL USE        │
        │ Execute each step using:  │
        │ - GitOps.get_diff()       │
        │ - OllamaClient.generate() │
        └────────────┬──────────────┘
                     ↓
        ┌───────────────────────────┐
        │  PHASE 3: REFLECTION      │
        │ Analyze and decide:       │
        │ - Categorize change       │
        │ - Assess risk             │
        │ - Make recommendation     │
        └────────────┬──────────────┘
                     ↓
        ┌───────────────────────────┐
        │  HUMAN APPROVAL  🙋       │
        │  Create issue/PR or skip  │
        └───────────────────────────┘
```

## Key Classes and Methods

### BaseAgent

```python
class BaseAgent(ABC):
    def plan(task: str) -> str
    def execute_step(step: str, context: str) -> str
    def reflect(task: str, results: List[str]) -> Dict
    def execute(task: str) -> Dict
```

### ChangeReviewAgent

```python
class ChangeReviewAgent(BaseAgent):
    def review_changes(
        ref1: Optional[str],
        ref2: Optional[str],
        staged_only: bool
    ) -> Dict
```

### GitOps

```python
class GitOps:
    @staticmethod
    def get_diff(ref1, ref2) -> str
    @staticmethod
    def get_staged_diff() -> str
    @staticmethod
    def parse_diff(diff_text: str) -> DiffAnalysis
```

### OllamaClient

```python
class OllamaClient:
    def generate(prompt: str, temperature: float) -> Dict
    def chat(messages: List, temperature: float) -> Dict
    def check_health() -> bool
```

## Testing the Agent

### Test 1: System Status Check

```bash
python agent.py status
```

### Test 2: Simulate a Change Review

1. Make changes to a local file:

   ```bash
   echo "# Test" > test.md
   git add test.md
   ```

2. Review staged changes:

   ```bash
   python agent.py review --staged
   ```

3. Agent will:
   - Extract and analyze the diff
   - Categorize as "documentation"
   - Assess risk as "low"
   - Recommend "CREATE_PR"
   - Ask for human approval

### Test 3: Configuration Test

```bash
# This will fail if config is missing
python agent.py review --ref1 HEAD~1 --ref2 HEAD
```

## Extending Phase 1

If you want to test Phase 1 enhancements:

### Add Custom Tools

Create new tool classes in `src/tools/`

### Improve LLM Prompts

Edit system prompts in agent classes

### Add Analysis Features

Extend `DiffAnalysis` dataclass with more metrics

## Next: Phase 2 & 3

When ready, we'll implement:

**Phase 2: Issue/PR Creator Agent**

- Takes review recommendation
- Drafts detailed content
- Gets user confirmation
- Creates GitHub ticket

**Phase 3: Issue/PR Improver Agent**

- Analyzes existing issues/PRs
- Suggests improvements
- Proposes content rewrites

**Phase 4: Coordinator Agent**

- Orchestrates all agents
- Handles complex workflows
- Manages feedback loops

## Troubleshooting

### "Ollama connection refused"

```bash
# Start Ollama
ollama serve

# In another terminal
ollama list  # Verify model
```

### "GitHub PAT invalid"

```bash
# Check token scopes
# Required: repo, issues
# Create new at: https://github.com/settings/tokens
```

### "Module not found" errors

```bash
# Verify venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall deps
pip install -r requirements.txt
```

### "Git is not a git repository"

```bash
# Ensure you're in a git repo
cd <your-repo-path>
git status  # Should work
```

## Performance Notes

- **First run**: May take 5-10s (LLM model loading)
- **Subsequent runs**: 2-5s (depends on diff size)
- **Large diffs**: May need to adjust timeout in code
- **Temperature**: 0.3 = deterministic; 0.5-1.0 = creative

## Environment Variables Reference

```env
# GitHub (Required)
GITHUB_PAT              # GitHub Personal Access Token
GITHUB_REPO_OWNER       # GitHub username/org
GITHUB_REPO_NAME        # Repository name

# Ollama (Defaults provided)
OLLAMA_API_URL          # Default: http://localhost:11434
OLLAMA_MODEL            # Default: ministral-3:3b (run `ollama list` to see installed models)

# Agent Behavior
AGENT_MAX_ITERATIONS    # Default: 5 (max planning steps)
AGENT_TEMPERATURE       # Default: 0.3 (0=deterministic, 1=random)
```

## Success Checklist

- [ ] Python venv created and activated
- [ ] Dependencies installed (pip check shows no errors)
- [ ] `.env` file configured with GitHub PAT
- [ ] Ollama running with ministral-3:3b model (or your chosen model from `ollama list`)
- [ ] `python agent.py status` shows all green
- [ ] `python agent.py review` works on test changes
- [ ] Git repo initialized in project folder

## Next Steps

1. ✅ Phase 1 complete - Run `python agent.py review`
2. 🔄 Phase 2 upcoming - Issue/PR creation
3. 📋 Phase 3 upcoming - Issue/PR improvement
4. 🤖 Phase 4 upcoming - Multi-agent coordination

---

**You're all set!** Run `python agent.py review` to see it in action. 🚀
