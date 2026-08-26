"""
capture_callback.py
LangChain callback handler that captures every step of an agent run
(LLM calls, tool calls, tool errors, final answer) into TraceStep
records and writes them via TraceWriter.

NOTE: exact callback method signatures vary a bit across LangChain
versions -- if something doesn't fire, check your installed version's
BaseCallbackHandler signature and adjust kwargs accordingly.
"""
import time
from typing import Dict, Optional

from langchain_core.callbacks.base import BaseCallbackHandler

from trace_schema import TraceStep, ToolCall, ToolResult, TraceWriter, new_trace_id


class TraceCaptureCallback(BaseCallbackHandler):
    def __init__(self, writer: TraceWriter, agent_role: str = "agent"):
        self.writer = writer
        self.agent_role = agent_role
        self.trace_id = new_trace_id()
        self.step_counter = 0
        self._tool_start_times: Dict[str, float] = {}
        self._pending_llm_start: Optional[float] = None

    def _next_step_id(self) -> int:
        sid = self.step_counter
        self.step_counter += 1
        return sid

    # ---- LLM lifecycle ----
    def on_llm_start(self, serialized, prompts, **kwargs):
        self._pending_llm_start = time.time()

    def on_llm_end(self, response, **kwargs):
        latency_ms = None
        if self._pending_llm_start:
            latency_ms = (time.time() - self._pending_llm_start) * 1000

        try:
            text_out = response.generations[0][0].text
        except Exception:
            text_out = str(response)

        tokens = None
        usage = getattr(response, "llm_output", None) or {}
        if isinstance(usage, dict):
            token_usage = usage.get("token_usage") or usage.get("usage")
            if token_usage:
                tokens = token_usage.get("total_tokens")

        step = TraceStep(
            trace_id=self.trace_id,
            step_id=self._next_step_id(),
            timestamp=time.time(),
            agent_role=self.agent_role,
            raw_output=text_out,
            action_type="message",
            tokens=tokens,
            latency_ms=latency_ms,
        )
        self.writer.write_step(step)

    # ---- Tool lifecycle ----
    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "unknown_tool")
        self._tool_start_times[tool_name] = time.time()

    def on_tool_end(self, output, **kwargs):
        tool_name = kwargs.get("name", "unknown_tool")
        start = self._tool_start_times.pop(tool_name, None)
        latency_ms = (time.time() - start) * 1000 if start else None

        step = TraceStep(
            trace_id=self.trace_id,
            step_id=self._next_step_id(),
            timestamp=time.time(),
            agent_role=self.agent_role,
            action_type="tool_call",
            tool_call=ToolCall(name=tool_name),
            tool_result=ToolResult(output=str(output), latency_ms=latency_ms),
        )
        self.writer.write_step(step)

    def on_tool_error(self, error, **kwargs):
        tool_name = kwargs.get("name", "unknown_tool")
        step = TraceStep(
            trace_id=self.trace_id,
            step_id=self._next_step_id(),
            timestamp=time.time(),
            agent_role=self.agent_role,
            action_type="tool_call",
            tool_call=ToolCall(name=tool_name),
            tool_result=ToolResult(error=str(error)),
        )
        self.writer.write_step(step)

    # ---- Agent lifecycle ----
    def on_agent_action(self, action, **kwargs):
        tool_input = getattr(action, "tool_input", None)
        args = tool_input if isinstance(tool_input, dict) else {"input": str(tool_input)}
        step = TraceStep(
            trace_id=self.trace_id,
            step_id=self._next_step_id(),
            timestamp=time.time(),
            agent_role=self.agent_role,
            action_type="tool_call",
            tool_call=ToolCall(name=action.tool, args=args),
            raw_output=getattr(action, "log", ""),
        )
        self.writer.write_step(step)

    def on_agent_finish(self, finish, **kwargs):
        output_text = ""
        if hasattr(finish, "return_values"):
            output_text = finish.return_values.get("output", "")
        step = TraceStep(
            trace_id=self.trace_id,
            step_id=self._next_step_id(),
            timestamp=time.time(),
            agent_role=self.agent_role,
            action_type="final_answer",
            raw_output=output_text,
            self_reported_status="success",
        )
        self.writer.write_step(step)