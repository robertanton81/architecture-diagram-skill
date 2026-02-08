# Architecture Diagrams Skill — Setup Guide

## Mermaid Mode

**No setup required.** Mermaid mode works out of the box — the skill generates Mermaid diagram code that can be rendered in GitHub, VS Code, documentation sites, or any Mermaid-compatible viewer.

## IcePanel Mode

IcePanel mode requires API credentials and the IcePanel MCP server.

## Installation

### Claude Code

Unzip the `.skill` file into your skills directory:

```bash
mkdir -p ~/.claude/skills/architecture-diagrams
unzip architecture-diagrams.skill -d ~/.claude/skills/architecture-diagrams
```

### Claude.ai

Go to **Settings → Features** and upload the `architecture-diagrams.skill` file.

### Claude API

Upload via the Skills API:

```bash
curl -X POST https://api.anthropic.com/v1/skills \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "file=@architecture-diagrams.skill"
```

## IcePanel MCP Server Setup (optional — required only for IcePanel mode)

The codebase analysis and Mermaid generation work without this. Only needed if creating diagrams in IcePanel or querying existing IcePanel landscapes.

### 1. Get your credentials from IcePanel

1. Open IcePanel (desktop app or app.icepanel.io)
2. Click the landscape dropdown (top-left) → gear icon next to your organization name
3. Copy the **Organization Identifier** from the settings page
4. In the sidebar, click **API keys** → **Generate** a new key

### 2. Configure the MCP server

#### Claude Code

Add to `~/.claude/.mcp.json` (global) or `<project>/.mcp.json` (per-project):

```json
{
  "mcpServers": {
    "icepanel": {
      "command": "npx",
      "args": ["-y", "@icepanel/mcp-server@latest"],
      "env": {
        "API_KEY": "<your-api-key>",
        "ORGANIZATION_ID": "<your-org-id>"
      }
    }
  }
}
```

Restart Claude Code after adding this.

#### Cursor

Open Settings → MCP → Add server with the same configuration above.

#### Claude Agent SDK (TypeScript)

```typescript
const options = {
  mcpServers: {
    icepanel: {
      command: "npx",
      args: ["-y", "@icepanel/mcp-server@latest"],
      env: {
        API_KEY: process.env.ICEPANEL_API_KEY,
        ORGANIZATION_ID: process.env.ICEPANEL_ORGANIZATION_ID,
      },
    },
  },
  settingSources: ["user", "project"],
  allowedTools: ["Skill", "Bash", "Read", "Write", "Glob", "Grep", "mcp__icepanel__*"],
};
```

### 3. Verify

After setup, ask Claude: "List my IcePanel landscapes" — if configured correctly, it will return your landscapes.

## Requirements

- **Python 3.10+** (for the codebase analysis script)
- **Node.js 18+** (only for IcePanel mode — npx runs the MCP server)
- **IcePanel account** with API access (only for IcePanel mode)
