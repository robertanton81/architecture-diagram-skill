# Creating Diagrams & Positioning Objects

**Learned from**: https://developer.icepanel.io/api-reference/diagrams/create and diagrams/content/replace

## Create Diagram

```
POST /landscapes/{landscapeId}/versions/latest/diagrams
```

### Required Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Diagram title |
| `type` | enum | `context-diagram`, `app-diagram`, `component-diagram` |
| `modelId` | string | Model object this diagram belongs to (root ID for C1) |
| `index` | number | Ordering (0-based) |

### Optional Fields

description, status, groupId, parentId, labels, objects, connections, comments

### Response

```json
{
  "diagram": { "id": "...", "name": "...", ... },
  "diagramContent": { "objects": {}, "connections": {}, "comments": {} }
}
```

## Position Objects on Diagram (Replace Content)

```
PUT /landscapes/{landscapeId}/versions/latest/diagrams/{diagramId}/content
```

### Body Structure

```json
{
  "objects": {
    "<modelObjectId>": {
      "id": "<unique-diagram-object-id>",
      "modelId": "<modelObjectId>",
      "type": "system",
      "shape": "box",
      "x": 100,
      "y": 200,
      "width": 200,
      "height": 150
    }
  },
  "connections": {
    "<modelConnectionId>": {
      "id": "<unique-diagram-connection-id>",
      "modelId": "<modelConnectionId>",
      "originId": "<diagram-object-id-of-origin>",
      "targetId": "<diagram-object-id-of-target>",
      "lineShape": "curved",
      "labelPosition": 0.5,
      "points": []
    }
  },
  "comments": {}
}
```

### Shape types
- `box` — standard element (systems, containers, components, actors)
- `area` — boundary/grouping element (groups, system boundaries)

### Typical sizes
- System/Container: width=200, height=150
- Actor: width=150, height=150
- Group/boundary: width=600, height=400 (large enough to contain children)

### Connector positions (where arrows attach)
top-left, top-center, top-right, right-top, right-middle, right-bottom,
bottom-right, bottom-center, bottom-left, left-bottom, left-middle, left-top

### Layout tips
- Space objects ~250px apart horizontally, ~200px apart vertically
- Place actors at top, systems in middle, external systems at bottom/sides
- Use area shapes for groups, sized to contain their children with 50px padding

## Important Gotchas (Learned)

### App-diagram modelId
- `app-diagram` requires `modelId` to be a `system` object ID (not the root object)
- The diagram shows the containers *inside* that system

### Diagram content connections
- `originId`/`targetId` in diagram connections must reference the **key** in the `objects` map (= model object ID), NOT the custom `id` field of diagram objects
- `originConnector` and `targetConnector` are **required** for diagram connections

### Only system children on app-diagrams
- Only model objects that are children of the diagram's system (`parentId` = system ID) can be placed on the diagram
- Root-level objects (actors, external systems) appear as external references automatically
