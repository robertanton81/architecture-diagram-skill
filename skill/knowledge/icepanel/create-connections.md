# Creating Model Connections

**Learned from**: https://developer.icepanel.io/api-reference/model/connections/create

## Endpoint

```
POST /landscapes/{landscapeId}/versions/latest/model/connections
```

## Required Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Connection label |
| `direction` | enum | `outgoing` or `bidirectional` |
| `originId` | string | Source model object ID |
| `targetId` | string | Target model object ID |

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `description` | string | Additional detail |
| `status` | enum | `live`, `future`, `deprecated`, `removed` |
| `technologyIds` | string[] | Technology IDs |
| `tagIds` | string[] | Tag IDs |
| `labels` | object | Key-value pairs |
| `viaId` | string \| null | Intermediary model object |
| `handleId` | string | Custom handle for upsert |

## Response

```json
{ "modelConnection": { "id": "...", "name": "...", "originId": "...", "targetId": "...", ... } }
```
