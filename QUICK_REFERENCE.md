# 🚀 Quick Reference Card

## Installation

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python agent.py init
```

## Commands

### Task 1: Review

```bash
python agent.py review               # Review current changes
python agent.py review --staged      # Review staged only
python agent.py review --ref1 main --ref2 HEAD  # Compare commits
```

### Task 2: Create

```bash
python agent.py create --type pr --branch feat/xyz   # Review changes, draft + save PR (use approve to create)
python agent.py create --type pr --branch feat/xyz --yes   # Review changes, draft + immediately create PR
python agent.py create --type issue                  # Review changes, draft + save Issue (use approve to create)
python agent.py create --type issue --yes             # Review changes, draft + immediately create Issue
```

### Task 3: Improve

```bash
python agent.py improve 42            # Improve issue
python agent.py improve 123 --pr      # Improve PR
python agent.py improve 42 --as-comment  # As comment
```

### System

```bash
python agent.py status           # Check system health
python agent.py init             # Initialize/reconfigure
```

## Project Layout

```
src/
├── agents/          # AI agents (base + specialized)
├── tools/           # Git, GitHub, Ollama interfaces
├── config/          # Settings and configuration
└── main.py          # CLI commands
```

## Environment (.env)

```env
GITHUB_PAT=your_token
GITHUB_REPO_OWNER=username
GITHUB_REPO_NAME=repo
OLLAMA_API_URL=http://localhost:11434
# Use the exact model name shown by `ollama list`, e.g. ministral-3:3b
OLLAMA_MODEL=ministral-3:3b
```

## Execution Flow

```
User Input
  ↓
[PLANNING] break into steps
  ↓
[TOOL USE] git/ollama/github
  ↓
[REFLECTION] analyze results
  ↓
Human Approval
```

## Key Files

- `agent.py` - Entry point
- `src/agents/base_agent.py` - Planning + Tool Use + Reflection
- `src/agents/change_review_agent.py` - Task 1: Review
- `src/agents/issue_pr_creator_agent.py` - Task 2: Create
- `src/agents/issue_pr_improver_agent.py` - Task 3: Improve
- `src/agents/coordinator_agent.py` - Multi-agent orchestration
- `src/tools/` - Git, GitHub, Ollama integrations

## Troubleshooting

- `Ollama not connected?` → Run `ollama serve`
- `GitHub error?` → Check PAT token in .env
- `Git error?` → Ensure you're in a git repo
- `Import error?` → Activate venv first

---

**Status: ALL TASKS COMPLETE** ✅

- Task 1: Review Changes ✅
- Task 2: Create Issues/PRs ✅
- Task 3: Improve Tickets ✅
- All 4 Patterns: Complete ✅

**Ready for**: Production use and extension!
