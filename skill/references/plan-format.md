# Plan JSON Format

The `push_to_icepanel.py` script reads a plan JSON file that describes what to create in IcePanel.

## Schema

```json
{
  "objects": [
    {
      "ref": "local-reference-id",
      "name": "Display Name",
      "type": "system|app|store|component|actor|group",
      "caption": "Short description shown in IcePanel",
      "description": "Longer markdown description",
      "parentRef": null,
      "external": false,
      "status": "live",
      "technologyIds": [],
      "teamIds": []
    }
  ],
  "connections": [
    {
      "name": "Connection label",
      "originRef": "ref-of-source-object",
      "targetRef": "ref-of-target-object",
      "direction": "outgoing|bidirectional",
      "description": "Optional description",
      "status": "live"
    }
  ],
  "diagram": {
    "name": "Diagram title",
    "type": "context-diagram|app-diagram|component-diagram"
  },
  "flows": [
    {
      "name": "Flow title",
      "diagramRef": "_new_",
      "showAllSteps": false,
      "showConnectionNames": true,
      "steps": [
        {
          "id": "step_1",
          "index": 0,
          "type": "outgoing|reply|self-action|alternate-path|parallel-path|subflow|introduction|information|conclusion",
          "description": "Step description",
          "originRef": "ref-of-source-object",
          "targetRef": "ref-of-target-object",
          "parentId": null,
          "paths": {}
        }
      ]
    }
  ]
}
```

## Field reference

### Objects

| Field | Required | Description |
|---|---|---|
| `ref` | yes | Local reference ID (not sent to API). Used by connections' originRef/targetRef. |
| `name` | yes | Display name in IcePanel |
| `type` | yes | C4 element type. Use: `system` for C1, `app`/`store` for C2, `component` for C3, `actor` for users, `group` for boundaries |
| `caption` | no | Short description shown under the name in IcePanel |
| `description` | no | Markdown description |
| `parentRef` | no | Ref of parent object (for nesting). null = root level. |
| `external` | no | true for external systems |
| `status` | no | `live` (default), `future`, `deprecated`, `removed` |
| `technologyIds` | no | Array of IcePanel technology IDs |
| `teamIds` | no | Array of IcePanel team IDs |

### Connections

| Field | Required | Description |
|---|---|---|
| `name` | yes | Label shown on the connection |
| `originRef` | yes | Ref of the source object |
| `targetRef` | yes | Ref of the target object |
| `direction` | yes | `outgoing` or `bidirectional` |
| `description` | no | Additional description |
| `status` | no | `live` (default), `future`, `deprecated`, `removed` |

### Diagram

| Field | Required | Description |
|---|---|---|
| `name` | yes | Diagram title |
| `type` | yes | `context-diagram` (C1), `app-diagram` (C2), or `component-diagram` (C3) |

### Flows

| Field | Required | Description |
|---|---|---|
| `name` | yes | Flow title |
| `diagramRef` | yes | `"_new_"` to use the diagram created in this plan, or an existing diagram ID |
| `showAllSteps` | no | Show all steps at once (default: false = animated) |
| `showConnectionNames` | no | Display connection labels on flow (default: false) |
| `steps` | yes | Array of flow steps (see below) |

### Flow Steps

| Field | Required | Description |
|---|---|---|
| `id` | yes | Unique step ID (e.g. `"step_1"`) |
| `index` | yes | Step order (0-based) |
| `type` | yes | Step type (see below) |
| `description` | yes | What happens in this step |
| `originRef` | for outgoing/reply | Ref of source object |
| `targetRef` | for outgoing/reply | Ref of target object |
| `parentId` | for nested steps | Parent step ID (for steps inside alternate-path or parallel-path) |
| `paths` | for branching | Object of path definitions: `{ "path_id": { "id": "...", "index": 0, "name": "Path Name" } }` |
| `detailedDescription` | no | Longer markdown description |

### Step Types

| Type | Use | Needs origin/target? |
|---|---|---|
| `outgoing` | Request from A to B | Yes (originRef + targetRef) |
| `reply` | Response from B back to A | Yes (originRef + targetRef) |
| `self-action` | Internal processing | originRef only |
| `alternate-path` | Conditional branch (if/else) | No — container for child steps |
| `parallel-path` | Concurrent execution | No — container for child steps |
| `subflow` | Reference another flow | No |
| `introduction` | Opening context text | No |
| `information` | Informational note | No |
| `conclusion` | Closing summary text | No |

## Mapping from analyze_codebase.py output

| Codebase module type | IcePanel object type |
|---|---|
| API service, server, backend service | `app` |
| web application, frontend | `app` |
| database layer | `store` |
| background worker, message queue consumer | `app` |
| shared library, library, utilities | `component` (or `app` if deployed separately) |
| module (generic) | `app` |

Use `has_dockerfile` or `is_deployable` from the analysis to decide if something is an `app` (deployable) vs `component` (library).

## Example

```json
{
  "objects": [
    {"ref": "user", "name": "Home Cook", "type": "actor", "caption": "Plans meals via the app"},
    {"ref": "api", "name": "API Server", "type": "app", "caption": "REST API", "status": "live"},
    {"ref": "web", "name": "Web App", "type": "app", "caption": "React frontend", "parentRef": null},
    {"ref": "db", "name": "PostgreSQL", "type": "store", "caption": "Primary data store"}
  ],
  "connections": [
    {"name": "Uses", "originRef": "user", "targetRef": "web", "direction": "outgoing"},
    {"name": "API calls", "originRef": "web", "targetRef": "api", "direction": "outgoing"},
    {"name": "Reads/Writes", "originRef": "api", "targetRef": "db", "direction": "outgoing"}
  ],
  "diagram": {
    "name": "System Overview",
    "type": "context-diagram"
  },
  "flows": [
    {
      "name": "User Login Flow",
      "diagramRef": "_new_",
      "showAllSteps": false,
      "steps": [
        {"id": "s1", "index": 0, "type": "introduction", "description": "User attempts to log in"},
        {"id": "s2", "index": 1, "type": "outgoing", "description": "Opens login page", "originRef": "user", "targetRef": "web"},
        {"id": "s3", "index": 2, "type": "outgoing", "description": "POST /auth/login", "originRef": "web", "targetRef": "api"},
        {"id": "s4", "index": 3, "type": "outgoing", "description": "Validate credentials", "originRef": "api", "targetRef": "db"},
        {"id": "s5", "index": 4, "type": "alternate-path", "description": "Auth result",
          "paths": {
            "p_ok": {"id": "p_ok", "index": 0, "name": "Success"},
            "p_fail": {"id": "p_fail", "index": 1, "name": "Failure"}
          }
        },
        {"id": "s6", "index": 5, "type": "reply", "description": "Return JWT token", "originRef": "api", "targetRef": "web", "parentId": "s5"},
        {"id": "s7", "index": 6, "type": "reply", "description": "Return 401 error", "originRef": "api", "targetRef": "web", "parentId": "s5"},
        {"id": "s8", "index": 7, "type": "conclusion", "description": "User is authenticated or shown error"}
      ]
    }
  ]
}
```

## Running

```bash
# Dry run (shows what would be created):
python scripts/push_to_icepanel.py plan.json --dry-run

# Create in IcePanel:
python scripts/push_to_icepanel.py plan.json --landscape-id <id>

# List available landscapes:
python scripts/push_to_icepanel.py plan.json
```

Environment variables used: `API_KEY`, `ORGANIZATION_ID`, `ICEPANEL_LANDSCAPE_ID`.
