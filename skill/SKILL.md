---
name: architecture-diagrams
description: >-
  Creates C4 architecture diagrams by analyzing a codebase. Two output modes:
  IcePanel (push diagrams to the IcePanel app) and Mermaid (generate Mermaid
  diagram code). Supports full system diagrams, monorepo subdirectory scoping,
  and topic-focused diagrams for specific business processes (e.g. payment flow,
  user login, order processing). Use when the user wants to: create architecture
  diagrams, visualize a codebase, generate C4 diagrams, create flow/sequence
  diagrams, or diagram a specific business process.
---

# Architecture Diagram Generator

Creates C4 architecture diagrams by analyzing a codebase. Two output modes:

1. **IcePanel mode** — push model objects, connections, diagrams, and flows to the IcePanel app via REST API
2. **Mermaid mode** — generate Mermaid diagram code (C4, sequence, flowchart) renderable in GitHub, VS Code, docs, etc.

## FIRST: Determine what to diagram

Before doing anything else, determine the **scope** of the diagram.

### If the skill was invoked with an argument

The argument can be either a **path** or a **topic**:

- **Path** (e.g. `/architecture-diagrams services/payments`) — analyze only that subdirectory
- **Topic** (e.g. `/architecture-diagrams payment flow`) — analyze the full codebase but focus on tracing that specific business process

If unclear whether the argument is a path or topic, **ask**: "Is `<argument>` a directory path I should analyze, or a business process I should trace through the codebase?"

### If no argument was provided

**Ask the user:**

> "What would you like to diagram?
> 1. **Full system** — the entire project architecture
> 2. **Specific module/directory** — a subdirectory of the project (useful for monorepos)
> 3. **Specific business process** — trace a flow like payment processing, user login, order fulfillment across all relevant modules
>
> Which would you prefer, and can you point me to the project path?"

For monorepos, **always ask** which part to focus on — never diagram the entire monorepo without confirmation.

## SECOND: Select output mode

**After scope is determined, ask the user which output mode to use:**

> "Which output format would you like?
> 1. **IcePanel** — creates diagrams in your IcePanel workspace (requires API key setup)
> 2. **Mermaid** — generates Mermaid diagram code you can render in GitHub, VS Code, docs, etc.
>
> Which would you prefer?"

**Do NOT proceed until the user has explicitly chosen a mode.** Do not infer the mode from context. Do not default to one mode.

If the user mentions IcePanel explicitly in their request, confirm: "I'll use IcePanel mode — is that correct?"

## THIRD: Choose the right diagram type

**After analyzing the codebase (but before generating), recommend the best diagram type based on what you found.** Do not just list all options — analyze the codebase findings and make an informed recommendation, presenting the 2-3 most suitable options with reasoning.

### Decision logic

Use the codebase analysis results and the user's scope to determine what makes sense:

| What you found | Recommended diagram type | Why |
|---|---|---|
| Multiple independent systems/services communicating | **C4Context (C1)** | Shows the big picture — which systems exist and how they interact |
| One system with multiple internal apps/stores/workers | **C4Container (C2)** | Shows what's inside the system — containers, databases, queues |
| One container/service with internal modules | **C4Component (C3)** | Shows internal structure — modules, classes, packages |
| User asked for a specific flow/process | **C4Dynamic** or **sequenceDiagram** | Shows step-by-step interaction over time |
| Microservices with complex call chains | **C4Context (C1)** first, then offer **C4Dynamic** for specific flows | Overview first, then drill into flows |
| Monolith with clear internal modules | **C4Container (C2)** or **C4Component (C3)** | Depends on whether modules are deployable units or code-level |
| Topic-scoped (e.g. "payment flow") | **C4Dynamic** or **sequenceDiagram** + **C4Context** showing involved systems | Flow diagram is primary, structure diagram as companion |
| Simple app (few components, no microservices) | **C4Context (C1)** | Keep it simple — don't over-engineer the diagram |
| Infrastructure/deployment focus | **C4Deployment** | Shows servers, containers, cloud services |

### How to present the recommendation

After analyzing the codebase, present your recommendation with reasoning. Example:

> "Based on what I found, I'd recommend a **C4Container (C2) diagram** — your project has one main system with 5 distinct containers (API, Web App, Worker, PostgreSQL, Redis) that would be well-represented at this level.
>
> Other options that could work:
> - **C4Context (C1)** — if you want a higher-level view showing just the system + external services (Stripe, SendGrid)
> - **C4Dynamic** — if you'd prefer a sequence diagram showing a specific request flow
>
> Which would you prefer?"

