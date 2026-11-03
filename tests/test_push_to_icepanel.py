"""Tests for skill/scripts/push_to_icepanel.py.

Two layers:

* Unit tests call the payload-building functions directly with ``api_request``
  stubbed out, and pin down the exact shape of what would be sent to IcePanel.
  The diagram-content shape in particular was reverse-engineered against the
  live API (distinct diagram-connection ids, 0-100 label scale, non-empty
  ``points``), so these tests are the record of what "renders" means.

* End-to-end tests run the script as a CLI subprocess against an in-process
  mock of the IcePanel API (``tests/icepanel_mock.py``) and check the wiring in
  ``main()``: ref resolution, parent/child ordering, ``modelRef`` handling,
  flows, and ``--dry-run``.

No third-party dependencies; run with ``python -m unittest discover -s tests``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from icepanel_mock import ROOT_ID, MockIcePanel

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skill" / "scripts" / "push_to_icepanel.py"


def load_script():
    spec = importlib.util.spec_from_file_location("push_to_icepanel", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


push = load_script()


# ---------------------------------------------------------------------------
# Unit tests: api_request is stubbed, we inspect the payload the script built.
# ---------------------------------------------------------------------------


class _Captures:
    """Stub for api_request that records every call and returns {}."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    def __call__(self, method, path, api_key, body=None):
        self.calls.append((method, path, body))
        return {}

    @property
    def last_body(self) -> dict:
        return self.calls[-1][2] or {}


def _populate(objects, connections, ref_to_id, created_connections, exclude_ref=None):
    captures = _Captures()
    with mock.patch.object(push, "api_request", captures):
        push.populate_diagram_content(
            "key", "landscape", "diagram-1",
            objects, connections, ref_to_id, created_connections,
            exclude_ref=exclude_ref,
        )
    return captures


TWO_SYSTEMS = [
    {"ref": "web", "name": "Web", "type": "system"},
    {"ref": "bill", "name": "Billing", "type": "system"},
]
TWO_SYSTEMS_IDS = {"web": "obj-web", "bill": "obj-bill"}


