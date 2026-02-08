#!/usr/bin/env python3
"""Push C4 model objects and connections to IcePanel via its REST API.

Reads a JSON plan file describing objects and connections to create,
then creates them in IcePanel and outputs the created IDs.

Usage:
    python push_to_icepanel.py <plan.json> --api-key <key> --org-id <org-id> --landscape-id <id>

    Or use environment variables:
    ICEPANEL_API_KEY, ICEPANEL_ORGANIZATION_ID, ICEPANEL_LANDSCAPE_ID

Plan JSON format:
{
  "objects": [
    {
      "ref": "api",
      "name": "API Server",
      "type": "app",
      "caption": "REST API serving the frontend",
      "parentRef": null,
      "external": false,
      "status": "live",
      "technologyIds": [],
      "teamIds": []
    }
  ],
  "connections": [
    {
      "name": "Sends requests",
      "originRef": "frontend",
      "targetRef": "api",
      "direction": "outgoing",
      "status": "live"
    }
  ],
  "diagram": {
    "name": "System Context",
    "type": "context-diagram"
  }
}

The "ref" field is a local reference used to link connections to objects.
It is NOT sent to IcePanel — only used to resolve originId/targetId.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = os.environ.get("ICEPANEL_API_BASE_URL", "https://api.icepanel.io/v1")


def api_request(method: str, path: str, api_key: str, body: dict | None = None) -> dict:
    """Make an authenticated request to IcePanel API."""
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"ApiKey {api_key}")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"API Error {e.code} {method} {path}: {error_body}", file=sys.stderr)
        raise


def get_root_object_id(api_key: str, landscape_id: str) -> str:
    """Get the root model object ID for a landscape."""
    result = api_request(
        "GET",
        f"/landscapes/{landscape_id}/versions/latest/model/objects?filter[type]=root",
        api_key,
    )
    objects = result.get("modelObjects", [])
    if not objects:
        print("Error: No root object found in landscape", file=sys.stderr)
        sys.exit(1)
    return objects[0]["id"]


def create_model_object(api_key: str, landscape_id: str, obj: dict) -> dict:
    """Create a model object in IcePanel."""
    payload = {
        "name": obj["name"],
        "type": obj["type"],
        "parentId": obj.get("parentId"),
    }

    # Add optional fields if present
    for field in ["caption", "description", "external", "status", "technologyIds", "teamIds", "domainId", "labels"]:
        if field in obj and obj[field] is not None:
            payload[field] = obj[field]

    result = api_request(
        "POST",
        f"/landscapes/{landscape_id}/versions/latest/model/objects",
        api_key,
        payload,
    )
    return result.get("modelObject", result)


def create_model_connection(api_key: str, landscape_id: str, conn: dict) -> dict:
    """Create a model connection in IcePanel."""
    payload = {
        "name": conn["name"],
        "originId": conn["originId"],
        "targetId": conn["targetId"],
        "direction": conn.get("direction", "outgoing"),
    }

    for field in ["description", "status", "technologyIds", "tagIds", "labels"]:
        if field in conn and conn[field] is not None:
            payload[field] = conn[field]

    result = api_request(
        "POST",
        f"/landscapes/{landscape_id}/versions/latest/model/connections",
        api_key,
        payload,
    )
    return result.get("modelConnection", result)


def create_diagram(api_key: str, landscape_id: str, diagram: dict, root_id: str) -> dict:
    """Create a diagram in IcePanel."""
    payload = {
        "name": diagram["name"],
        "type": diagram.get("type", "context-diagram"),
        "modelId": root_id,
        "index": diagram.get("index", 0),
    }

    for field in ["description", "status"]:
        if field in diagram and diagram[field] is not None:
            payload[field] = diagram[field]

    result = api_request(
        "POST",
        f"/landscapes/{landscape_id}/versions/latest/diagrams",
        api_key,
        payload,
    )
    return result.get("diagram", result)


def auto_layout(objects: list[dict], ref_to_id: dict[str, str]) -> dict[str, dict]:
    """Generate auto-layout positions for diagram objects.

    Simple grid layout: actors top row, main objects middle rows,
    external systems bottom row. Groups rendered as area shapes.
    """
    actors = [o for o in objects if o.get("type") == "actor"]
    groups = [o for o in objects if o.get("type") == "group"]
    externals = [o for o in objects if o.get("external") and o.get("type") != "actor"]
    internals = [o for o in objects if not o.get("external") and o.get("type") not in ("actor", "group")]

    diagram_objects: dict[str, dict] = {}
    x_spacing = 280
    y_spacing = 220
    obj_w, obj_h = 200, 150
    actor_w, actor_h = 150, 150
    area_w, area_h = 600, 400

    def place_row(items: list[dict], start_x: int, y: int, w: int, h: int, shape: str = "box"):
        total_width = len(items) * x_spacing
        offset_x = start_x - total_width // 2 + x_spacing // 2
        for i, obj in enumerate(items):
            ref = obj.get("ref", obj["name"])
            model_id = ref_to_id.get(ref)
            if not model_id:
                continue
            diagram_objects[model_id] = {
                "id": f"dobj_{ref}",
                "modelId": model_id,
                "type": obj["type"],
                "shape": shape,
                "x": offset_x + i * x_spacing,
                "y": y,
                "width": w,
                "height": h,
            }

    center_x = max(len(actors), len(internals), len(externals)) * x_spacing // 2 + 100

    # Row 1: actors
    place_row(actors, center_x, 50, actor_w, actor_h)
    # Row 2+: internal objects
    cols = max(3, len(internals))
    for i, obj in enumerate(internals):
        row = i // cols
        col = i % cols
        ref = obj.get("ref", obj["name"])
        model_id = ref_to_id.get(ref)
        if not model_id:
            continue
        total_cols = min(cols, len(internals) - row * cols)
        offset_x = center_x - total_cols * x_spacing // 2 + x_spacing // 2
        diagram_objects[model_id] = {
            "id": f"dobj_{ref}",
            "modelId": model_id,
            "type": obj["type"],
            "shape": "box",
            "x": offset_x + col * x_spacing,
            "y": 250 + row * y_spacing,
            "width": obj_w,
            "height": obj_h,
        }

    # Bottom row: externals
    ext_y = 250 + ((len(internals) - 1) // cols + 1) * y_spacing + 50
    place_row(externals, center_x, ext_y, obj_w, obj_h)

    # Groups as areas (behind their children)
    for grp in groups:
        ref = grp.get("ref", grp["name"])
        model_id = ref_to_id.get(ref)
        if not model_id:
            continue
        diagram_objects[model_id] = {
            "id": f"dobj_{ref}",
            "modelId": model_id,
            "type": "group",
            "shape": "area",
            "x": 50,
            "y": 200,
            "width": area_w,
            "height": area_h,
        }

    return diagram_objects


def create_flow(api_key: str, landscape_id: str, flow: dict) -> dict:
    """Create a flow (sequence diagram) in IcePanel."""
    payload = {
        "name": flow["name"],
        "diagramId": flow["diagramId"],
    }

    for field in ["index", "pinned", "showAllSteps", "showConnectionNames", "labels", "handleId"]:
        if field in flow and flow[field] is not None:
            payload[field] = flow[field]

    # Build steps if provided
    if "steps" in flow and flow["steps"]:
        steps = {}
        for step in flow["steps"]:
            step_id = step["id"]
            step_payload = {
                "description": step["description"],
                "id": step_id,
                "index": step["index"],
                "type": step["type"],
            }

            for field in ["detailedDescription", "originId", "targetId", "viaId", "parentId", "flowId"]:
                if field in step and step[field] is not None:
                    step_payload[field] = step[field]

            # Handle paths for alternate-path and parallel-path steps
            if "paths" in step and step["paths"]:
                step_payload["paths"] = step["paths"]

            steps[step_id] = step_payload
        payload["steps"] = steps

    result = api_request(
        "POST",
        f"/landscapes/{landscape_id}/versions/latest/flows",
        api_key,
        payload,
    )
    return result.get("flow", result)


def resolve_flow_steps(flow: dict, ref_to_id: dict[str, str]) -> dict:
    """Resolve ref-based originRef/targetRef in flow steps to model IDs."""
    if "steps" not in flow:
        return flow

    for step in flow["steps"]:
        # Resolve originRef -> originId
        if "originRef" in step and step["originRef"]:
            origin_ref = step["originRef"]
            if origin_ref in ref_to_id:
                step["originId"] = ref_to_id[origin_ref]
            else:
                print(f"  Warning: flow step originRef '{origin_ref}' not found", file=sys.stderr)

        # Resolve targetRef -> targetId
        if "targetRef" in step and step["targetRef"]:
            target_ref = step["targetRef"]
            if target_ref in ref_to_id:
                step["targetId"] = ref_to_id[target_ref]
            else:
                print(f"  Warning: flow step targetRef '{target_ref}' not found", file=sys.stderr)

    return flow


def populate_diagram_content(
    api_key: str,
    landscape_id: str,
    diagram_id: str,
    objects: list[dict],
    connections: list[dict],
    ref_to_id: dict[str, str],
    connection_ids: list[dict],
) -> dict:
    """Place objects and connections on the diagram canvas."""
    diagram_objects = auto_layout(objects, ref_to_id)

    # Build diagram connection map
    diagram_connections: dict[str, dict] = {}
    for conn_info in connection_ids:
        conn_id = conn_info["id"]
        origin_ref = conn_info.get("originRef", "")
        target_ref = conn_info.get("targetRef", "")
        origin_model_id = ref_to_id.get(origin_ref, "")
        target_model_id = ref_to_id.get(target_ref, "")

        origin_dobj = diagram_objects.get(origin_model_id, {})
        target_dobj = diagram_objects.get(target_model_id, {})

        if origin_dobj and target_dobj:
            diagram_connections[conn_id] = {
                "id": f"dconn_{origin_ref}_{target_ref}",
                "modelId": conn_id,
                "originId": origin_dobj["id"],
                "targetId": target_dobj["id"],
                "lineShape": "curved",
                "labelPosition": 0.5,
                "points": [],
            }

    payload = {
        "objects": diagram_objects,
        "connections": diagram_connections,
        "comments": {},
    }

    result = api_request(
        "PUT",
        f"/landscapes/{landscape_id}/versions/latest/diagrams/{diagram_id}/content",
        api_key,
        payload,
    )
    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Push C4 model to IcePanel")
    parser.add_argument("plan_file", help="Path to plan JSON file")
    parser.add_argument("--api-key", default=os.environ.get("ICEPANEL_API_KEY", os.environ.get("API_KEY")))
    parser.add_argument("--org-id", default=os.environ.get("ICEPANEL_ORGANIZATION_ID", os.environ.get("ORGANIZATION_ID")))
    parser.add_argument("--landscape-id", default=os.environ.get("ICEPANEL_LANDSCAPE_ID"))
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without calling API")

    args = parser.parse_args()

    if not args.api_key:
        print("Error: --api-key or ICEPANEL_API_KEY / API_KEY env var required", file=sys.stderr)
        sys.exit(1)

    with open(args.plan_file) as f:
        plan = json.load(f)

    # If no landscape ID, list landscapes and let user pick
    if not args.landscape_id:
        if not args.org_id:
            print("Error: --org-id or ICEPANEL_ORGANIZATION_ID env var required to list landscapes", file=sys.stderr)
            sys.exit(1)
        result = api_request("GET", f"/organizations/{args.org_id}/landscapes", args.api_key)
        landscapes = result.get("landscapes", result) if isinstance(result, dict) else result
        if isinstance(landscapes, list):
            print("Available landscapes:")
            for ls in landscapes:
                name = ls.get("name", "unnamed")
                lid = ls.get("id", "?")
                print(f"  - {name} (id: {lid})")
            print("\nRe-run with --landscape-id <id>", file=sys.stderr)
        else:
            print(f"Landscapes response: {json.dumps(result, indent=2)}")
        sys.exit(1)

    landscape_id = args.landscape_id

    if args.dry_run:
        print("=== DRY RUN ===")
        print(f"Landscape: {landscape_id}")
        print(f"\nObjects to create ({len(plan.get('objects', []))}):")
        for obj in plan.get("objects", []):
            print(f"  [{obj['type']}] {obj['name']} (ref: {obj.get('ref', 'none')})")
        print(f"\nConnections to create ({len(plan.get('connections', []))}):")
        for conn in plan.get("connections", []):
            print(f"  {conn.get('originRef', '?')} --({conn['name']})--> {conn.get('targetRef', '?')}")
        if plan.get("diagram"):
            print(f"\nDiagram: {plan['diagram']['name']} ({plan['diagram'].get('type', 'context-diagram')})")
        if plan.get("flows"):
            print(f"\nFlows to create ({len(plan['flows'])}):")
            for flow in plan["flows"]:
                print(f"  Flow: {flow['name']} (on diagram: {flow.get('diagramRef', flow.get('diagramId', '?'))})")
                for step in flow.get("steps", []):
                    step_type = step.get("type", "?")
                    desc = step.get("description", "")
                    origin = step.get("originRef", "")
                    target = step.get("targetRef", "")
                    indent = "    "
                    if step.get("parentId"):
                        indent = "      "
                    if step_type in ("outgoing", "reply"):
                        print(f"{indent}[{step['index']}] ({step_type}) {origin} → {target}: {desc}")
                    elif step_type == "self-action":
                        print(f"{indent}[{step['index']}] ({step_type}) {origin}: {desc}")
                    elif step_type in ("alternate-path", "parallel-path"):
                        paths = step.get("paths", {})
                        path_names = [p.get("name", "?") for p in paths.values()] if isinstance(paths, dict) else []
                        print(f"{indent}[{step['index']}] ({step_type}) {desc} → paths: {', '.join(path_names)}")
                    else:
                        print(f"{indent}[{step['index']}] ({step_type}) {desc}")
        return

    # Get root object ID
    print(f"Fetching root object for landscape {landscape_id}...")
    root_id = get_root_object_id(args.api_key, landscape_id)
    print(f"Root object: {root_id}")

    # Create objects, tracking ref -> created ID mapping
    # Seed with any pre-existing refs from the plan
    ref_to_id: dict[str, str] = dict(plan.get("existing_refs", {}))
    created_objects = []

    # First pass: create objects without parents or with root parent
    # Second pass: create child objects (parentRef points to another ref)
    objects = plan.get("objects", [])

    # Sort: root-level objects first, then children
    root_objects = [o for o in objects if not o.get("parentRef")]
    child_objects = [o for o in objects if o.get("parentRef")]

    for obj in root_objects:
        obj["parentId"] = root_id
        print(f"Creating [{obj['type']}] {obj['name']}...")
        result = create_model_object(args.api_key, landscape_id, obj)
        created_id = result.get("id", "?")
        ref = obj.get("ref", obj["name"])
        ref_to_id[ref] = created_id
        created_objects.append({"ref": ref, "id": created_id, "name": obj["name"]})
        print(f"  Created: {created_id}")

    for obj in child_objects:
        parent_ref = obj["parentRef"]
        if parent_ref not in ref_to_id:
            print(f"  Warning: parentRef '{parent_ref}' not found, using root", file=sys.stderr)
            obj["parentId"] = root_id
        else:
            obj["parentId"] = ref_to_id[parent_ref]
        print(f"Creating [{obj['type']}] {obj['name']} (parent: {parent_ref})...")
        result = create_model_object(args.api_key, landscape_id, obj)
        created_id = result.get("id", "?")
        ref = obj.get("ref", obj["name"])
        ref_to_id[ref] = created_id
        created_objects.append({"ref": ref, "id": created_id, "name": obj["name"]})
        print(f"  Created: {created_id}")

    # Create connections
    created_connections = []
    for conn in plan.get("connections", []):
        origin_ref = conn.get("originRef", "")
        target_ref = conn.get("targetRef", "")

        if origin_ref not in ref_to_id:
            print(f"  Warning: originRef '{origin_ref}' not found, skipping", file=sys.stderr)
            continue
        if target_ref not in ref_to_id:
            print(f"  Warning: targetRef '{target_ref}' not found, skipping", file=sys.stderr)
            continue

        conn["originId"] = ref_to_id[origin_ref]
        conn["targetId"] = ref_to_id[target_ref]

        print(f"Creating connection: {origin_ref} -> {target_ref} ({conn['name']})...")
        result = create_model_connection(args.api_key, landscape_id, conn)
        created_id = result.get("id", "?")
        created_connections.append({
            "id": created_id,
            "name": conn["name"],
            "originRef": origin_ref,
            "targetRef": target_ref,
        })
        print(f"  Created: {created_id}")

    # Create diagram if specified and populate it with objects + connections
    created_diagram = None
    if plan.get("diagram"):
        print(f"Creating diagram: {plan['diagram']['name']}...")
        result = create_diagram(args.api_key, landscape_id, plan["diagram"], root_id)
        diagram_id = result.get("id", "?")
        created_diagram = {"id": diagram_id, "name": plan["diagram"]["name"]}
        print(f"  Created: {diagram_id}")

        # Populate diagram content: position objects and draw connections
        if diagram_id != "?" and (created_objects or created_connections):
            print(f"Populating diagram with {len(created_objects)} objects and {len(created_connections)} connections...")
            try:
                populate_diagram_content(
                    args.api_key,
                    landscape_id,
                    diagram_id,
                    objects,
                    plan.get("connections", []),
                    ref_to_id,
                    created_connections,
                )
                print("  Diagram content populated successfully")
            except Exception as e:
                print(f"  Warning: Failed to populate diagram content: {e}", file=sys.stderr)

    # Create flows if specified
    created_flows = []
    for flow_def in plan.get("flows", []):
        # Resolve diagramRef to diagram ID
        if "diagramRef" in flow_def and flow_def["diagramRef"] == "_new_" and created_diagram:
            flow_def["diagramId"] = created_diagram["id"]
        elif "diagramRef" in flow_def:
            # diagramRef could be a known diagram ID passed directly
            flow_def["diagramId"] = flow_def["diagramRef"]

        if "diagramId" not in flow_def or not flow_def["diagramId"]:
            print(f"  Warning: Flow '{flow_def['name']}' has no diagramId, skipping", file=sys.stderr)
            continue

        # Resolve step refs to model IDs
        resolve_flow_steps(flow_def, ref_to_id)

        print(f"Creating flow: {flow_def['name']}...")
        try:
            result = create_flow(args.api_key, landscape_id, flow_def)
            flow_id = result.get("id", "?")
            step_count = len(flow_def.get("steps", []))
            created_flows.append({"id": flow_id, "name": flow_def["name"], "steps": step_count})
            print(f"  Created: {flow_id} ({step_count} steps)")
        except Exception as e:
            print(f"  Warning: Failed to create flow '{flow_def['name']}': {e}", file=sys.stderr)

    # Output summary
    print("\n=== Summary ===")
    print(json.dumps({
        "objects_created": created_objects,
        "connections_created": created_connections,
        "diagram_created": created_diagram,
        "flows_created": created_flows,
        "ref_to_id_mapping": ref_to_id,
    }, indent=2))


if __name__ == "__main__":
    main()