### Key rules

- **Always explain WHY** you recommend a specific type — tie it to what you found in the codebase
- **Offer 2-3 options**, not all of them — filter based on what actually makes sense
- **If the scope clearly dictates one type** (e.g. "diagram the payment flow" → C4Dynamic/sequenceDiagram), still confirm: "A sequence diagram is the best fit for tracing this flow — sound good?"
- **If multiple types are equally valid**, explain the trade-off: "C1 gives you the bird's-eye view, C2 shows internal structure — which perspective is more useful for you?"
- **For complex systems, suggest a multi-diagram approach**: "I'd recommend starting with a C1 overview, then drilling into C2 for the backend system — want me to create both?"
- **Never silently pick a diagram type** without at least confirming with the user

## CRITICAL RULE: Never assume — always ask

**This is the most important behavioral rule in this skill.**

When ANYTHING is ambiguous, unclear, or could be interpreted multiple ways: **STOP and ASK the user.** Do not make assumptions. Do not pick a "reasonable default." Do not proceed with your best guess.

### Architecture decisions (both modes)
- **Module classification** — "I found `auth/` — is this a standalone service, a shared library, or part of the API?"
- **External systems** — "I see calls to Stripe/AWS/etc. Include these as external systems?"
- **Actors** — "Who are the users/actors? I can infer from code but want to confirm."
- **Boundaries** — "Group by team, domain, or deployment unit?"
- **Data flows** — "What protocol does this connection use? REST, gRPC, messaging?"
- **Detail depth** — "Expand nested subsystems or keep them collapsed?"
- **Flow branching** — "Show conditional paths (success/failure) or just the happy path?"

### Topic-scoped decisions
- **Scope boundaries** — "Should I include the notification service that sends receipts, or stop at payment confirmation?"
- **Entry points** — "I found multiple entry points for this flow (API + webhook + scheduled job). Include all of them?"
- **Depth** — "Should I trace into internal service logic, or keep it at the service-to-service level?"

### Mermaid-specific decisions
- **Styling** — "Want custom theming/colors, or Mermaid defaults?"
- **Output destination** — "Write to a file (e.g. `docs/architecture.md`) or show the code here?"
- **Multiple diagrams** — "Create separate diagrams for overview + drill-downs, or one combined?"

### IcePanel-specific decisions
- **Landscape** — "Which IcePanel landscape should I create these in?"
- **Existing objects** — "I found similar objects in IcePanel. Reuse them or create new?"
- **Technology mapping** — "Which IcePanel technology ID for this framework?"

**Pattern:** Present what you discovered, recommend a diagram type with reasoning, then ask 2-3 targeted questions. Always better than generating a possibly-wrong diagram.

## Knowledge base: Learn before you act

Before performing any diagramming operation, **check the knowledge base first**:

1. Determine which mode is active (IcePanel or Mermaid)
2. Look in `knowledge/<mode>/` for a `.md` file covering the topic
3. Also check `knowledge/shared/` for general C4 topics
4. If a file exists → read it and use that information
5. If NO file exists:
   a. Check `knowledge/.index.md` for the relevant documentation URL
   b. Fetch and read the docs
   c. Extract the key information (syntax, endpoints, fields, examples, gotchas)
   d. Save as a new `.md` file in the correct subdirectory (concise, under 200 lines)
   e. Then proceed with the operation

**This is critical.** The knowledge base grows over time. Every topic encountered becomes persistent knowledge for future sessions. Never guess about syntax or API behavior — learn it first, persist the knowledge, then act.

### Pre-seeded topics

**Shared:** `shared/c4-model.md`

**IcePanel:** `icepanel/api-basics.md`, `icepanel/create-model-objects.md`, `icepanel/create-connections.md`, `icepanel/create-diagrams.md`, `icepanel/create-flows.md`

**Mermaid:** `mermaid/c4-syntax.md`

### Topics that commonly need learning on first encounter

**IcePanel:** Domains, Tags, Versions, Diagram groups, Export formats

**Mermaid:** Sequence diagrams, Flowcharts, Class diagrams, Themes & styling, Directives

## Shared workflow: Codebase analysis

This step is the same regardless of output mode.

### Full / path-scoped analysis

```bash
python scripts/analyze_codebase.py <path>
```

This outputs JSON with: modules, entry points, connections, technologies. Present findings to the user before proceeding.

### Topic-focused analysis

For business process scoping (e.g. "payment flow", "user login"):

