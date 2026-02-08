# Creating Model Objects

**Learned from**: https://developer.icepanel.io/api-reference/model/objects/create

## Endpoint

```
POST /landscapes/{landscapeId}/versions/latest/model/objects
```

## Required Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Display name |
| `parentId` | string \| null | Parent object ID. Use root object ID for top-level. |
| `type` | enum | `actor`, `app`, `component`, `group`, `root`, `store`, `system` |

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `caption` | string | Short summary shown as display description |
| `description` | string | Detailed markdown description |
| `external` | boolean | Mark as external system |
| `status` | enum | `live`, `future`, `deprecated`, `removed` |
| `technologyIds` | string[] | Technology IDs from catalog |
| `teamIds` | string[] | Owning team IDs |
| `tagIds` | string[] | Tag IDs |
| `groupIds` | string[] | Group membership IDs |
| `domainId` | string | Domain ID |
| `handleId` | string | Custom handle for upsert |
| `labels` | object | Key-value pairs |
| `icon` | object | `{ catalogTechnologyId, name }` |
| `links` | object | Reality connectors (GitHub, GitLab, etc.) |

## Response

```json
{ "modelObject": { "id": "...", "name": "...", "type": "...", ... } }
```

## C4 Type Mapping

| C4 Level | IcePanel types |
|---|---|
| C1 System Context | `system`, `actor`, `group` |
| C2 Container | `app`, `store`, `actor`, `group` |
| C3 Component | `component`, `actor`, `group` |

## Getting Root Object

```
GET /landscapes/{id}/versions/latest/model/objects?filter[type]=root
→ modelObjects[0].id is the parentId for top-level objects
```
