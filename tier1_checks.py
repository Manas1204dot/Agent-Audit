"""
tier1_checks.py
Deterministic, zero-cost failure checks -- no embeddings, no LLM calls.
Run these on every step of every trace; they're the cheapest, fastest
tier of the localization pipeline. Returns a list of flags per trace,
each pointing at a specific step_id.
"""
import json
from collections import defaultdict


def load_trace_groups(steps: list):
    """steps: flat list of step dicts (already belonging to ONE trace)."""
    return sorted(steps, key=lambda s: s["step_id"])


def check_malformed_tool_call(steps: list) -> list:
    """Flags tool calls with clearly corrupted/placeholder args."""
    flags = []
    for s in steps:
        if s.get("action_type") == "tool_call":
            args = (s.get("tool_call") or {}).get("args")
            if isinstance(args, dict) and args.get("corrupted"):
                flags.append({
                    "step_id": s["step_id"],
                    "check": "malformed_tool_call",
                    "detail": f"tool_call args flagged as corrupted: {args}",
                })
    return flags


def check_contradiction(steps: list) -> list:
    """Flags a tool_call that errored, immediately followed by a
    final_answer that still self-reports success."""
    flags = []
    last_tool_error = None
    for s in steps:
        if s.get("action_type") == "tool_call":
            tr = s.get("tool_result") or {}
            last_tool_error = tr.get("error")
        if s.get("action_type") == "final_answer" and last_tool_error:
            if s.get("self_reported_status") == "success":
                flags.append({
                    "step_id": s["step_id"],
                    "check": "contradiction",
                    "detail": f"final_answer claims success but last tool "
                              f"result was an error: {last_tool_error!r}",
                })
    return flags


def check_repeated_tool_call(steps: list) -> list:
    """Flags the SAME tool called with the SAME args 2+ times in a row
    -- classic loop/stuck-agent symptom."""
    flags = []
    prev = None
    for s in steps:
        if s.get("action_type") == "tool_call":
            tc = s.get("tool_call") or {}
            sig = (tc.get("name"), json.dumps(tc.get("args"), sort_keys=True))
            if prev == sig:
                flags.append({
                    "step_id": s["step_id"],
                    "check": "repeated_tool_call",
                    "detail": f"identical tool call repeated: {sig}",
                })
            prev = sig
    return flags


def check_truncated_result(steps: list, min_len: int = 3) -> list:
    """Flags a tool_result whose output looks suspiciously short given
    the tool succeeded (no error) -- crude but catches obvious truncation."""
    flags = []
    for s in steps:
        if s.get("action_type") == "tool_call":
            tr = s.get("tool_result") or {}
            out = tr.get("output")
            if out is not None and not tr.get("error") and 0 < len(out) < min_len:
                flags.append({
                    "step_id": s["step_id"],
                    "check": "truncated_result",
                    "detail": f"tool output suspiciously short: {out!r}",
                })
    return flags


ALL_CHECKS = [
    check_malformed_tool_call,
    check_contradiction,
    check_repeated_tool_call,
    check_truncated_result,
]


def run_tier1(steps: list) -> list:
    """Runs all Tier 1 checks against one trace's steps, returns combined flags."""
    steps = load_trace_groups(steps)
    all_flags = []
    for check_fn in ALL_CHECKS:
        all_flags.extend(check_fn(steps))
    return all_flags


if __name__ == "__main__":
    # quick smoke test against a hand-built trace
    fake_steps = [
        {"step_id": 0, "action_type": "message", "raw_output": "thinking..."},
        {"step_id": 1, "action_type": "tool_call",
         "tool_call": {"name": "order_lookup", "args": {"corrupted": True}},
         "tool_result": {"output": None, "error": "bad args"}},
        {"step_id": 2, "action_type": "final_answer",
         "raw_output": "Order shipped!", "self_reported_status": "success"},
    ]
    flags = run_tier1(fake_steps)
    for f in flags:
        print(f)