1. Run `analyze_codebase.py` on the **project root** to understand overall structure
2. **Trace the specific business process** through the codebase:
   - Search for relevant entry points (API routes, event handlers, CLI commands)
   - Follow the call chain through controllers → services → repositories → external APIs
   - Identify all systems touched (databases, queues, external services, caches)
   - Note the data flow direction and protocols
3. **Present findings**: "For the payment flow, I found these systems are involved: [list]. Here's the chain I traced: [flow]. Does this look complete?"
4. **Ask about boundaries**: "Should I include the notification service that sends payment receipts, or stop at the payment confirmation?"
5. Proceed with only the relevant subset of the architecture

## IcePanel mode

### Capabilities

- **Read** existing architecture via the `icepanel` MCP server (read-only tools)
- **Write** new model objects, connections, diagrams, and flows via `push_to_icepanel.py` (REST API)

### Primary workflow: Codebase → IcePanel

1. Analyze codebase (see shared workflow above)
2. **Present findings**: list discovered modules, entry points, connections, technologies. Highlight ambiguities.
3. **Recommend diagram type** (see [THIRD: Choose the right diagram type](#third-choose-the-right-diagram-type)) — recommend C4 level based on codebase findings, offer 2-3 options with reasoning, confirm with user.
4. **Ask clarifying questions**: include/exclude modules, classify ambiguous components, external systems, actors, flow branches.
5. **Check knowledge base**: read relevant files from `knowledge/icepanel/` for the API operations needed. If a topic is missing, fetch from IcePanel docs, learn it, and save to `knowledge/icepanel/` before proceeding.
6. **Build a plan JSON file** from the confirmed architecture. See [references/plan-format.md](references/plan-format.md).
7. **Show the plan** for approval: "Here's what I'll create in IcePanel — does this look right?"
8. **Dry run first**:
   ```bash
   python scripts/push_to_icepanel.py plan.json --dry-run
   ```
9. **Push to IcePanel** after approval:
   ```bash
   python scripts/push_to_icepanel.py plan.json
   ```
   Uses env vars `API_KEY` and `ORGANIZATION_ID` from MCP config, plus `ICEPANEL_LANDSCAPE_ID` (ask user if not set).
10. **Offer to refine**: drill into modules, add detail levels, create additional diagram views.
11. **Offer to add flows**: "Would you like to create flow diagrams showing how requests travel through the system?" Follow the flow generation workflow below.

### Reading existing IcePanel data

Use the `icepanel` MCP server (read-only) to query existing architecture:

- `icepanel:getLandscapes` — list landscapes
- `icepanel:getModelObjects` — query objects with type filters:
  - C1 System Context: `type: ["system", "actor", "group"]`
  - C2 Container: `type: ["app", "store", "actor", "group"]`
  - C3 Component: `type: ["component", "actor", "group"]`
- `icepanel:getModelObjectRelationships` — get connections for an object
- `icepanel:getTeams` — filter by team ownership
- `icepanel:getTechnologyCatalog` — look up technology IDs
- `icepanel:getModelObject` — get details (use `includeHierarchicalInfo` sparingly)

### Combined workflow: Codebase + IcePanel

1. Analyze the codebase
2. Query IcePanel for the target landscape's existing objects
3. **Show both sources side-by-side** and ask the user to resolve conflicts (different names, duplicates, missing items)
4. Build the plan JSON, excluding objects that already exist in IcePanel
5. Dry run → user approval → push

### IcePanel flow generation (interactive)

Flows are step-by-step sequence diagrams overlaid on a diagram. Always gather the full specification interactively.

**Step 1: Establish context**
- Which diagram should the flow live on?
- What objects are on that diagram?

**Step 2: Gather the flow specification**
1. **Purpose**: "What scenario does this flow describe?"
2. **Happy path**: "Walk me through the steps — what happens first, then what?"
3. **Actors**: "Which systems/services are involved?" (confirm against diagram objects)
4. **Branching**: "Any decision points? What happens if auth fails, payment is declined?"
5. **Parallel execution**: "Do any steps happen simultaneously?"
6. **Reply steps**: "Should I show responses going back?"
7. **Error paths**: "What happens when things go wrong?"

**Step 3: Present the flow plan**
```
Flow: "User Login"
  1. [introduction] User attempts to log in
  2. [outgoing] User → Web App: Opens login page
  3. [outgoing] Web App → API: POST /auth/login
  4. [outgoing] API → Database: Validate credentials
  5. [alternate-path] Auth result
     ├─ Success:
     │  6. [reply] API → Web App: Return JWT token
     ├─ Failure:
     │  7. [reply] API → Web App: Return 401 error
  8. [conclusion] User is authenticated or shown error
```

Ask: "Does this flow look right? Should I add, remove, or change any steps?"

**Step 4: Create**
1. Check `knowledge/icepanel/create-flows.md` for API details
2. Build the flow definition in plan JSON (see `references/plan-format.md`)
3. Dry run → user approval → push

**Flow question patterns for complex flows:**
- **Conditionals**: "Show conditional paths or just the happy path?"
- **Depth**: "Show internal logic (DB queries, cache) or keep at service-to-service level?"
- **Async**: "Show async calls as separate flows or inline?"
- **Subflows**: "Show this referenced process inline or as a subflow?"
- **Granularity**: "Should 'API processes request' be expanded into individual steps?"

## Mermaid mode

### Workflow: Codebase → Mermaid

1. Analyze codebase (see shared workflow above)
2. **Present findings**: list discovered modules, entry points, connections, technologies. Highlight ambiguities.
3. **Recommend diagram type** (see [THIRD: Choose the right diagram type](#third-choose-the-right-diagram-type)) — based on codebase findings, recommend the best Mermaid diagram type (C4Context, C4Container, C4Component, C4Dynamic, sequenceDiagram, flowchart). Present 2-3 suitable options with reasoning. Confirm with user before proceeding.
4. **Ask clarifying questions** (based on confirmed diagram type):
   - Include/exclude specific modules?
   - External systems and actors to show?
   - Styling preferences?
5. **Check knowledge base**: read `knowledge/mermaid/c4-syntax.md` (or the relevant diagram type file). If the file doesn't exist, check `knowledge/.index.md` for the docs URL, fetch, learn, and save before generating.
6. **Generate the Mermaid diagram** using confirmed architecture and learned syntax. Map modules using [references/c4-mapping.md](references/c4-mapping.md). Follow the readability best practices in `knowledge/mermaid/c4-syntax.md` (label lengths, element count, layout config).
7. **Visual review — render and inspect before showing to the user** (see [Visual review for Mermaid diagrams](#visual-review-for-mermaid-diagrams) below for full details):
   a. Write the Mermaid code to a temp file (`/tmp/architecture-diagram.mmd`)
   b. Render to PNG: `npx -p @mermaid-js/mermaid-cli mmdc -i /tmp/architecture-diagram.mmd -o /tmp/architecture-diagram.png -w 2048 -H 1536`
   c. Read the PNG image and visually inspect it against the readability checklist
   d. If readability issues found → fix the Mermaid code → re-render → re-inspect (max 3 iterations)
   e. If `mmdc` fails or is unavailable → skip visual review, note it to the user, and proceed with code-only presentation
8. **Present for approval** — show BOTH the Mermaid code in a fenced code block AND the rendered image:
   ````
   ```mermaid
   C4Context
       title System Context - Project Name
       ...
   ```
   ````
   Show the rendered PNG image alongside the code.
   Ask: "Does this look right? Should I add, remove, or change anything?"
9. **Refine** based on feedback: add/remove elements, change C4 levels, adjust labels, add detail. **Re-run visual review** after each refinement.
10. **Offer next steps**:
    - "Want me to create a drill-down diagram for any of these systems?"
    - "Should I add a sequence diagram showing a specific request flow?"
    - "Want me to write this to a file? If so, where?"

### Mermaid sequence diagrams (interactive)

For flow/sequence diagrams in Mermaid mode, follow the same interactive pattern:

1. **Ask** which scenario to diagram
2. **Gather the flow**: "Walk me through the steps"
3. **Ask about** branching, parallel execution, error paths
4. Check `knowledge/mermaid/sequence-diagrams.md` — self-learn if missing
5. Generate Mermaid `sequenceDiagram` or `C4Dynamic` syntax
6. **Visual review** — render and inspect the diagram (same process as the main workflow step 6 above)
7. Present for approval (show code + rendered image), refine. Re-run visual review after each refinement.

### Output options

- **Code block** — show Mermaid code in chat (default)
- **File** — write to a `.md` or `.mmd` file at user-specified path
- **Multiple diagrams** — generate separate files for overview + drill-downs

Always ask which output the user prefers.

## Visual review for Mermaid diagrams

**Every Mermaid diagram must be visually reviewed before presenting to the user.** Generating correct code is not enough — the rendered diagram must be readable and well-laid-out.

### Rendering

```bash
# Write diagram code to temp file, then render to PNG
npx -p @mermaid-js/mermaid-cli mmdc -i /tmp/architecture-diagram.mmd -o /tmp/architecture-diagram.png -w 2048 -H 1536
```

Then read the PNG image to visually inspect it. Claude can see images — use this ability.

If `mmdc` fails (not installed, Node issue, etc.): tell the user "I wasn't able to render a preview — please check the Mermaid code visually" and proceed with code-only presentation. Do not block the workflow on rendering failures.

### Readability checklist

Inspect the rendered image for these issues:

| Issue | What to look for | How to fix |
|---|---|---|
| **Overlapping labels** | Text running into other text, labels covering boxes or arrows | Shorten labels, use `UpdateRelStyle` with `$offsetX`/`$offsetY` to reposition |
| **Cramped layout** | Elements too close together, no whitespace between boxes | Increase `$c4ShapeInRow`, add `UpdateLayoutConfig`, reorder elements |
| **Too many elements** | >12-15 elements making the diagram overwhelming | Split into overview + drill-down diagrams, ask user which level of detail |
| **Unreadable text** | Labels truncated, text too small to read, descriptions cut off | Shorten labels to 3-4 words, shorten descriptions to 8-10 words |
| **Arrow spaghetti** | Too many crossing connections, hard to trace any single path | Group related elements in boundaries, reduce connections per element to 3-4 |
| **Missing context** | No title, key elements without descriptions | Add `title`, add descriptions to main elements |
| **Poor flow direction** | Important relationships not following a clear visual flow | Use directional `Rel_D`/`Rel_R`/`Rel_L`/`Rel_U` to guide layout |

### Iteration loop

1. Render and inspect
2. If issues found → identify which fixes to apply (consult `knowledge/mermaid/c4-syntax.md` readability section)
3. Modify the Mermaid code
4. Re-render and re-inspect
5. Repeat up to **3 iterations** maximum
6. If still not ideal after 3 iterations → present the best version with a note about remaining issues and suggestions

### What a good diagram looks like

- Clear visual hierarchy (actors at top, main system in center, externals at edges)
- All labels readable without zooming
- Connections traceable — you can follow any arrow from source to destination
- Adequate whitespace — elements don't feel cramped
- Consistent level of detail — no single element with far more detail than others
- Title present and descriptive

## Topic-focused diagramming

When the user wants to diagram a specific business process (e.g. "payment flow", "customer login", "order processing"):

### Discovery phase

1. Analyze the full codebase to understand the overall structure
2. Search for entry points related to the topic:
   - API routes (e.g. `/payments`, `/checkout`, `/orders`)
   - Event handlers (e.g. `onPaymentReceived`, `handleOrder`)
   - CLI commands, scheduled jobs, webhooks
3. Trace the call chain through the codebase:
   - Controllers → services → repositories → databases
   - Service-to-service calls (HTTP, gRPC, message queues)
   - External API calls (payment gateways, email services, etc.)
4. Identify all systems/modules touched by this process

### Presentation phase

Present the discovered flow: "For the **payment flow**, I found these systems are involved:
- Web App (initiates checkout)
- API Server (processes payment logic)
- PostgreSQL (stores orders)
- Stripe API (charges the card)
- RabbitMQ (publishes order events)
- Email Service (sends confirmation)

Here's the chain I traced: User → Web → API → Stripe → API → DB → Queue → Email

Does this look complete? Should I include or exclude anything?"

### Generation phase

Based on user confirmation:
- **Structure diagram**: generate a focused C4 diagram showing only the relevant subset
- **Flow diagram**: generate a sequence/flow diagram showing the step-by-step process
- **Offer both**: "Would you like a structure diagram (which systems are involved) and/or a flow diagram (the step-by-step sequence)?"

## Handling complex systems

For non-trivial architectures, always ask about:

- **Multiple detail levels**: "Create separate diagrams for C1 overview + C2 drill-downs?"
- **Flow diagrams**: "Static structure diagram, or also sequence/flow diagrams?"
- **Conditional flows**: "Show branching paths (success/failure) or just the happy path?"
- **Async vs sync**: "Visually distinguish sync from async connections?"
- **Deployment vs logical view**: "Diagram logical architecture or deployment topology?"

## Setup

**Mermaid mode** requires no setup — works out of the box.

**IcePanel mode** requires the IcePanel MCP server configured with API credentials. See [references/setup.md](references/setup.md) for instructions.

The codebase analysis script (`analyze_codebase.py`) requires Python 3.10+.
