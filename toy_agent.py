"""
toy_agent.py
A deliberately simple agent with 3 tools -- this is the test subject
you'll collect traces from. The order_lookup tool is intentionally
flaky ~15% of the time, so you get some NATURAL failures in your
dataset, not just synthetic ones from fault_injector.py.

NOTE: as of LangChain 1.x, the old initialize_agent()/AgentType API
is gone entirely -- replaced by create_agent() (built on LangGraph
under the hood). Tools are now plain @tool-decorated functions, not
Tool(...) objects, and invocation uses {"messages": [...]} instead
of {"input": ...}. This file targets the current API.
"""
import random
import time

from dotenv import load_dotenv
load_dotenv()  # reads .env into os.environ -- must happen BEFORE any
                # LangChain/Anthropic client is constructed, or the SDK
                # won't find ANTHROPIC_API_KEY at all.

from langchain.agents import create_agent
from langchain_core.tools import tool

from capture_callback import TraceCaptureCallback
from trace_schema import TraceWriter


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. '12*4+1'."""
    try:
        # eval is fine here only because this is a local toy tool with a
        # fixed, trusted input path -- never do this with real user input.
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"error: {e}"


FAKE_ORDERS = {
    "A123": {"status": "shipped", "eta": "2026-08-05"},
    "B456": {"status": "processing", "eta": "2026-08-10"},
}


@tool
def order_lookup(order_id: str) -> str:
    """Look up an order by its ID, e.g. 'A123'. Returns status and ETA."""
    order_id = order_id.strip().upper()
    if random.random() < 0.15:
        time.sleep(0.3)
        return "error: upstream order service timeout"
    if order_id in FAKE_ORDERS:
        return str(FAKE_ORDERS[order_id])
    return f"error: no order found for id {order_id}"


@tool
def weather(city: str) -> str:
    """Get current weather for a city name."""
    fake = {"delhi": "38C, haze", "hyderabad": "33C, partly cloudy", "mumbai": "31C, humid"}
    return fake.get(city.strip().lower(), "error: city not found")


def build_agent(model_name: str = "google_genai:gemini-flash-lite-latest"):
    return create_agent(model_name, tools=[calculator, order_lookup, weather])


def run_one(task: str, trace_path: str = "traces.jsonl"):
    from trace_schema import TraceStep
    import time as _time

    writer = TraceWriter(trace_path)
    callback = TraceCaptureCallback(writer, agent_role="toy_support_agent")
    agent = build_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": task}]},
        config={"callbacks": [callback]},
    )

    # create_agent runs on LangGraph, not the old AgentExecutor loop, so
    # on_agent_finish (written for AgentExecutor's callback events) never
    # fires here. Log the final answer explicitly instead of relying on it.
    final_text = ""
    if result.get("messages"):
        final_text = getattr(result["messages"][-1], "content", "") or ""

    writer.write_step(TraceStep(
        trace_id=callback.trace_id,
        step_id=callback._next_step_id(),
        timestamp=_time.time(),
        agent_role="toy_support_agent",
        action_type="final_answer",
        raw_output=final_text,
        self_reported_status="success",
    ))

    return callback.trace_id, result


if __name__ == "__main__":
    tid, result = run_one(
        "What's the status of order A123, and what's the weather in Hyderabad?"
    )
    print("trace_id:", tid)
    print("result:", result["messages"][-1].content)