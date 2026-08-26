import json
import tempfile
import unittest
from pathlib import Path

from fault_injector import INJECTION_TYPES, inject_fault
from tier1_checks import run_tier1
from trace_schema import TraceStep, TraceWriter


class TraceSchemaTests(unittest.TestCase):
    def test_writer_rejects_tool_step_without_tool_data(self):
        step = TraceStep("trace-1", 0, 0.0, action_type="tool_call")
        with tempfile.TemporaryDirectory() as directory:
            writer = TraceWriter(str(Path(directory) / "traces.jsonl"))
            with self.assertRaises(ValueError):
                writer.write_step(step)

    def test_writer_persists_schema_version(self):
        step = TraceStep("trace-1", 0, 0.0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "traces.jsonl"
            TraceWriter(str(path)).write_step(step)
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(record["schema_version"], 1)


class FaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self.steps = [
            {"trace_id": "trace-1", "step_id": 0, "action_type": "tool_call",
             "tool_call": {"name": "order_lookup", "args": {"order_id": "A123"}},
             "tool_result": {"output": "{'status': 'shipped'}"}},
            {"trace_id": "trace-1", "step_id": 1, "action_type": "message",
             "raw_output": "The order is shipped."},
            {"trace_id": "trace-1", "step_id": 2, "action_type": "tool_call",
             "tool_call": {"name": "weather", "args": {"city": "Delhi"}},
             "tool_result": {"output": "38C, haze"}},
        ]

    def test_every_injection_type_returns_ground_truth(self):
        for injection_type in INJECTION_TYPES:
            with self.subTest(injection_type=injection_type):
                result = inject_fault(self.steps, injection_type=injection_type)
                self.assertIsNotNone(result)
                corrupted, label = result
                self.assertEqual(label["injection_type"], injection_type)
                self.assertNotEqual(corrupted, self.steps)

    def test_unknown_injection_type_is_rejected(self):
        with self.assertRaises(ValueError):
            inject_fault(self.steps, injection_type="unknown")

    def test_new_faults_are_localized(self):
        cases = {
            "truncated_tool_result": self.steps[:1],
            "swapped_tool_result": self.steps,
            "dropped_step": self.steps,
        }
        for injection_type, steps in cases.items():
            with self.subTest(injection_type=injection_type):
                corrupted, label = inject_fault(
                    steps, injection_type=injection_type
                )
                flags = run_tier1(corrupted)
                flagged = {flag["step_id"] for flag in flags}
                self.assertIn(label["target_step_id"], flagged)

    def test_serialized_tool_errors_are_not_marked_truncated(self):
        steps = [{
            "step_id": 0,
            "action_type": "tool_call",
            "tool_call": {"name": "weather", "args": {"city": "Atlantis"}},
            "tool_result": {
                "output": "content='error: city not found' name='weather'"
            },
        }]
        checks = {flag["check"] for flag in run_tier1(steps)}
        self.assertNotIn("truncated_result", checks)
        self.assertNotIn("swapped_tool_result", checks)


if __name__ == "__main__":
    unittest.main()