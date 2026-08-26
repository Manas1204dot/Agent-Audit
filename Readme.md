# Agent Reliability Capstone — Data Collection Starter


```
(Swap `langchain_anthropic.ChatAnthropic` for `langchain_openai.ChatOpenAI` in
`toy_agent.py` if you'd rather use an OpenAI key — nothing else changes.)

## The three sources of data you actually need

**1. Your own agent's traces (this repo).**
Run `python run_collection.py --repeats 3` — this runs the toy agent
across `tasks.py` three times each, capturing every LLM call and
tool call into `traces.jsonl` via the LangChain callback in
`capture_callback.py`. The `order_lookup` tool is intentionally
flaky ~15% of the time, so you'll get some *natural* failures mixed
in with successful runs, not just clean data.

**2. Synthetic fault injection (this repo).**
Run `python fault_injector.py` — takes the clean traces you just
collected and corrupts them at a known point (wrong tool arg,
hallucinated claim, truncated/swapped tool result, dropped step),
writing `faulty_traces.jsonl` with a `ground_truth` label attached
to every corrupted trace. This is what turns "I built a detector"
into "I can report precision/recall for my detector" — you can't
grade localization accuracy without knowing exactly where you broke
something, and hand-labeling real failures at any volume isn't
realistic on your timeline.

**3. MAST's public dataset (external, don't rebuild this).**
Cemri et al.'s "Why Do Multi-Agent LLM Systems Fail?" (arXiv:2503.13657)
open-sourced ~1,600 annotated traces across 7 popular agent
frameworks, already labeled against their 14-failure-mode taxonomy.
Look for the linked GitHub/HuggingFace repo from the paper's project
page. Use this to (a) validate your localizer generalizes beyond
your one toy agent, and (b) borrow their category labels instead of
inventing your own — cite it, don't reinvent it.

## Suggested collection volume for a capstone
- 100–150 clean traces from your own toy agent (repeats matter —
  they're what let you measure run-to-run consistency later, not
  just single-shot success)
- Equal number of fault-injected traces, evenly spread across the
  5 injection types in `fault_injector.py`
- Cross-check against a subsample of MAST's dataset once your
  pipeline exists

