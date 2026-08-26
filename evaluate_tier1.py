"""
evaluate_tier1.py
Grades tier1_checks.py against faulty_traces.jsonl's ground-truth
labels, and separately checks false-positive rate on clean traces.
This is the actual evaluation methodology you'll cite in your
capstone report -- precision/recall against a known answer key,
not "it looked right in the demo."
"""
import json
from collections import defaultdict
from tier1_checks import run_tier1


def evaluate_on_faulty(path: str = "faulty_traces.jsonl"):
    total = 0
    caught_step = 0       # flagged the exact injected step_id
    caught_trace = 0      # flagged SOMETHING in the right trace (looser)
    missed = 0
    by_type = defaultdict(lambda: {"total": 0, "exact": 0, "flagged": 0})

    with open(path) as f:
        for line in f:
            record = json.loads(line)
            steps = record["steps"]
            gt = record["ground_truth"]
            total += 1
            metrics = by_type[gt["injection_type"]]
            metrics["total"] += 1

            flags = run_tier1(steps)
            flagged_step_ids = {fl["step_id"] for fl in flags}

            if gt["target_step_id"] in flagged_step_ids:
                caught_step += 1
                caught_trace += 1
                metrics["exact"] += 1
            elif flagged_step_ids:
                caught_trace += 1  # flagged wrong step, but noticed *something*
            else:
                missed += 1
            if flagged_step_ids:
                metrics["flagged"] += 1

    print(f"--- Faulty traces: {total} total ---")
    print(f"Exact step-id recall:      {caught_step}/{total} "
          f"({100*caught_step/max(total,1):.1f}%)")
    print(f"Any-flag-in-trace recall:  {caught_trace}/{total} "
          f"({100*caught_trace/max(total,1):.1f}%)")
    print(f"Completely missed:         {missed}/{total}")
    print("\nBy injection type:")
    for injection_type, metrics in sorted(by_type.items()):
        recall = 100 * metrics["exact"] / max(metrics["total"], 1)
        print(f"  {injection_type}: {metrics['exact']}/{metrics['total']} "
              f"exact ({recall:.1f}%), {metrics['flagged']} flagged")

    return {
        "total": total,
        "exact_localization": caught_step,
        "trace_detected": caught_trace,
        "missed": missed,
        "by_type": dict(by_type),
    }


def evaluate_false_positives(path: str = "traces.jsonl"):
    traces = defaultdict(list)
    with open(path) as f:
        for line in f:
            step = json.loads(line)
            traces[step["trace_id"]].append(step)

    total = len(traces)
    false_positive_traces = 0

    for tid, steps in traces.items():
        flags = run_tier1(steps)
        if flags:
            false_positive_traces += 1

    print(f"\n--- Clean traces: {total} total ---")
    print(f"Flagged something (false positives): {false_positive_traces}/{total} "
          f"({100*false_positive_traces/max(total,1):.1f}%)")
    print("(Some of these may be REAL natural failures from the flaky "
          "order_lookup tool, not true false positives -- worth spot-checking.)")
    return {
        "total": total,
        "false_positive_traces": false_positive_traces,
    }


if __name__ == "__main__":
    evaluate_on_faulty()
    evaluate_false_positives()