"""
F1-T2 Live Tests — Cancel Endpoint Verification

Verifies the backend /api/task-cancel/{task_id} endpoint is correctly wired
and responds to POST requests.

Plan: docs/PLAN_Desempenho_UI_Pipeline_Bugs_R2.md — F1-T2
Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f1_t2_cancel_live.py -v -m live
"""

import pytest
import requests

from .conftest import LIVE_URL

pytestmark = [pytest.mark.live]


class TestCancelEndpointSetsFlag:
    """
    POST /api/task-cancel/{task_id} is the backend cancel endpoint added in F6-T1
    (routes_tasks.py). These tests verify it responds correctly for:
    - A non-existent task_id → 404 (task not found — correct, not a 500)
    - If a real running task_id is available → 200 with cancel_requested: true

    The live test for a real running task requires a task to be in flight,
    so we focus on the structural endpoint check (404 for unknown tasks)
    which is deterministic.
    """

    def test_cancel_endpoint_exists_and_responds(self):
        """
        POST /api/task-cancel/{task_id} must return a structured response
        (not a 404 route-not-found or 500 server error).

        For a non-existent task_id the backend should return HTTP 404
        with a JSON body explaining the task was not found — NOT a raw
        HTML error page or unhandled exception.

        This confirms the endpoint is registered in routes_tasks.py.

        RED: would fail if the route doesn't exist at all (FastAPI returns 404
             for unknown routes, but the body would be {"detail": "Not Found"}
             which is distinguishable from a task-not-found 404).
        GREEN: passes once the endpoint is registered and returns JSON.
        """
        fake_task_id = "test-nonexistent-task-f1t2-cancel"
        url = f"{LIVE_URL}/api/task-cancel/{fake_task_id}"

        resp = requests.post(url, timeout=15)

        # The endpoint must exist — a route-not-found would return 404 with
        # {"detail":"Not Found"} which is FastAPI's generic not-found response.
        # A task-not-found from our code returns 404 with a meaningful message.
        # Either 200 (task found) or 404 (task not found) is acceptable —
        # 405 (method not allowed) or 500 (server error) is NOT acceptable.
        assert resp.status_code in (200, 404), (
            f"POST /api/task-cancel/{fake_task_id} returned HTTP {resp.status_code}.\n"
            "Expected 200 (task cancelled) or 404 (task not found).\n"
            "A 405 means the route exists but doesn't accept POST.\n"
            "A 500 means the endpoint crashed.\n"
            f"Response body: {resp.text[:400]}"
        )

        # The response must be JSON
        try:
            body = resp.json()
        except Exception:
            pytest.fail(
                f"POST /api/task-cancel/{fake_task_id} did not return JSON.\n"
                f"Response body: {resp.text[:400]}"
            )

        # If 404, it must NOT be FastAPI's generic route-not-found
        # (which has only {"detail": "Not Found"} with no other keys)
        if resp.status_code == 404:
            assert body != {"detail": "Not Found"}, (
                "The cancel endpoint returned FastAPI's generic 'Not Found' response.\n"
                "This means the route /api/task-cancel/{task_id} is NOT registered.\n"
                "Fix: add the route in routes_tasks.py (F6-T1 implementation).\n"
                f"Full response: {body}"
            )

    def test_cancel_endpoint_returns_cancel_requested_on_valid_task(self):
        """
        When a real running task is cancelled, POST /api/task-cancel/{task_id}
        must return a JSON body containing cancel_requested: true.

        This test uses a known-invalid task_id and asserts the endpoint
        at minimum returns a meaningful JSON response (not a crash).

        Full verification (with a real running task_id) requires a live pipeline
        to be in flight — that is handled by human verification in the MC-1 gate.

        GREEN criterion: endpoint responds with JSON and does not 500.
        """
        fake_task_id = "test-cancel-response-shape-f1t2"
        url = f"{LIVE_URL}/api/task-cancel/{fake_task_id}"

        resp = requests.post(url, timeout=15)

        # Must not crash
        assert resp.status_code != 500, (
            f"POST /api/task-cancel/{fake_task_id} returned 500 — server error.\n"
            f"Response: {resp.text[:400]}"
        )

        # Must return JSON
        try:
            body = resp.json()
        except Exception:
            pytest.fail(
                f"POST /api/task-cancel/{fake_task_id} did not return JSON.\n"
                f"Response body: {resp.text[:400]}"
            )

        # If 200, body must contain cancel_requested key
        if resp.status_code == 200:
            assert "cancel_requested" in body, (
                "Successful cancel response must include 'cancel_requested' key.\n"
                f"Got: {body}"
            )
            assert body["cancel_requested"] is True, (
                "cancel_requested must be True after a successful cancel.\n"
                f"Got: {body['cancel_requested']}"
            )
