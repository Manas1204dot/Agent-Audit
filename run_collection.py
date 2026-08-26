"""
run_collection.py
Batch-runs the toy agent across the task set, N repeats per task, to
build up a raw trace dataset. Repeats matter -- they're what let you
later measure pass^k / run-to-run consistency, not just single-shot
success, which is the exact gap most public benchmarks have.

Usage:
    python run_collection.py --repeats 3 --out traces.jsonl
"""
import argparse
import time

from tasks import TASKS
from toy_agent import run_one


def collect(n_repeats: int = 3, out_path: str = "traces.jsonl", delay_s: float = 1.0):
    log = []
    for task in TASKS:
        for i in range(n_repeats):
            print(f"[run] task={task!r} rep={i}")
            try:
                trace_id, result = run_one(task, trace_path=out_path)
                log.append({"task": task, "rep": i, "trace_id": trace_id, "ok": True})
            except Exception as e:
                print(f"  failed: {e}")
                log.append({"task": task, "rep": i, "trace_id": None, "ok": False, "error": str(e)})
            time.sleep(delay_s)  # be polite to the API / avoid rate limits
    return log


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--out", type=str, default="traces.jsonl")
    args = parser.parse_args()

    summary = collect(n_repeats=args.repeats, out_path=args.out)
    ok = sum(1 for r in summary if r["ok"])
    print(f"\nDone. {ok}/{len(summary)} runs completed. Traces written to {args.out}")