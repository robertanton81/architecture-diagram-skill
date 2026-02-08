---
name: diagramming-architecture
description: >-
  Creates C4 architecture diagrams by analyzing a codebase. Two output modes:
  IcePanel (push diagrams to the IcePanel app) and Mermaid (generate Mermaid
  diagram code). Supports full system diagrams, monorepo subdirectory scoping,
  and topic-focused diagrams for specific business processes (e.g. payment flow,
  user login, order processing). Use when the user wants to: create architecture
  diagrams, visualize a codebase, generate C4 diagrams, create flow diagrams,
  or diagram a specific business process.
---

# Architecture Diagramming

Two output modes:

1. **IcePanel mode** — push model objects, connections, diagrams, and flows to IcePanel via REST API
2. **Mermaid mode** — generate Mermaid diagram code (C4, sequence, flowchart)

Available tools:
- `scripts/analyze_codebase.py` — scans a project directory, outputs JSON with modules, entry points, connections, technologies (Python 3.10+, stdlib only)
- `scripts/push_to_icepanel.py` — pushes a plan JSON file to IcePanel REST API (Python 3.10+, stdlib only)
- `knowledge/` — pre-seeded knowledge base: `shared/`, `icepanel/`, `mermaid/`
- `references/` — static reference files: `c4-mapping.md`, `icepanel-api.md`, `plan-format.md`, `setup.md`

**Mermaid rendering** requires `@mermaid-js/mermaid-cli` (installed on-demand via `npx`).

# Workflow

Follow these steps in order. Do not skip steps.

Copy this checklist and track progress:

```
Diagram Progress:
- [ ] Step 1: Determine scope (full system / module / business process)
- [ ] Step 2: Select output mode (IcePanel / Mermaid)
- [ ] Step 3: Analyze codebase (run analyze_codebase.py)
- [ ] Step 4: Present findings, recommend diagram type, resolve ambiguities
- [ ] Step 5: Check knowledge base for syntax/API details
- [ ] Step 6: Generate diagram (mode-specific workflow)
```

## Step 1: Determine what to diagram

If the skill was invoked with an argument, it is either a **path** or a **topic**:
- **Path** (e.g. `/diagramming-architecture services/payments`) — analyze only that subdirectory
- **Topic** (e.g. `/diagramming-architecture payment flow`) — trace that business process across the codebase

If unclear whether the argument is a path or topic, ask: "Is `<argument>` a directory path I should analyze, or a business process I should trace through the codebase?"

If no argument was provided, ask:

> "What would you like to diagram?
> 1. **Full system** — the entire project architecture
> 2. **Specific module/directory** — a subdirectory (useful for monorepos)
> 3. **Specific business process** — trace a flow like payment processing across all relevant modules
>
> Which would you prefer, and can you point me to the project path?"

For monorepos, always ask which part to focus on — never diagram the entire monorepo without confirmation.

## Step 2: Select output mode

Ask the user which output mode to use:

> "Which output format would you like?
> 1. **IcePanel** — creates diagrams in your IcePanel workspace (requires API key setup)
> 2. **Mermaid** — generates Mermaid diagram code you can render in GitHub, VS Code, docs, etc."

Do NOT proceed until the user has explicitly chosen a mode. If the user mentions IcePanel explicitly in their request, confirm: "I'll use IcePanel mode — is that correct?"

## Step 3: Analyze the codebase

For full / path-scoped analysis:
```bash
python scripts/analyze_codebase.py <path>
```

For topic-focused analysis (e.g. "payment flow"):
1. Run `analyze_codebase.py` on the project root for overall structure
2. Trace the business process: search for entry points (API routes, event handlers, CLI commands) → follow call chain through controllers/services/repositories → identify all systems touched → note data flow direction and protocols

## Step 4: Present findings and recommend diagram type

Think step-by-step before presenting. Then show findings in this format:

> **What I found:**
> - [N] modules/services: [list with 1-line description each]
> - [N] external systems: [list]
> - [N] data stores: [list]
> - Key connections: [brief summary]
> - Technologies: [list]
>
> **Recommended diagram type:** [type] — [1-sentence reason]
>
> Other options:
> - [alternative 1] — [when better]
> - [alternative 2] — [when better]
>
> **Questions before I proceed:**
> 1. [specific question about an ambiguity]
> 2. [specific question about scope/inclusion]

### Diagram type decision logic

| What you found | Recommended type | Why |
|---|---|---|
| Multiple independent systems communicating | **C4Context (C1)** | Big picture: which systems exist and interact |
| One system with internal apps/stores/workers | **C4Container (C2)** | What's inside: containers, databases, queues |
| One container with internal modules | **C4Component (C3)** | Internal structure: modules, classes, packages |
| User asked for a specific flow/process | **C4Dynamic** or **sequenceDiagram** | Step-by-step interaction over time |
| Microservices with complex call chains | **C4Context (C1)** first, then offer **C4Dynamic** | Overview first, drill into flows |
| Monolith with clear internal modules | **C4Container (C2)** or **C4Component (C3)** | Depends on whether modules are deployable |
| Topic-scoped (e.g. "payment flow") | **C4Dynamic** or **sequenceDiagram** + **C4Context** | Flow is primary, structure as companion |
| Simple app (few components) | **C4Context (C1)** | Keep it simple |
| Infrastructure/deployment focus | **C4Deployment** | Servers, containers, cloud services |