class PopulateDiagramContentTests(unittest.TestCase):
    def test_puts_objects_and_connections_to_the_content_endpoint(self):
        captures = _populate(
            TWO_SYSTEMS, [], TWO_SYSTEMS_IDS,
            [{"id": "conn-1", "originRef": "web", "targetRef": "bill"}],
        )
        method, path, body = captures.calls[-1]
        self.assertEqual(method, "PUT")
        self.assertEqual(path, "/landscapes/landscape/versions/latest/diagrams/diagram-1/content")
        self.assertEqual(set(body), {"objects", "connections", "comments"})
        self.assertEqual(len(body["objects"]), 2)
        self.assertEqual(len(body["connections"]), 1)

    def test_diagram_object_key_id_and_model_id_are_all_the_model_object_id(self):
        body = _populate(TWO_SYSTEMS, [], TWO_SYSTEMS_IDS, []).last_body
        for key, dobj in body["objects"].items():
            self.assertEqual(dobj["id"], key)
            self.assertEqual(dobj["modelId"], key)
        self.assertEqual(set(body["objects"]), {"obj-web", "obj-bill"})

    def test_diagram_connection_has_the_shape_icepanel_renders(self):
        body = _populate(
            TWO_SYSTEMS, [], TWO_SYSTEMS_IDS,
            [{"id": "conn-1", "originRef": "web", "targetRef": "bill"}],
        ).last_body
        (key, dconn), = body["connections"].items()

        # Distinct diagram-connection id (NOT the model connection id), which
        # points at the model connection through modelId.
        self.assertEqual(dconn["id"], key)
        self.assertNotEqual(dconn["id"], "conn-1")
        self.assertEqual(dconn["modelId"], "conn-1")

        # Endpoints are model object ids (== diagram object keys).
        self.assertEqual(dconn["originId"], "obj-web")
        self.assertEqual(dconn["targetId"], "obj-bill")
        self.assertIn(dconn["originId"], body["objects"])
        self.assertIn(dconn["targetId"], body["objects"])

        # Label position is on the 0-100 scale, not 0-1.
        self.assertEqual(dconn["labelPosition"], 50)

        # A line is only drawn when there is a non-empty path.
        self.assertGreaterEqual(len(dconn["points"]), 2)
        for point in dconn["points"]:
            self.assertEqual(set(point), {"x", "y"})

        allowed = {"top-center", "bottom-center", "left-middle", "right-middle"}
        self.assertIn(dconn["originConnector"], allowed)
        self.assertIn(dconn["targetConnector"], allowed)
        self.assertEqual(dconn["lineShape"], "curved")

    def test_points_run_from_origin_anchor_to_target_anchor(self):
        # An actor is laid out on the top row and an internal object below it
        # in the same column, so the connection is vertical.
        objects = [
            {"ref": "user", "name": "User", "type": "actor"},
            {"ref": "api", "name": "API", "type": "system"},
        ]
        ids = {"user": "obj-user", "api": "obj-api"}
        body = _populate(objects, [], ids, [{"id": "c", "originRef": "user", "targetRef": "api"}]).last_body
        (dconn,) = body["connections"].values()
        origin, target = body["objects"]["obj-user"], body["objects"]["obj-api"]

        self.assertEqual((dconn["originConnector"], dconn["targetConnector"]), ("bottom-center", "top-center"))
        first, last = dconn["points"][0], dconn["points"][-1]
        self.assertEqual((first["x"], first["y"]), (origin["x"] + origin["width"] / 2, origin["y"] + origin["height"]))
        self.assertEqual((last["x"], last["y"]), (target["x"] + target["width"] / 2, target["y"]))

    def test_side_by_side_objects_connect_horizontally(self):
        body = _populate(TWO_SYSTEMS, [], TWO_SYSTEMS_IDS, [{"id": "c", "originRef": "web", "targetRef": "bill"}]).last_body
        (dconn,) = body["connections"].values()
        web, bill = body["objects"]["obj-web"], body["objects"]["obj-bill"]
        self.assertEqual(web["y"], bill["y"])
        self.assertLess(web["x"], bill["x"])
        self.assertEqual((dconn["originConnector"], dconn["targetConnector"]), ("right-middle", "left-middle"))

    def test_every_model_connection_between_the_same_pair_gets_its_own_line(self):
        # Regression: "sends request" / "returns response" between the same two
        # boxes used to collapse into one diagram connection (last one won).
        body = _populate(
            TWO_SYSTEMS, [], TWO_SYSTEMS_IDS,
            [
                {"id": "conn-req", "originRef": "web", "targetRef": "bill"},
                {"id": "conn-resp", "originRef": "web", "targetRef": "bill"},
            ],
        ).last_body
        self.assertEqual(len(body["connections"]), 2)
        self.assertEqual({d["modelId"] for d in body["connections"].values()}, {"conn-req", "conn-resp"})
        self.assertEqual(len({d["id"] for d in body["connections"].values()}), 2)

    def test_objects_without_ref_fall_back_to_name_and_are_still_placed(self):
        # Regression: with exclude_ref=None, objects lacking a "ref" key were
        # filtered out because None != None is False. The rest of the script
        # treats a missing ref as "use the name", so this must too.
        objects = [{"name": "Web", "type": "system"}, {"name": "Billing", "type": "system"}]
        ids = {"Web": "obj-web", "Billing": "obj-bill"}
        body = _populate(objects, [], ids, [{"id": "c", "originRef": "Web", "targetRef": "Billing"}]).last_body
        self.assertEqual(set(body["objects"]), {"obj-web", "obj-bill"})
        self.assertEqual(len(body["connections"]), 1)

    def test_exclude_ref_omits_the_diagrams_own_parent_and_its_connections(self):
        # An app-diagram shows the system's children, not the system itself.
        objects = [
            {"ref": "shop", "name": "Shop", "type": "system"},
            {"ref": "api", "name": "API", "type": "app", "parentRef": "shop"},
            {"ref": "db", "name": "DB", "type": "store", "parentRef": "shop"},
            {"ref": "user", "name": "User", "type": "actor"},
        ]
        ids = {"shop": "obj-shop", "api": "obj-api", "db": "obj-db", "user": "obj-user"}
        created = [
            {"id": "c1", "originRef": "api", "targetRef": "db"},
            {"id": "c2", "originRef": "user", "targetRef": "shop"},  # touches the excluded system
        ]
        body = _populate(objects, [], ids, created, exclude_ref="shop").last_body
        self.assertEqual(set(body["objects"]), {"obj-api", "obj-db", "obj-user"})
        self.assertEqual([d["modelId"] for d in body["connections"].values()], ["c1"])

    def test_connection_whose_endpoint_is_not_on_the_diagram_is_skipped(self):
        body = _populate(
            TWO_SYSTEMS, [], TWO_SYSTEMS_IDS,
            [{"id": "c", "originRef": "web", "targetRef": "ghost"}],
        ).last_body
        self.assertEqual(body["connections"], {})


