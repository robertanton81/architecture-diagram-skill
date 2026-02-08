# IcePanel REST API Reference

Persistent reference for the IcePanel REST API. The skill reads this file instead of re-fetching docs each time.

## Contents

- [Base URL & Auth](#base-url--auth)
- [Rate Limits](#rate-limits)
- [Landscapes](#landscapes)
- [Model Objects](#model-objects) (List, Create, Upsert, Update, Get/Delete, Get root)
- [Model Connections](#model-connections) (Create, Upsert/Update/Get/Delete)
- [Diagrams](#diagrams) (Create, Replace Content/Positioning)
- [Teams](#teams)
- [Technologies](#technologies)
- [Flows](#flows)
- [Versions](#versions)
- [Export](#export)

## Base URL & Auth

```
Base: https://api.icepanel.io/v1
Header: Authorization: ApiKey <key>
   or:  X-API-Key: <key>
```

## Rate Limits

- GET/HEAD: 2,400/min
- POST/PUT/PATCH/DELETE: 60/min
- POST /user/*: 10/min

## Landscapes

```
GET  /organizations/{orgId}/landscapes          → { landscapes: [...] }
GET  /organizations/{orgId}/landscapes/{id}     → { landscape: {...} }
```

## Model Objects

### List
```
GET /landscapes/{landscapeId}/versions/latest/model/objects
    ?filter[type]=system|app|store|component|actor|group|root
    ?filter[status]=live|future|deprecated|removed
    ?filter[external]=true|false
    ?filter[parentId]=<id>|null
    ?filter[teamId]=<id>
    ?filter[technologyId]=<id>
```

### Create
```
POST /landscapes/{landscapeId}/versions/latest/model/objects

Body (required): { name, parentId, type }
Body (optional): caption, description, external, status,
                 technologyIds[], teamIds[], tagIds[], groupIds[],
                 domainId, handleId, labels{}, icon{}, links{}

Response: { modelObject: { id, name, type, ... } }
```

### Upsert (create-or-update)
```
PUT /landscapes/{landscapeId}/versions/latest/model/objects/{modelObjectId}

Same body as Create. If modelObjectId exists → update, else → create.
```

### Update
```
PATCH /landscapes/{landscapeId}/versions/latest/model/objects/{modelObjectId}

Body: any subset of fields to update
```

### Get / Delete
```
GET    /landscapes/{landscapeId}/versions/latest/model/objects/{id}
DELETE /landscapes/{landscapeId}/versions/latest/model/objects/{id}
```

### Get root object
To create top-level objects, get the root object ID first:
```
GET /landscapes/{landscapeId}/versions/latest/model/objects?filter[type]=root
→ use modelObjects[0].id as parentId for top-level objects
```

## Model Connections

### Create
```
POST /landscapes/{landscapeId}/versions/latest/model/connections

Body (required): { name, direction, originId, targetId }
  direction: "outgoing" | "bidirectional"

Body (optional): description, status, technologyIds[], tagIds[],
                 labels{}, viaId, handleId, links{}

Response: { modelConnection: { id, name, originId, targetId, ... } }
```

### Upsert / Update / Get / Delete
```
PUT    /landscapes/{landscapeId}/versions/latest/model/connections/{id}
PATCH  /landscapes/{landscapeId}/versions/latest/model/connections/{id}
GET    /landscapes/{landscapeId}/versions/latest/model/connections/{id}
DELETE /landscapes/{landscapeId}/versions/latest/model/connections/{id}
```

## Diagrams

### Create
```
POST /landscapes/{landscapeId}/versions/latest/diagrams

Body (required): { name, type, modelId, index }
  type: "context-diagram" | "app-diagram" | "component-diagram"
  modelId: the model object this diagram belongs to (use root for C1)
  index: ordering number (0-based)

Body (optional): description, status, groupId, parentId, labels{},
                 objects{}, connections{}, comments{}

Response: { diagram: { id, ... }, diagramContent: { objects, connections, ... } }
```

### Replace Diagram Content (position objects on canvas)
```
PUT /landscapes/{landscapeId}/versions/latest/diagrams/{diagramId}/content

Body: {
  objects: {
    "<modelObjectId>": {
      "id": "<diagramObjectId>",
      "modelId": "<modelObjectId>",
      "type": "system|app|store|component|actor|group",
      "shape": "box|area",
      "x": 100, "y": 200,
      "width": 200, "height": 150
    }
  },
  connections: {
    "<modelConnectionId>": {
      "id": "<diagramConnectionId>",
      "modelId": "<modelConnectionId>",
      "originId": "<diagramObjectId>",
      "targetId": "<diagramObjectId>",
      "lineShape": "curved|straight|square",
      "labelPosition": 0.5,
      "points": []
    }
  },
  comments: {}
}
```

**Connectors** (where arrows attach): top-left, top-center, top-right, right-top, right-middle, right-bottom, bottom-right, bottom-center, bottom-left, left-bottom, left-middle, left-top

**Shape types**:
- `box`: standard element (systems, containers, components, actors)
- `area`: boundary/grouping element (groups, system boundaries)

**Typical sizes**:
- System/Container box: width=200, height=150
- Actor: width=150, height=150
- Group/boundary area: width=600, height=400

## Teams
```
GET /organizations/{orgId}/teams → { teams: [{ id, name, color, ... }] }
```

## Technologies
```
GET /catalog/technologies?filter[type]=data-storage|framework-library|...
GET /organizations/{orgId}/technologies
```

## Flows
```
POST /landscapes/{landscapeId}/versions/latest/flows
Body: { name, type, diagramId, index }
```

## Versions
```
POST /landscapes/{landscapeId}/versions
Body: { name, notes, modelHandleId }
```

## Export
```
GET /landscapes/{landscapeId}/versions/latest/model/objects/export/csv
GET /landscapes/{landscapeId}/versions/latest/model/connections/export/csv
GET /landscapes/{landscapeId}/versions/latest/export/json
```