### Example: good findings presentation

**Scenario:** E-commerce monolith with 5 internal services

> **What I found:**
> - 5 internal services: API Gateway, Product Service, Order Service, Payment Service, Notification Service
> - 2 external systems: Stripe (payments), SendGrid (email)
> - 2 data stores: PostgreSQL (primary), Redis (cache)
> - Key connections: All services via internal HTTP; API Gateway routes external requests
> - Technologies: Node.js, Express, PostgreSQL, Redis
>
> **Recommended:** C4Container (C2) — single system with 5 distinct containers
>
> **Questions:**
> 1. Should Redis appear as a separate container, or is it an implementation detail?
> 2. The Notification Service handles email and SMS — include both?

**When anything is ambiguous, STOP and ASK.** Do not assume. Pattern: present what you discovered, then ask 2-3 targeted questions. Never ask more than 3 at once.

## Step 5: Check knowledge base

Before performing any diagramming operation:

1. Check `knowledge/<mode>/` for a `.md` file on the topic
2. Also check `knowledge/shared/` for general C4 topics
3. If a file exists, read and use it
4. If no file exists, check `knowledge/.index.md` for the documentation URL, fetch and learn it, then save as a new `.md` file (under 200 lines) before proceeding

**Pre-seeded topics** (ready to use without fetching):
- **Shared:** `shared/c4-model.md`
- **IcePanel:** `icepanel/api-basics.md`, `icepanel/create-model-objects.md`, `icepanel/create-connections.md`, `icepanel/create-diagrams.md`, `icepanel/create-flows.md`
- **Mermaid:** `mermaid/c4-syntax.md`

## Step 6: Generate (mode-specific)

Follow the appropriate mode workflow below.

---

# IcePanel Mode

## Capabilities

- **Read** existing architecture via the `icepanel` MCP server (read-only tools)
- **Write** new model objects, connections, diagrams, and flows via `push_to_icepanel.py` (REST API)

## Workflow: Generate and push

1. Build a plan JSON file from the confirmed architecture. See [references/plan-format.md](references/plan-format.md).
2. Show the plan for approval: "Here's what I'll create in IcePanel — does this look right?"
3. Dry run first:
   ```bash
   python scripts/push_to_icepanel.py plan.json --dry-run
   ```
4. Push after approval:
   ```bash
   python scripts/push_to_icepanel.py plan.json
   ```
   Uses env vars `API_KEY` and `ORGANIZATION_ID` from MCP config, plus `ICEPANEL_LANDSCAPE_ID` (ask user if not set).
5. Offer to refine: drill into modules, add detail levels, create additional diagram views.
6. Offer to add flows: "Would you like to create flow diagrams showing how requests travel through the system?"

## Reading existing IcePanel data

Use the `icepanel` MCP server (read-only) to query existing architecture:

- `icepanel:getLandscapes` — list landscapes
- `icepanel:getModelObjects` — query objects with type filters:
  - C1: `type: ["system", "actor", "group"]`
  - C2: `type: ["app", "store", "actor", "group"]`
  - C3: `type: ["component", "actor", "group"]`
- `icepanel:getModelObjectRelationships` — get connections for an object
- `icepanel:getTeams` — filter by team ownership
- `icepanel:getTechnologyCatalog` — look up technology IDs
- `icepanel:getModelObject` — get details (use `includeHierarchicalInfo` sparingly)

## Combined workflow: Codebase + existing IcePanel

1. Analyze the codebase
2. Query IcePanel for existing objects in the target landscape
3. Show both side-by-side, ask user to resolve conflicts (different names, duplicates, missing items)
4. Build plan JSON excluding objects that already exist
5. Dry run, approval, push

## Flow diagram generation (interactive)

Flows are step-by-step diagrams overlaid on a diagram. Always gather the full specification interactively.

**Step A: Establish context** — which diagram should the flow live on? What objects are on it?

**Step B: Gather specification** (one group at a time):
1. "What scenario does this flow describe?"
2. "Walk me through the steps — what happens first, then what?"
3. "Which systems/services are involved?" (confirm against diagram objects)
4. "Any decision points? What happens if auth fails, payment is declined?"
5. "Do any steps happen simultaneously?"
6. "Should I show responses going back?"

**Step C: Present the flow plan**

```
Flow: "User Login"
  1. [introduction] User attempts to log in
  2. [outgoing] User -> Web App: Opens login page
  3. [outgoing] Web App -> API: POST /auth/login
  4. [outgoing] API -> Database: Validate credentials
  5. [alternate-path] Auth result
     +- Success:
     |  6. [reply] API -> Web App: Return JWT token
     +- Failure:
     |  7. [reply] API -> Web App: Return 401 error
  8. [conclusion] User is authenticated or shown error
```

