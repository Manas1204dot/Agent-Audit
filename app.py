"""Interactive dashboard for exploring captured agent reliability traces."""
import json
from collections import Counter, defaultdict
from pathlib import Path

import streamlit as st

from tier1_checks import run_tier1


ROOT = Path(__file__).parent
CLEAN_PATH = ROOT / "traces.jsonl"
FAULTY_PATH = ROOT / "faulty_traces.jsonl"

st.set_page_config(
    page_title="Tracewatch | Agent reliability",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root { --ink:#101417; --muted:#7f8b8d; --line:#273034; --paper:#171d20; --lime:#c7f36b; --orange:#ff9b62; --cyan:#83d9d1; }
    .stApp { background:var(--ink); color:#f2f5ed; }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:#151b1e; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top:2rem; }
    h1,h2,h3,p,div,span { font-family:'Manrope', sans-serif; }
    h1 { letter-spacing:0; font-weight:800; font-size:2.2rem; }
    h2 { font-size:1.25rem; margin-top:1.5rem; }
    .mono, code { font-family:'DM Mono', monospace !important; }
    .eyebrow { color:var(--lime); font:500 0.72rem 'DM Mono', monospace; letter-spacing:0; text-transform:uppercase; }
    .subtitle { color:var(--muted); margin-top:-0.8rem; margin-bottom:2rem; }
    .metric { border-top:1px solid var(--line); padding:0.9rem 0 0.55rem; }
    .metric-label { color:var(--muted); font:500 0.7rem 'DM Mono', monospace; text-transform:uppercase; }
    .metric-value { font-size:1.75rem; font-weight:800; line-height:1.2; }
    .metric-note { color:var(--muted); font-size:0.75rem; }
    .section-rule { border-top:1px solid var(--line); margin:1.5rem 0; }
    .status { display:inline-block; padding:0.18rem 0.5rem; border:1px solid; border-radius:2px; font:500 0.68rem 'DM Mono', monospace; text-transform:uppercase; }
    .status-ok { color:var(--lime); border-color:#5e7831; }
    .status-warn { color:var(--orange); border-color:#865033; }
    .step { border-left:2px solid var(--line); padding:0.1rem 0 0.65rem 1rem; margin-left:0.35rem; }
    .step.issue { border-color:var(--orange); }
    .step-head { display:flex; gap:0.65rem; align-items:center; color:#f2f5ed; font-weight:700; }
    .step-number { color:var(--lime); font:500 0.72rem 'DM Mono', monospace; }
    .step-meta { color:var(--muted); font:400 0.72rem 'DM Mono', monospace; margin-top:0.25rem; }
    .finding { background:#201d1a; border-left:2px solid var(--orange); padding:0.7rem 0.85rem; margin:0.5rem 0; }
    .finding-name { color:var(--orange); font:500 0.75rem 'DM Mono', monospace; }
    .finding-detail { color:#c9d0ca; font-size:0.82rem; margin-top:0.25rem; }
    .empty { border:1px dashed var(--line); padding:1.5rem; color:var(--muted); text-align:center; }
    .stButton > button { border-radius:2px; border:1px solid #657838; color:var(--lime); background:transparent; }
    .stButton > button:hover { border-color:var(--lime); color:var(--ink); background:var(--lime); }
    [data-testid="stMetric"] { background:transparent; border:0; padding:0; }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_jsonl(path: Path):
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({"_error": f"Invalid JSON at line {line_number}"})
    return records


def group_clean_steps(records):
    traces = defaultdict(list)
    for record in records:
        if "trace_id" in record:
            traces[record["trace_id"]].append(record)
    return {trace_id: sorted(steps, key=lambda item: item.get("step_id", 0))
            for trace_id, steps in traces.items()}


def text_value(value):
    if isinstance(value, list):
        return " ".join(text_value(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value or "")


def evaluate_faults(records):
    by_type = defaultdict(lambda: {"total": 0, "exact": 0, "flagged": 0})
    exact = detected = total = 0
    for record in records:
        if "steps" not in record or "ground_truth" not in record:
            continue
        total += 1
        truth = record["ground_truth"]
        metrics = by_type[truth["injection_type"]]
        metrics["total"] += 1
        flags = run_tier1(record["steps"])
        ids = {flag["step_id"] for flag in flags}
        if ids:
            detected += 1
            metrics["flagged"] += 1
        if truth["target_step_id"] in ids:
            exact += 1
            metrics["exact"] += 1
    return {"total": total, "exact": exact, "detected": detected, "by_type": dict(by_type)}


def flag_map(steps):
    return {step_id: flags for step_id, flags in _group_flags(run_tier1(steps)).items()}


def _group_flags(flags):
    grouped = defaultdict(list)
    for flag in flags:
        grouped[flag["step_id"]].append(flag)
    return grouped


clean_records = read_jsonl(CLEAN_PATH)
faulty_records = read_jsonl(FAULTY_PATH)
clean_traces = group_clean_steps(clean_records)
fault_metrics = evaluate_faults(faulty_records)

with st.sidebar:
    st.markdown('<div class="eyebrow">Tracewatch / local lab</div>', unsafe_allow_html=True)
    st.markdown("## Agent reliability")
    st.caption("A small, inspectable view into what your agent did, where it struggled, and how well the checks found it.")
    view = st.radio("Workspace", ["Overview", "Trace explorer", "Fault benchmark"], label_visibility="collapsed")
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric"><div class="metric-label">Data source</div><div class="mono">traces.jsonl</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric"><div class="metric-label">Loaded traces</div><div class="metric-value">{len(clean_traces)}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric"><div class="metric-label">Checks</div><div class="mono">TIER 1 / DETERMINISTIC</div></div>', unsafe_allow_html=True)

if view == "Overview":
    st.markdown('<div class="eyebrow">Overview / current run</div>', unsafe_allow_html=True)
    st.title("Reliability, in plain sight.")
    st.markdown('<div class="subtitle">A practical control room for the captured toy support agent.</div>', unsafe_allow_html=True)
    tool_calls = sum(1 for step in clean_records if step.get("action_type") == "tool_call")
    errors = sum(1 for step in clean_records if (step.get("tool_result") or {}).get("error"))
    flagged = sum(1 for steps in clean_traces.values() if run_tier1(steps))
    columns = st.columns(4)
    for column, label, value, note in zip(columns, ["Traces", "Tool calls", "Tool errors", "Flagged clean"], [len(clean_traces), tool_calls, errors, flagged], ["captured runs", "across all runs", "explicit error fields", "needs review"]):
        with column:
            st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

    st.markdown("## Signal summary")
    action_counts = Counter(step.get("action_type", "unknown") for step in clean_records)
    left, right = st.columns([1, 1])
    with left:
        st.markdown("### Captured behavior")
        for action, count in action_counts.items():
            st.markdown(f'<div class="metric"><span class="mono">{action}</span><span style="float:right">{count}</span></div>', unsafe_allow_html=True)
    with right:
        st.markdown("### Detector benchmark")
        if fault_metrics["total"]:
            recall = 100 * fault_metrics["exact"] / fault_metrics["total"]
            st.markdown(f'<div class="metric"><div class="metric-label">Exact localization</div><div class="metric-value">{recall:.1f}%</div><div class="metric-note">{fault_metrics["exact"]} of {fault_metrics["total"]} injected traces</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric"><div class="metric-label">Any detection</div><div class="metric-value">{100 * fault_metrics["detected"] / fault_metrics["total"]:.1f}%</div><div class="metric-note">at least one flagged step</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">No fault dataset loaded.</div>', unsafe_allow_html=True)

elif view == "Trace explorer":
    st.markdown('<div class="eyebrow">Trace explorer / step detail</div>', unsafe_allow_html=True)
    st.title("Follow the run.")
    st.markdown('<div class="subtitle">Select a captured trace and inspect every model message, tool call, and result.</div>', unsafe_allow_html=True)
    query = st.text_input("Filter trace IDs", placeholder="Search by UUID prefix")
    trace_ids = [trace_id for trace_id in clean_traces if query.lower() in trace_id.lower()]
    if not trace_ids:
        st.markdown('<div class="empty">No traces match that filter.</div>', unsafe_allow_html=True)
    else:
        selected = st.selectbox("Trace", trace_ids, format_func=lambda value: value[:8] + "...  /  " + str(len(clean_traces[value])) + " steps")
        steps = clean_traces[selected]
        flags_by_step = flag_map(steps)
        st.markdown(f'<span class="status {"status-warn" if flags_by_step else "status-ok"}">{"needs review" if flags_by_step else "clean"}</span> <span class="mono" style="color:#7f8b8d"> {selected}</span>', unsafe_allow_html=True)
        st.markdown("## Timeline")
        for step in steps:
            step_flags = flags_by_step.get(step.get("step_id"), [])
            action = step.get("action_type", "unknown")
            tool_name = (step.get("tool_call") or {}).get("name")
            title = tool_name or action.replace("_", " ")
            meta = [f"step {step.get('step_id')}"]
            if step.get("latency_ms") is not None:
                meta.append(f"{step['latency_ms']:.0f} ms")
            body = text_value(step.get("raw_output"))
            if step.get("tool_result"):
                result = step["tool_result"]
                body = text_value(result.get("output") or result.get("error"))
            tool_call = step.get("tool_call") or {}
            if tool_call.get("args"):
                body = "args: " + json.dumps(tool_call["args"]) + "\n\n" + body
            issue_class = " issue" if step_flags else ""
            st.markdown(f'<div class="step{issue_class}"><div class="step-head"><span class="step-number">{step.get("step_id"):02d}</span><span>{title}</span></div><div class="step-meta">{" · ".join(meta)}</div><pre>{body}</pre></div>', unsafe_allow_html=True)
            for flag in step_flags:
                st.markdown(f'<div class="finding"><div class="finding-name">{flag["check"]}</div><div class="finding-detail">{flag["detail"]}</div></div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="eyebrow">Fault benchmark / evaluation</div>', unsafe_allow_html=True)
    st.title("Where the checks hold up.")
    st.markdown('<div class="subtitle">Known faults, exact localization, and the cases that still need a smarter tier.</div>', unsafe_allow_html=True)
    if not fault_metrics["total"]:
        st.markdown('<div class="empty">Run fault_injector.py to create a benchmark dataset.</div>', unsafe_allow_html=True)
    else:
        recall = 100 * fault_metrics["exact"] / fault_metrics["total"]
        columns = st.columns(3)
        for column, label, value in zip(columns, ["Injected traces", "Exact localization", "Any detection"], [fault_metrics["total"], f"{recall:.1f}%", f"{100 * fault_metrics['detected'] / fault_metrics['total']:.1f}%"]):
            with column:
                st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
        st.markdown("## By injection type")
        for injection_type, metrics in sorted(fault_metrics["by_type"].items()):
            percentage = 100 * metrics["exact"] / max(metrics["total"], 1)
            st.markdown(f'<div class="metric"><span class="mono">{injection_type}</span><span style="float:right;color:#c7f36b">{percentage:.1f}%</span><div class="metric-note">{metrics["exact"]}/{metrics["total"]} exact · {metrics["flagged"]} flagged</div></div>', unsafe_allow_html=True)
        st.markdown("## Interpretation")
        st.info("Deterministic checks are strongest when the trace violates a structural contract. Ambiguous output corruption may need a semantic or model-assisted tier.")
