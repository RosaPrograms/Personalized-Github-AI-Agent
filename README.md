# Personalized GitHub AI Agent

A multi-agent AI system that reviews your repository changes, drafts GitHub Issues/PRs with human approval, and improves existing Issues/PRs using local Ollama LLM.

## ✨ Features

### Phase 1 - Complete ✓

- **Change Review Agent**: Analyzes git diffs and recommends actions
- **Planning Pattern**: Breaks tasks into logical steps
- **Tool Use Pattern**: Git + GitHub API + Ollama LLM
- **Reflection Pattern**: Analyzes and makes decisions
- **Human Approval**: CLI interface for approval workflow
- **Local LLM**: Uses Ministral 3B via Ollama

### Phase 2 - Complete ✓

- **Issue/PR Creator Agent**: Drafts detailed content from reviews
- **Workflow Integration**: Review → Create pipelines
- **Smart Drafting**: AI-generated titles and descriptions
- **Label Suggestions**: Automatic label recommendations
- **Human-in-the-Loop**: Approve before creation

### Phase 3 - Complete ✓

- **Issue/PR Improver Agent**: Analyzes existing tickets
- **Improvement Suggestions**: Identifies gaps and issues
- **Content Rewrites**: Proposes better titles/descriptions
- **Strategic Options**: Apply directly or add as comments
- **Non-Destructive**: Suggests before modifying

### Phase 4 - Complete ✓

- **Coordinator Agent**: Orchestrates multi-agent workflows
- **Workflow Patterns**: Review-only, Review→Create, Review→Create→Improve
- **Error Handling**: Graceful degradation
- **Workflow Logging**: Track multi-step processes

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Ollama with Ministral 3B installed
- GitHub Personal Access Token (PAT)

### Setup (3 Steps)

```bash
# 1. Install dependencies
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt

# 2. Configure
python agent.py init

# 3. Review changes
python agent.py review
```

## 📋 All Commands

### Task 1: Review Changes

```bash
# Review current branch changes
python agent.py review

# Review staged changes only
python agent.py review --staged

# Compare specific commits
python agent.py review --ref1 main --ref2 HEAD
```

### Task 2: Create Issues or PRs

```bash
# Create PR from changes (with review workflow)
python agent.py create --type pr --branch feature/my-feature

# Create PR from changes and create immediately (no approval step)
python agent.py create --type pr --branch feature/my-feature --yes

# Create Issue from changes
python agent.py create --type issue

# Create Issue from changes and create immediately
python agent.py create --type issue --yes

# Analyze specific commit range
python agent.py create --type pr --ref1 main --ref2 HEAD
```

### Task 3: Improve Existing Tickets

```bash
# Improve an issue
python agent.py improve 42

# Improve a pull request (add --pr flag)
python agent.py improve 123 --pr

# Add suggestions as comment instead of editing
python agent.py improve 42 --as-comment

# Improve PR with comment
python agent.py improve 123 --pr --as-comment
```

### System Management

```bash
# Check system status
python agent.py status

# Initialize/reconfigure
python agent.py init
```

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      CLI Interface (Click)          │
│ review / create / improve / status  │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────────┐
    ▼          ▼              ▼
┌────────┐ ┌────────┐ ┌────────┐
│Review  │ │Create  │ │Improve │
│ Agent  │ │ Agent  │ │ Agent  │
└────────┘ └────────┘ └────────┘
    │          │          │
    └──────────┼──────────┘
               ▼
    ┌──────────────────────┐
    │ CoordinatorAgent     │
    │ (orchestrates flow)  │
    └────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ▼          ▼          ▼          ▼
  Git Ops  GitHub API  Ollama LLM  Utils
```

## 📚 Design Patterns

### 1. Planning Pattern

Agents decompose tasks into steps before execution

### 2. Tool Use Pattern

Integrated tools: Git operations, GitHub API, Ollama LLM

### 3. Reflection Pattern

Analyze results, assess outcomes, make decisions

### 4. Multi-Agent Pattern

Modular agents, coordinator orchestration (future)

## 🔧 Configuration

Create `.env` file:

```env
GITHUB_PAT=your_token
GITHUB_REPO_OWNER=username
GITHUB_REPO_NAME=repo_name
OLLAMA_API_URL=http://localhost:11434
# Use the exact model name shown by `ollama list`, e.g. ministral-3:3b
OLLAMA_MODEL=ministral-3:3b
AGENT_TEMPERATURE=0.3
```

## 📁 Project Structure

```
src/
├── agents/
│   ├── base_agent.py          # Planning + Tool Use + Reflection
│   ├── change_review_agent.py  # Task 1 implementation
│   └── __init__.py
├── tools/
│   ├── git_ops.py              # Git commands
│   ├── github_ops.py           # GitHub API
│   ├── ollama_client.py        # Local LLM
│   └── __init__.py
├── config/
│   ├── settings.py
│   └── __init__.py
└── main.py                     # CLI Entry point
```

## 🎯 How It Works

### Change Review Agent Workflow

1. **Planning**: Break analysis into steps
2. **Tool Use**: Extract git diff and analyze
3. **Reflection**: Assess and recommend action

### Output Example

```
🔍 Starting Change Review Agent...

📊 Analyzing git changes...

📈 Diff Statistics:
  Files changed: 3
  Insertions: +45
  Deletions: -12

🤖 Agent Analysis:
  Type: Feature with refactoring
  Analysis: Authentication module + error handling...

✨ Recommendation:
  Action: CREATE_PR
  Risk Level: MEDIUM
  Change Type: feature
```

## 🔮 Next Phases

- **Phase 2**: Issue/PR Creator Agent
- **Phase 3**: Issue/PR Improver Agent
- **Phase 4**: Coordinator Agent (orchestrates all)

## 🐛 Troubleshooting

**Ollama not found?**

```bash
msiexec.exe /i ollama-installer.msi  # Download from ollama.ai
ollama serve  # In one terminal
```

**GitHub errors?**

- Verify PAT has `repo` and `issues` scopes
- Check owner/repo names in .env
- Confirm git repo exists locally

## 📝 License

MIT - Feel free to extend and improve!