Ask: "Does this flow look right? Should I add, remove, or change any steps?"

**Step D: Create** — check `knowledge/icepanel/create-flows.md`, build flow in plan JSON (see `references/plan-format.md`), dry run, approval, push.

---

# Mermaid Mode

## Workflow: Generate and review

1. Generate Mermaid code using confirmed architecture and learned syntax. Map modules using [references/c4-mapping.md](references/c4-mapping.md). Follow readability best practices in `knowledge/mermaid/c4-syntax.md`.
2. **Visual review** — render and inspect before showing to user (see below).
3. Present BOTH the Mermaid code and rendered PNG. Ask: "Does this look right? Should I add, remove, or change anything?"
4. Refine based on feedback. Re-run visual review after each refinement.
5. Offer next steps:
   - "Want me to create a drill-down diagram for any of these systems?"
   - "Should I add a flow diagram showing a specific request flow?"
   - "Want me to write this to a file? If so, where?"

## Flow diagrams (interactive)

Follow the same interactive pattern as IcePanel flow generation:
1. Ask which scenario to diagram
2. Gather the flow step-by-step
3. Ask about branching, parallel execution, error paths
4. Check `knowledge/mermaid/sequence-diagrams.md` — self-learn if missing
5. Generate Mermaid `sequenceDiagram` or `C4Dynamic` syntax
6. Visual review, present for approval, refine

---

# Visual Review for Mermaid Diagrams

Every Mermaid diagram must be visually reviewed before presenting to the user.

## Rendering

```bash
npx -p @mermaid-js/mermaid-cli mmdc -i /tmp/architecture-diagram.mmd -o /tmp/architecture-diagram.png -w 2048 -H 1536
```

Read the PNG to visually inspect it.

If `mmdc` fails: tell the user "I wasn't able to render a preview — please check the Mermaid code visually" and proceed with code-only. Do not block the workflow.

## Readability checklist

| Issue | What to look for | Fix |
|---|---|---|
| Overlapping labels | Text running into other text | Shorten labels, use `UpdateRelStyle` offsets |
| Cramped layout | Elements too close | Increase `$c4ShapeInRow`, add `UpdateLayoutConfig` |
| Too many elements | >12-15 elements | Split into overview + drill-down, ask user |
| Unreadable text | Labels truncated or too small | Shorten to 3-4 word labels, 8-10 word descriptions |
| Arrow spaghetti | Too many crossing connections | Group in boundaries, max 3-4 connections per element |
| Missing context | No title, key elements undescribed | Add `title`, add descriptions |
| Poor flow direction | No clear visual flow | Use directional `Rel_D`/`Rel_R`/`Rel_L`/`Rel_U` |

## Iteration loop

1. Render and inspect
2. If issues found, identify fixes (consult `knowledge/mermaid/c4-syntax.md` readability section)
3. Modify code, re-render, re-inspect
4. Maximum 3 iterations
5. If still not ideal, present best version with a note about remaining issues

---

# Topic-Focused Diagramming

When diagramming a specific business process (e.g. "payment flow", "customer login"):

## Discovery phase

1. Analyze full codebase for overall structure
2. Search for entry points: API routes, event handlers, CLI commands, webhooks
3. Trace call chain: controllers -> services -> repositories -> databases, plus service-to-service calls and external APIs
4. Identify all systems/modules touched

## Presentation phase

> "For the **[topic]**, I found these systems are involved:
> - [System 1] ([role])
> - [System 2] ([role])
>
> Chain: [Actor] -> [System 1] -> [System 2] -> ...
>
> Does this look complete? Should I include or exclude anything?"

## Generation phase

Offer: **Structure diagram** (focused C4 showing relevant subset), **Flow diagram** (step-by-step sequence), or **Both**.

---

# Handling Complex Systems

For non-trivial architectures, ask about:
- **Multiple detail levels**: "Create separate diagrams for C1 overview + C2 drill-downs?"
- **Flow diagrams**: "Static structure, or also step-by-step flows?"
- **Conditional flows**: "Show branching paths (success/failure) or just the happy path?"
- **Async vs sync**: "Visually distinguish sync from async connections?"
- **Deployment vs logical view**: "Diagram logical architecture or deployment topology?"

---

# Setup

**Mermaid mode** requires no setup — works out of the box.

**IcePanel mode** requires the IcePanel MCP server configured with API credentials. See [references/setup.md](references/setup.md).

## Dependencies

- **Python 3.10+** — for `analyze_codebase.py` and `push_to_icepanel.py` (stdlib only, no pip packages needed)
- **Node.js 18+** — only for Mermaid rendering (`npx -p @mermaid-js/mermaid-cli mmdc`) and IcePanel MCP server (`npx @icepanel/mcp-server`)
- **IcePanel account** with API access — only for IcePanel mode
