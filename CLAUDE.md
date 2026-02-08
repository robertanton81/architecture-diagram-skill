# Architecture Diagram Skill

A Claude Skill and SDK agent for generating C4 architecture diagrams from codebase analysis. Supports two output modes: **IcePanel** (push diagrams to the IcePanel app) and **Mermaid** (generate Mermaid diagram code).

## Features

- Analyze any codebase to discover modules, services, connections, and technologies
- Two output modes: IcePanel (REST API) and Mermaid (text-based diagrams)
- Topic-focused diagramming: trace specific business processes (e.g. payment flow, user login) across the codebase
- Monorepo support: scope analysis to a specific subdirectory
- Self-learning knowledge base: learns IcePanel API and Mermaid syntax from docs, persists for future sessions
- Interactive flow diagram generation with branching and parallel paths
- Never assumes — always asks the user when something is ambiguous

## Project Structure

- `skill/` — The Claude Skill (portable, install globally or per-project)
  - `SKILL.md` — Skill definition with frontmatter and instructions
  - `scripts/` — Codebase analyzer and IcePanel push script
  - `knowledge/` — Self-learning knowledge base (shared, icepanel, mermaid subdirectories)
  - `references/` — C4 mapping tables, IcePanel API reference, plan format, setup guide
- `src/` — TypeScript agent using Claude Agent SDK
  - `index.ts` — Single-prompt mode (pass prompt as CLI arg)
  - `interactive.ts` — Interactive REPL mode

## Running the SDK Agent

```bash
npm install

# Mermaid mode (no credentials needed):
npm start -- "Analyze this project and create a Mermaid C4 diagram"

# IcePanel mode (requires credentials in .env):
cp .env.example .env   # then fill in your IcePanel credentials
npm start -- "Create a C4 diagram of this project in IcePanel"

# Interactive mode:
npm run interactive

# With topic scoping:
npm start -- "Diagram the payment flow in this project"

# With path scoping (monorepo):
npm start -- "Create architecture diagram for services/auth"
```

## Installing the Skill in Claude Code

```bash
# Global install (all projects):
mkdir -p ~/.claude/skills/diagramming-architecture
cp -r skill/* ~/.claude/skills/diagramming-architecture/

# Or from the distributable package:
mkdir -p ~/.claude/skills/diagramming-architecture
unzip diagramming-architecture.skill -d ~/.claude/skills/diagramming-architecture
```

## Environment Variables (optional — only for IcePanel mode)

- `ICEPANEL_API_KEY` — Your IcePanel API key
- `ICEPANEL_ORGANIZATION_ID` — Your IcePanel organization ID
- `ICEPANEL_LANDSCAPE_ID` — Target landscape ID (or the agent will ask)

Without these, the agent operates in Mermaid-only mode.
