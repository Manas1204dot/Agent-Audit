"""
inspect_traces.py
Quick sanity check on traces.jsonl before you trust it for anything.
Run this before fault_injector.py -- garbage in, garbage out.
"""
import json
from collections import defaultdict, Counter


def inspect(path: str = "traces.jsonl"):
    traces = defaultdict(list)
    with open(path) as f:
        for line in f:
            step = json.loads(line)
            traces[step["trace_id"]].append(step)

    print(f"Total traces: {len(traces)}")

    action_counts = Counter()
    tool_error_count = 0
    tool_call_count = 0
    steps_per_trace = []

    for tid, steps in traces.items():
        steps_per_trace.append(len(steps))
        for s in steps:
            action_counts[s.get("action_type")] += 1
            if s.get("action_type") == "tool_call":
                tool_call_count += 1
                tr = s.get("tool_result") or {}
                if tr.get("error"):
                    tool_error_count += 1

    print(f"Steps per trace: min={min(steps_per_trace)}, "
          f"max={max(steps_per_trace)}, avg={sum(steps_per_trace)/len(steps_per_trace):.1f}")
    print(f"Action type breakdown: {dict(action_counts)}")
    print(f"Tool calls: {tool_call_count}, of which errored: {tool_error_count} "
          f"({100*tool_error_count/max(tool_call_count,1):.1f}%)")

    # flag anything obviously broken
    empty_traces = [tid for tid, steps in traces.items() if len(steps) == 0]
    no_final_answer = [tid for tid, steps in traces.items()
                        if not any(s.get("action_type") == "final_answer" for s in steps)]

    if empty_traces:
        print(f"WARNING: {len(empty_traces)} completely empty traces")
    if no_final_answer:
        print(f"WARNING: {len(no_final_answer)} traces never reached a final_answer step "
              f"({[t[:8] for t in no_final_answer]})")


if __name__ == "__main__":
    inspect()