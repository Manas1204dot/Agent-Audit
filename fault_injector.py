"""
fault_injector.py
Takes CLEAN traces (grouped by trace_id) and produces synthetically
corrupted copies with a labeled ground-truth injection point. This
is what you'll evaluate your localization pipeline against later --
you know exactly where the fault is because you put it there
yourself, which is the only way to get precision/recall numbers
without hand-labeling thousands of real failures.

Usage:
    python fault_injector.py
    # reads traces.jsonl, writes faulty_traces.jsonl
"""
import json
import random
import copy
from collections import defaultdict


def load_traces(path: str):
    traces = defaultdict(list)
    with open(path) as f:
        for line in f:
            step = json.loads(line)
            traces[step["trace_id"]].append(step)
    for tid in traces:
        traces[tid].sort(key=lambda s: s["step_id"])
    return traces


INJECTION_TYPES = [
    "wrong_tool_arg",
    "hallucinated_claim",
    "truncated_tool_result",
    "swapped_tool_result",
    "dropped_step",
]


def inject_fault(steps: list, injection_type: str = None, rng: random.Random = None):
    rng = rng or random.Random()
    steps = copy.deepcopy(steps)
    injection_type = injection_type or rng.choice(INJECTION_TYPES)

    tool_step_idxs = [i for i, s in enumerate(steps) if s.get("action_type") == "tool_call"]
    if not tool_step_idxs:
        return None  # nothing to corrupt in this trace

    target_idx = rng.choice(tool_step_idxs)
    label = {
        "injection_type": injection_type,
        "target_step_id": steps[target_idx]["step_id"],
        "trace_id": steps[0]["trace_id"],
    }

    if injection_type == "wrong_tool_arg" and steps[target_idx].get("tool_call"):
        steps[target_idx]["tool_call"]["args"] = {"corrupted": True}

    elif injection_type == "hallucinated_claim":
        # inject an unsupported claim into the next message/final_answer step
        for j in range(target_idx + 1, len(steps)):
            if steps[j].get("action_type") in ("message", "final_answer"):
                steps[j]["raw_output"] = (
                    steps[j].get("raw_output", "")
                    + " (Note: order has been fully refunded and closed.)"
                )
                label["target_step_id"] = steps[j]["step_id"]
                break

    elif injection_type == "truncated_tool_result" and steps[target_idx].get("tool_result"):
        out = steps[target_idx]["tool_result"].get("output") or ""
        steps[target_idx]["tool_result"]["output"] = out[: max(1, len(out) // 3)]

    elif injection_type == "swapped_tool_result" and steps[target_idx].get("tool_result"):
        other_results = [
            s["tool_result"]["output"] for i, s in enumerate(steps)
            if i != target_idx and s.get("tool_result") and s["tool_result"].get("output")
        ]
        if other_results:
            steps[target_idx]["tool_result"]["output"] = rng.choice(other_results)

    elif injection_type == "dropped_step":
        del steps[target_idx]

    return steps, label


def build_fault_dataset(clean_traces_path: str, out_path: str, seed: int = 0):
    rng = random.Random(seed)
    traces = load_traces(clean_traces_path)

    n_written = 0
    with open(out_path, "w") as f:
        for tid, steps in traces.items():
            result = inject_fault(steps, rng=rng)
            if result is None:
                continue
            corrupted_steps, label = result
            f.write(json.dumps({"steps": corrupted_steps, "ground_truth": label}) + "\n")
            n_written += 1

    print(f"Wrote {n_written} fault-injected traces to {out_path}")


if __name__ == "__main__":
    build_fault_dataset("traces.jsonl", "faulty_traces.jsonl")