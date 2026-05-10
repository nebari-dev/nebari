# GitHub Automation Tools

This directory contains GitHub Actions workflows that use Claude to automate various development tasks.

## Available Actions

### Claude PR Review (`/claude review`)

Triggers an AI-powered code review on a pull request. Reviews code quality, potential bugs, security implications, and performance considerations.

**Usage:** Comment `/claude review` on any pull request

**Workflow file:** [workflows/claude-pr-review.yml](workflows/claude-pr-review.yml)

---

### Claude Issue Actions

Automates bug fixes, feature implementations, and issue investigations directly from GitHub issues.

**Workflow file:** `.github-issue-actions.yml` (in root directory)

**Available commands:**

#### `/claude fix`
Creates a PR to fix a bug. Analyzes the issue, creates a fix branch, implements the fix with tests, and opens a PR.

#### `/claude implement`
Creates a PR to implement a feature. Creates a feature branch, implements following project patterns, adds tests and documentation, and opens a PR.

#### `/claude investigate`
Investigates an issue and posts detailed analysis including root cause, recommended solution, and affected files. Does not create a PR.

---

### Adding Custom Instructions

All commands support optional custom instructions that get passed directly to Claude's prompt:

```
/claude fix

Ensure backwards compatibility with Python 3.8 and add comprehensive unit tests
```

```
/claude implement

Follow the pattern used in src/services/auth.py
```

```
/claude investigate

Check for interactions with the new caching layer added in PR #123
```

Use custom instructions to specify implementation details, highlight constraints, or provide additional context.

---

## Requirements

### Permissions
- **Team membership**: Must be a member of the authorized team to trigger actions
- **GitHub token permissions**: Workflows require:
  - PR Review: `contents: read`, `pull-requests: write`, `id-token: write`
  - Issue Actions: `contents: write`, `issues: write`, `pull-requests: write`, `id-token: write`

### Secrets
- `ANTHROPIC_API_KEY`: Required secret configured in repository settings (managed by repository administrators)