class CreateFlowTests(unittest.TestCase):
    def _create(self, flow):
        captures = _Captures()
        with mock.patch.object(push, "api_request", captures):
            push.create_flow("key", "landscape", flow)
        return captures

    def test_posts_to_flows_endpoint_with_steps_keyed_by_id(self):
        captures = self._create({
            "name": "Checkout", "diagramId": "diag-1",
            "steps": [
                {"id": "s1", "index": 0, "type": "outgoing", "description": "pay", "originId": "a", "targetId": "b"},
                {"id": "s2", "index": 1, "type": "reply", "description": "ok", "originId": "b", "targetId": "a"},
            ],
        })
        method, path, body = captures.calls[-1]
        self.assertEqual((method, path), ("POST", "/landscapes/landscape/versions/latest/flows"))
        self.assertEqual(body["name"], "Checkout")
        self.assertEqual(body["diagramId"], "diag-1")
        self.assertEqual(list(body["steps"]), ["s1", "s2"])

    def test_every_optional_step_key_is_present_null_when_absent(self):
        # IcePanel's flow API rejects steps that merely omit optional keys.
        body = self._create({
            "name": "f", "diagramId": "d",
            "steps": [{"id": "s1", "index": 0, "type": "self-action", "description": "think", "originId": "a"}],
        }).last_body
        step = body["steps"]["s1"]
        for key in ("originId", "targetId", "parentId", "paths", "flowId", "viaId"):
            self.assertIn(key, step, key)
        self.assertEqual(step["originId"], "a")
        for key in ("targetId", "parentId", "paths", "flowId", "viaId"):
            self.assertIsNone(step[key], key)
        self.assertNotIn("detailedDescription", step)

    def test_detailed_description_and_paths_pass_through_when_given(self):
        paths = {"p1": {"name": "Card", "steps": []}, "p2": {"name": "Cash", "steps": []}}
        body = self._create({
            "name": "f", "diagramId": "d",
            "steps": [{
                "id": "s1", "index": 0, "type": "alternate-path", "description": "choose",
                "detailedDescription": "**md**", "paths": paths,
            }],
        }).last_body
        step = body["steps"]["s1"]
        self.assertEqual(step["detailedDescription"], "**md**")
        self.assertEqual(step["paths"], paths)

    def test_flow_without_steps_sends_no_steps_key(self):
        body = self._create({"name": "f", "diagramId": "d"}).last_body
        self.assertNotIn("steps", body)


class CreateDiagramTests(unittest.TestCase):
    def test_model_id_is_the_object_passed_in(self):
        captures = _Captures()
        with mock.patch.object(push, "api_request", captures):
            push.create_diagram("key", "landscape", {"name": "C2", "type": "app-diagram"}, "obj-shop")
        body = captures.last_body
        self.assertEqual(body["modelId"], "obj-shop")
        self.assertEqual(body["type"], "app-diagram")
        self.assertEqual(body["index"], 0)


# ---------------------------------------------------------------------------
# End-to-end: the CLI against a mock IcePanel server.
# ---------------------------------------------------------------------------


