# C4 Diagram Mapping Reference

Quick-reference tables for mapping codebase analysis output to diagram elements.

For full Mermaid C4 syntax and examples, see `knowledge/mermaid/c4-syntax.md`.
For C4 model concepts, see `knowledge/shared/c4-model.md`.

## IcePanel type → Mermaid C4 element

| IcePanel type | external? | Mermaid C4 |
|---|---|---|
| `actor` | — | `Person(id, "name", "desc")` |
| `system` | false | `System(id, "name", "desc")` |
| `system` | true | `System_Ext(id, "name", "desc")` |
| `app` | — | `Container(id, "name", "tech", "desc")` |
| `store` | — | `ContainerDb(id, "name", "tech", "desc")` |
| `component` | — | `Component(id, "name", "tech", "desc")` |
| `group` | — | `System_Boundary(id, "name")` or `Container_Boundary(id, "name")` |

## Codebase module → diagram element

Map `analyze_codebase.py` output using the module's `type` field:

| Module type | IcePanel type | Mermaid C4 |
|---|---|---|
| `API service`, `server`, `backend service` | `app` | `Container(id, "name", "tech", "desc")` |
| `web application`, `frontend` | `app` | `Container(id, "name", "tech", "desc")` |
| `database layer` | `store` | `ContainerDb(id, "name", "tech", "desc")` |
| `background worker`, `message queue consumer` | `app` | `Container(id, "name", "tech", "desc")` |
| `shared library`, `library`, `utilities` | `component` | `Component(id, "name", "tech", "desc")` |
| Other / `module` | `app` | `Container(id, "name", "tech", "desc")` |

Use `technologies[0].name` as the tech label. Use the module `path` as a fallback description.

## Connections

**Mermaid:**
```
Rel(originId, targetId, "label")
Rel(originId, targetId, "label", "technology")
BiRel(originId, targetId, "label")     // bidirectional
```

**IcePanel:** `direction: "outgoing"` or `direction: "bidirectional"`

From codebase analysis, use `connections[].from` → `connections[].to` with label "uses".

## PlantUML C4

Same element names as Mermaid C4. Wrap in `@startuml`/`@enduml` and add `!include <C4/C4_Context>` (or `C4_Container`, `C4_Component`).
