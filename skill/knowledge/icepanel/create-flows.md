# Creating Flows (Sequence Diagrams)

**Learned from**: https://developer.icepanel.io/api-reference/flows/create

## Endpoint

```
POST /landscapes/{landscapeId}/versions/latest/flows
```

## Required Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Flow name |
| `diagramId` | string | Diagram this flow belongs to |

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `index` | number | Ordering |
| `pinned` | boolean | Pin flow |
| `showAllSteps` | boolean | Show all steps expanded |
| `showConnectionNames` | boolean | Show connection labels |
| `labels` | object | Key-value pairs |
| `handleId` | string | For upsert |
| `steps` | object | Map of step_id -> FlowStep |

## Step Structure

Steps are a map (object, not array) keyed by step ID.

### Step Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `id` | yes | string | Step identifier (same as key) |
| `description` | yes | string | Step label |
| `index` | yes | number | Order (0-based) |
| `type` | yes | enum | See step types below |
| `originId` | no | string | Source model object ID |
| `targetId` | no | string | Target model object ID |
| `parentId` | no | string | Parent step ID (for nested steps) |
| `detailedDescription` | no | string | Long-form description |

### Step Types

- `introduction` — opening context
- `information` — informational note
- `conclusion` — closing summary
- `self-action` — action within a single object
- `reply` — response back (reverse direction)
- `outgoing` — call from origin to target
- `alternate-path` — branching logic (if/else)
- `parallel-path` — concurrent execution
- `subflow` — reference to another flow

## Response

```json
{ "flow": { "id": "...", "name": "...", "diagramId": "...", ... } }
```