def run_cli(server: MockIcePanel, plan: dict, *extra_args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")}
    env.update({
        "ICEPANEL_API_BASE_URL": server.base_url,
        "ICEPANEL_API_KEY": "test-key",
        "ICEPANEL_LANDSCAPE_ID": "land-1",
        "NO_PROXY": "127.0.0.1,localhost",
        "no_proxy": "127.0.0.1,localhost",
    })
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(plan, f)
        plan_path = f.name
    try:
        return subprocess.run(
            [sys.executable, str(SCRIPT), plan_path, *extra_args],
            env=env, capture_output=True, text=True, timeout=60,
        )
    finally:
        os.unlink(plan_path)


def _summary(proc: subprocess.CompletedProcess) -> dict:
    """The JSON block the script prints after '=== Summary ==='."""
    _, _, tail = proc.stdout.partition("=== Summary ===")
    return json.loads(tail)


C2_PLAN = {
    "objects": [
        {"ref": "shop", "name": "Shop", "type": "system", "parentRef": None},
        {"ref": "api", "name": "API", "type": "app", "parentRef": "shop"},
        {"ref": "db", "name": "DB", "type": "store", "parentRef": "shop"},
        {"ref": "user", "name": "User", "type": "actor", "parentRef": None},
    ],
    "connections": [
        {"name": "reads", "originRef": "api", "targetRef": "db"},
        {"name": "uses", "originRef": "user", "targetRef": "shop"},
    ],
    "diagram": {"name": "Shop C2", "type": "app-diagram", "modelRef": "shop"},
}


class MainEndToEndTests(unittest.TestCase):
    def test_context_diagram_attaches_to_root_and_places_everything(self):
        plan = {
            "objects": [
                {"ref": "web", "name": "Web", "type": "system"},
                {"ref": "bill", "name": "Billing", "type": "system"},
            ],
            "connections": [{"name": "calls", "originRef": "web", "targetRef": "bill"}],
            "diagram": {"name": "Context", "type": "context-diagram"},
        }
        with MockIcePanel() as server:
            proc = run_cli(server, plan)
            self.assertEqual(proc.returncode, 0, proc.stderr)

            # Objects are parented to the landscape root.
            for post in server.requests_matching("POST", "/model/objects"):
                self.assertEqual(post["body"]["parentId"], ROOT_ID)
            self.assertEqual(server.requests_matching("POST", "/diagrams")[0]["body"]["modelId"], ROOT_ID)

            content = server.requests_matching("PUT", "/content")[0]["body"]
            self.assertEqual(set(content["objects"]), {server.id_of("objects", "Web"), server.id_of("objects", "Billing")})
            (dconn,) = content["connections"].values()
            self.assertEqual(dconn["modelId"], server.id_of("connections", "calls"))

            summary = _summary(proc)
            self.assertEqual(
                summary["ref_to_id_mapping"],
                {"web": server.id_of("objects", "Web"), "bill": server.id_of("objects", "Billing")},
            )
            self.assertEqual(summary["diagram_created"]["name"], "Context")

    def test_app_diagram_attaches_to_model_ref_and_does_not_draw_that_object(self):
        with MockIcePanel() as server:
            proc = run_cli(server, C2_PLAN)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            shop_id = server.id_of("objects", "Shop")

            # Children are created after, and parented to, the system.
            for name in ("API", "DB"):
                post = next(r for r in server.requests_matching("POST", "/model/objects") if r["body"]["name"] == name)
                self.assertEqual(post["body"]["parentId"], shop_id)

            # Diagram hangs off the system, not the root.
            self.assertEqual(server.requests_matching("POST", "/diagrams")[0]["body"]["modelId"], shop_id)

            # The system itself is not a box on its own diagram; its children and the actor are.
            content = server.requests_matching("PUT", "/content")[0]["body"]
            self.assertNotIn(shop_id, content["objects"])
            self.assertEqual(
                set(content["objects"]),
                {server.id_of("objects", n) for n in ("API", "DB", "User")},
            )
            # Only the connection between placed objects is drawn.
            self.assertEqual(
                [d["modelId"] for d in content["connections"].values()],
                [server.id_of("connections", "reads")],
            )

    def test_app_objects_without_a_parent_system_trigger_a_warning(self):
        plan = {
            "objects": [
                {"ref": "api", "name": "API", "type": "app"},
                {"ref": "db", "name": "DB", "type": "store"},
                {"ref": "user", "name": "User", "type": "actor"},
            ],
            "connections": [],
        }
        with MockIcePanel() as server:
            proc = run_cli(server, plan)
        self.assertIn("Warning", proc.stderr)
        self.assertIn("API", proc.stderr)
        self.assertIn("DB", proc.stderr)
        self.assertNotIn("User", proc.stderr)  # actors may live at root

    def test_flow_targets_the_new_diagram_and_resolves_step_refs(self):
        plan = dict(C2_PLAN)
        plan["flows"] = [{
            "name": "Read path",
            "diagramRef": "_new_",
            "steps": [
                {"id": "s1", "index": 0, "type": "outgoing", "description": "query", "originRef": "api", "targetRef": "db"},
                {"id": "s2", "index": 1, "type": "reply", "description": "rows", "originRef": "db", "targetRef": "api"},
            ],
        }]
        with MockIcePanel() as server:
            proc = run_cli(server, plan)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            flow_post = server.requests_matching("POST", "/flows")[0]["body"]
            self.assertEqual(flow_post["diagramId"], server.id_of("diagrams", "Shop C2"))
            s1 = flow_post["steps"]["s1"]
            self.assertEqual(s1["originId"], server.id_of("objects", "API"))
            self.assertEqual(s1["targetId"], server.id_of("objects", "DB"))
            self.assertIsNone(s1["parentId"])
        self.assertEqual(_summary(proc)["flows_created"][0]["steps"], 2)

    def test_connection_with_unknown_ref_is_skipped_with_a_warning(self):
        plan = {
            "objects": [{"ref": "web", "name": "Web", "type": "system"}],
            "connections": [{"name": "calls", "originRef": "web", "targetRef": "nope"}],
        }
        with MockIcePanel() as server:
            proc = run_cli(server, plan)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(server.requests_matching("POST", "/model/connections"), [])
        self.assertIn("targetRef 'nope' not found", proc.stderr)

    def test_dry_run_makes_no_api_calls(self):
        with MockIcePanel() as server:
            proc = run_cli(server, C2_PLAN, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(server.requests, [])
        self.assertIn("DRY RUN", proc.stdout)
        self.assertIn("Shop C2", proc.stdout)

    def test_api_key_is_sent_as_apikey_authorization_header(self):
        plan = {"objects": [{"ref": "web", "name": "Web", "type": "system"}], "connections": []}
        with MockIcePanel() as server:
            run_cli(server, plan)
            self.assertTrue(server.requests)
            for request in server.requests:
                self.assertEqual(request["authorization"], "ApiKey test-key")


if __name__ == "__main__":
    unittest.main()
