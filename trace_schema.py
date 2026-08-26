"""
trace_schema.py
Canonical schema for a single agent trace, built from a list of steps.
Every other part of the pipeline (capture, fault injection, localization)
reads/writes this shape, so get this right first.
"""
from dataclasses import dataclass, asdict
from typing import Optional
import json
import uuid


@dataclass
class ToolCall:
    name: Optional[str] = None
    args: Optional[dict] = None


@dataclass
class ToolResult:
    output: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None


@dataclass
class TraceStep:
    trace_id: str
    step_id: int
    timestamp: float
    agent_role: str = "agent"
    input_context: str = ""
    raw_output: str = ""
    action_type: str = "message"  # "tool_call" | "message" | "final_answer"
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    self_reported_status: Optional[str] = None  # "success" | "failure" | None
    tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[float] = None

    def to_dict(self):
        return asdict(self)


class TraceWriter:
    """Appends TraceStep records to a JSONL file. Many steps, many traces,
    one file -- group by trace_id downstream."""

    def __init__(self, path: str):
        self.path = path

    def write_step(self, step: TraceStep):
        with open(self.path, "a") as f:
            f.write(json.dumps(step.to_dict()) + "\n")


def new_trace_id() -> str:
    return str(uuid.uuid4())