"""Tracewatch — Agent Reliability Dashboard."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import streamlit as st

from tier1_checks import run_tier1


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).parent
CLEAN_PATH = ROOT / "traces.jsonl"
FAULTY_PATH = ROOT / "faulty_traces.jsonl"

st.set_page_config(
    page_title="Tracewatch",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# GLOBAL VISUAL SYSTEM
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap'
    );

    :root {
        --cream: #f5f1eb;
        --paper: #fbfaf7;
        --white: #ffffff;

        --black: #111111;
        --dark: #242220;

        --gray: #77726c;
        --light-gray: #aaa39b;

        --line: #e5dfd7;
        --line-dark: #d8d0c6;

        --red: #e43d32;
        --red-dark: #c92f28;
        --red-soft: #f9ded9;

        --green: #3f8d68;
        --green-soft: #dceee4;

        --shadow:
            0 18px 50px rgba(48, 39, 30, .09);
    }


    /* --------------------------------------------------------
       APP
    -------------------------------------------------------- */

    .stApp {
        background: var(--cream);
        color: var(--black);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.2rem;
        padding-bottom: 5rem;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu,
    footer {
        visibility: hidden;
    }


    /* --------------------------------------------------------
       TYPOGRAPHY
    -------------------------------------------------------- */

    h1,
    h2,
    h3 {
        font-family: "Space Grotesk", sans-serif !important;
        color: var(--black) !important;
    }

    h1 {
        font-size: clamp(
            3.2rem,
            7vw,
            6.5rem
        ) !important;

        line-height: .91 !important;

        letter-spacing: -.075em !important;

        font-weight: 600 !important;

        margin-top: 0 !important;
        margin-bottom: 20px !important;
    }

    h2 {
        font-size: 2rem !important;
        letter-spacing: -.05em !important;
        margin-top: 0 !important;
    }

    h3 {
        font-size: 1.2rem !important;
    }

    p,
    label,
    span,
    div {
        font-family: "DM Sans", sans-serif;
    }

    .mono {
        font-family: "IBM Plex Mono", monospace !important;
    }



    /* REAL NAVIGATION */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 5px !important;
        margin: 5px 0 18px !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        min-height: 34px !important;
        padding: 8px 10px !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
        color: #5f5953 !important;
        background: transparent !important;
        font-size: 11px !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: #f8f5f0 !important;
        border-color: #ddd5cc !important;
        color: #171513 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
        background: #f3dfda !important;
        border-color: #e7c5bf !important;
        color: #171513 !important;
        font-weight: 600 !important;
    }

    /* --------------------------------------------------------
       TOP NAV
    -------------------------------------------------------- */

    .tw-nav {
        width: 100%;

        display: flex;
        align-items: center;
        justify-content: space-between;

        padding:
            12px 4px
            22px 4px;

        border-bottom:
            1px solid
            rgba(17,17,17,.09);

        margin-bottom: 60px;
    }

    .tw-logo {
        display: flex;
        align-items: center;
        gap: 9px;

        color: var(--black);

        font-family:
            "Space Grotesk",
            sans-serif;

        font-size: 17px;
        font-weight: 700;

        letter-spacing: -.04em;
    }

    .tw-logo-mark {
        width: 27px;
        height: 27px;

        border-radius: 7px;

        background: var(--red);

        color: white;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 12px;

        box-shadow:
            0 4px 12px
            rgba(228,61,50,.22);
    }

    .tw-nav-center {
        display: flex;
        gap: 35px;

        color: #77716b;

        font-size: 11px;
    }

    .tw-nav-right {
        display: flex;
        align-items: center;
        gap: 16px;

        font-size: 11px;
        color: #55504a;
    }

    .tw-nav-button {
        padding:
            9px 17px;

        background: var(--red);

        color: white;

        border-radius: 999px;

        font-size: 10px;
        font-weight: 600;

        box-shadow:
            0 5px 14px
            rgba(228,61,50,.18);
    }


    /* --------------------------------------------------------
       BACKGROUND PATTERN
    -------------------------------------------------------- */

    .tw-background {
        position: relative;
    }

    .tw-background::before {
        content: "";

        position: absolute;

        top: 40px;
        right: -90px;

        width: 440px;
        height: 440px;

        background-image:
            radial-gradient(
                ellipse,
                rgba(228,61,50,.17) 0 38%,
                transparent 40%
            );

        background-size:
            34px 25px;

        transform:
            rotate(-16deg);

        opacity: .55;

        pointer-events: none;
    }


    /* --------------------------------------------------------
       HERO
    -------------------------------------------------------- */

    .tw-hero {
        position: relative;

        min-height: 520px;

        display: flex;
        flex-direction: column;

        align-items: center;
        text-align: center;

        justify-content: center;

        overflow: hidden;

        padding:
            45px 20px
            80px;

        border-radius: 28px;

        background:
            rgba(251,250,247,.55);
    }

    .tw-eyebrow {
        display: inline-flex;

        align-items: center;
        gap: 7px;

        padding:
            8px 14px;

        border-radius: 999px;

        border:
            1px solid
            rgba(228,61,50,.24);

        background:
            rgba(228,61,50,.06);

        color:
            var(--red-dark);

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size: 9px;

        letter-spacing: .02em;

        margin-bottom: 28px;
    }

    .tw-eyebrow-dot {
        width: 6px;
        height: 6px;

        border-radius: 50%;

        background: var(--red);
    }

    .tw-hero-title {
        position: relative;

        z-index: 2;

        max-width: 920px;

        font-family:
            "Space Grotesk",
            sans-serif;

        font-size:
            clamp(
                3.5rem,
                7vw,
                6.5rem
            );

        line-height: .9;

        letter-spacing: -.075em;

        font-weight: 600;

        color: var(--black);
    }

    .tw-hero-title .accent {
        color: var(--red);

        position: relative;

        display: inline-block;
    }

    .tw-hero-title .accent::after {
        content: "";

        position: absolute;

        left: 2%;
        right: 0;

        bottom: -5px;

        height: 3px;

        background:
            var(--red);

        transform:
            rotate(-1deg);
    }

    .tw-hero-copy {
        max-width: 580px;

        color: #77716b;

        font-size: 14px;

        line-height: 1.65;

        margin-top: 24px;

        z-index: 2;
    }


    /* --------------------------------------------------------
       FLOATING CARDS
    -------------------------------------------------------- */

    .tw-floating-grid {
        width: 100%;

        max-width: 1980px;

        display: grid;

        grid-template-columns:
            1.4fr .8fr .8fr;

        gap: 10px;

        margin-top: 60px;

        position: relative;

        z-index: 3;
    }

    .tw-float-card {
        min-height: 245px;

        padding: 20px;

        background:
            rgba(255,255,255,.82);

        border:
            1px solid
            rgba(17,17,17,.07);

        border-radius:
            15px;

        box-shadow:
            0 20px 40px
            rgba(55,44,32,.07);

        text-align: left;

        transition:
            transform .2s ease,
            box-shadow .2s ease;
    }

    .tw-float-card:hover {
        transform:
            translateY(-5px);

        box-shadow:
            0 25px 45px
            rgba(55,44,32,.12);
    }

    .tw-float-card.large {
        min-height: 180px;
    }

    .tw-icon {
        width: 30px;
        height: 30px;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 8px;

        background:
            var(--red-soft);

        color:
            var(--red);

        font-size: 14px;

        margin-bottom: 20px;
    }

    .tw-float-title {
        color:
            var(--black);

        font-size:
            13px;

        font-weight:
            600;
    }

    .tw-float-description {
        color:
            #858079;

        font-size:
            10px;

        margin-top:
            4px;

        line-height:
            1.45;
    }


    /* --------------------------------------------------------
       SECTION
    -------------------------------------------------------- */

    .tw-section {
        margin-top: 100px;
    }

    .tw-section-header {
        display: flex;

        justify-content: space-between;

        align-items: end;

        margin-bottom: 25px;
    }

    .tw-section-label {
        color:
            var(--red);

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            9px;

        letter-spacing:
            .06em;

        margin-bottom:
            8px;

        text-transform:
            uppercase;
    }

    .tw-section-title {
        font-family:
            "Space Grotesk",
            sans-serif;

        color:
            var(--black);

        font-size:
            34px;

        font-weight:
            600;

        letter-spacing:
            -.06em;
    }

    .tw-section-description {
        max-width:
            390px;

        color:
            #817b74;

        font-size:
            11px;

        line-height:
            1.55;

        text-align:
            right;
    }


    /* --------------------------------------------------------
       METRIC CARDS
    -------------------------------------------------------- */

    .tw-metrics {
        display:
            grid;

        grid-template-columns:
            repeat(4,1fr);

        gap:
            10px;
    }

    .tw-metric {
        position:
            relative;

        overflow:
            hidden;

        padding:
            23px;

        min-height:
            145px;

        border:
            1px solid
            var(--line);

        background:
            rgba(255,255,255,.66);

        border-radius:
            15px;

        transition:
            transform .2s ease,
            background .2s ease;
    }

    .tw-metric:hover {
        transform:
            translateY(-3px);

        background:
            rgba(255,255,255,.95);
    }

    .tw-metric::after {
        content: "";

        position:
            absolute;

        width:
            100px;

        height:
            100px;

        right:
            -45px;

        bottom:
            -50px;

        border-radius:
            50%;

        background:
            rgba(228,61,50,.08);
    }


    /* Slightly larger result boxes: Exact Localization + Any Detection */
    .tw-metric:has(.tw-metric-label-strong) {
    min-height: 156px !important;
    min-width: 280px !important;
    padding: 24px 22px !important;
    }

    .tw-metric:has(.tw-metric-label-strong) .tw-metric-value {
        font-size: 3.05rem !important;
    }

    .tw-metric:has(.tw-metric-label-strong) .tw-metric-note {
        margin-top: 10px !important;
    }

    .tw-metric-label-strong {
        color: #2a2926 !important;
        font-weight: 700 !important;
    }

    .tw-metric-label {
        color:
            #8b857e;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            8px;

        letter-spacing:
            .04em;
    }

    .tw-metric-value {
        margin-top:
            13px;

        color:
            var(--black);

        font-family:
            "Space Grotesk",
            sans-serif;

        font-size:
            34px;

        font-weight:
            600;

        letter-spacing:
            -.055em;
    }

    .tw-metric-note {
        margin-top:
            2px;

        color:
            #a19a92;

        font-size:
            9px;
    }


    /* --------------------------------------------------------
       PANELS
    -------------------------------------------------------- */

    .tw-panel {
        padding:
            23px;

        border:
            1px solid
            var(--line);

        background:
            rgba(255,255,255,.6);

        border-radius:
            16px;
    }

    .tw-panel-title {
        color:
            var(--black);

        font-family:
            "Space Grotesk",
            sans-serif;

        font-size:
            15px;

        font-weight:
            600;

        margin-bottom:
            22px;
    }


    /* --------------------------------------------------------
       BARS
    -------------------------------------------------------- */

    .tw-bar-row {
        margin-bottom:
            19px;
    }

    .tw-bar-header {
        display:
            flex;

        justify-content:
            space-between;

        margin-bottom:
            7px;
    }

    .tw-bar-label {
        color:
            #5f5a55;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            9px;
    }

    .tw-bar-number {
        color:
            #918a82;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            9px;
    }

    .tw-bar {
        height:
            5px;

        border-radius:
            999px;

        background:
            #ebe5de;

        overflow:
            hidden;
    }

    .tw-bar-fill {
        height:
            100%;

        border-radius:
            999px;

        background:
            var(--red);
    }


    /* --------------------------------------------------------
       TRACE
    -------------------------------------------------------- */

    .tw-trace-header {
        display:
            flex;

        align-items:
            center;

        justify-content:
            space-between;

        padding:
            16px 18px;

        margin:
            20px 0 30px;

        border:
            1px solid
            var(--line);

        border-radius:
            13px;

        background:
            rgba(255,255,255,.6);
    }

    .tw-trace-label {
        color:
            #98918a;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            8px;

        letter-spacing:
            .05em;
    }

    .tw-trace-id {
        color:
            #46413d;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            10px;

        margin-top:
            5px;
    }

    .tw-status {
        padding:
            6px 10px;

        border-radius:
            999px;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            8px;
    }

    .tw-status.clean {
        color:
            var(--green);

        background:
            var(--green-soft);
    }

    .tw-status.issue {
        color:
            var(--red);

        background:
            var(--red-soft);
    }


    /* --------------------------------------------------------
       TIMELINE
    -------------------------------------------------------- */

    .tw-timeline {
        position:
            relative;

        margin-top:
            25px;
    }

    .tw-step {
        position:
            relative;

        display:
            grid;

        grid-template-columns:
            35px 1fr;

        gap:
            10px;

        min-height:
            105px;
    }

    .tw-step-line {
        position:
            absolute;

        left:
            5px;

        top:
            13px;

        bottom:
            -10px;

        width:
            1px;

        background:
            #ded7cf;
    }

    .tw-step:last-child
    .tw-step-line {
        display:
            none;
    }

    .tw-step-dot {
        position:
            relative;

        width:
            11px;

        height:
            11px;

        margin-top:
            4px;

        border-radius:
            50%;

        background:
            var(--cream);

        border:
            2px solid
            var(--red);

        z-index:
            2;
    }

    .tw-step-content {
        padding-bottom:
            22px;
    }

    .tw-step-heading {
        display:
            flex;

        align-items:
            center;

        gap:
            9px;
    }

    .tw-step-number {
        color:
            var(--red);

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            8px;
    }

    .tw-step-title {
        color:
            var(--black);

        font-size:
            12px;

        font-weight:
            600;
    }

    .tw-step-meta {
        color:
            #aaa29a;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            8px;

        margin-top:
            4px;
    }

    .tw-step-body {
        margin-top:
            9px;

        padding:
            12px;

        border:
            1px solid
            #e5dfd7;

        border-radius:
            9px;

        background:
            #f6f2ed;

        color:
            #756f68;

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            9px;

        line-height:
            1.6;

        white-space:
            pre-wrap;

        overflow:
            auto;
    }

    .tw-issue {
        margin:
            -4px 0
            20px 45px;

        padding:
            12px 14px;

        border-left:
            2px solid
            var(--red);

        border-radius:
            0 8px 8px 0;

        background:
            var(--red-soft);
    }

    .tw-issue-title {
        color:
            var(--red-dark);

        font-family:
            "IBM Plex Mono",
            monospace;

        font-size:
            8px;

        text-transform:
            uppercase;
    }

    .tw-issue-detail {
        color:
            #8b655f;

        font-size:
            10px;

        line-height:
            1.45;

        margin-top:
            3px;
    }


    /* --------------------------------------------------------
       INPUTS
    -------------------------------------------------------- */

    [data-testid="stTextInput"] input {
        background:
            rgba(255,255,255,.75) !important;

        color:
            var(--black) !important;

        border:
            1px solid
            var(--line-dark) !important;

        border-radius:
            9px !important;

        font-family:
            "DM Sans",
            sans-serif !important;
    }

    [data-testid="stTextInput"] input:focus {
        border-color:
            var(--red) !important;

        box-shadow:
            0 0 0 2px
            rgba(228,61,50,.08) !important;
    }

    [data-testid="stSelectbox"] > div {
        background:
            rgba(255,255,255,.75) !important;

        border:
            1px solid
            var(--line-dark) !important;

        border-radius:
            9px !important;
    }


    /* --------------------------------------------------------
       BUTTON
    -------------------------------------------------------- */

    .stButton > button {
        background:
            var(--red);

        color:
            white;

        border:
            none;

        border-radius:
            999px;

        font-size:
            11px;

        font-weight:
            600;
    }

    .stButton > button:hover {
        background:
            var(--red-dark);

        color:
            white;

        border:
            none;

        transform:
            translateY(-1px);
    }


    /* --------------------------------------------------------
       STREAMLIT SPACING
    -------------------------------------------------------- */

    [data-testid="column"] {
        padding-left:
            5px !important;

        padding-right:
            5px !important;
    }

    [data-testid="stAlert"] {
        background:
            rgba(255,255,255,.7);

        border:
            1px solid
            var(--line);

        color:
            #5e5954;
    }


    /* --------------------------------------------------------
       MOBILE
    -------------------------------------------------------- */

    @media(max-width: 850px) {

        .tw-nav-center {
            display:
                none;
        }

        .tw-floating-grid {
            grid-template-columns:
                1fr;
        }

        .tw-metrics {
            grid-template-columns:
                1fr 1fr;
        }

        .tw-section-header {
            display:
                block;
        }

        .tw-section-description {
            text-align:
                left;

            margin-top:
                10px;
        }

    }

    @media(max-width: 550px) {

        .tw-metrics {
            grid-template-columns:
                1fr;
        }

        .tw-hero {
            min-height:
                480px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HTML RENDERER
# ============================================================

def ui(html):
    st.html(html)


# ============================================================
# DATA
# ============================================================

def read_jsonl(path: Path):

    if not path.exists():
        return []

    records = []

    with path.open(
        encoding="utf-8"
    ) as handle:

        for line_number, line in enumerate(
            handle,
            1
        ):

            if not line.strip():
                continue

            try:
                records.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:

                records.append({
                    "_error":
                        f"Invalid JSON at line {line_number}"
                })

    return records


def group_clean_steps(records):

    traces = defaultdict(list)

    for record in records:

        if "trace_id" in record:

            traces[
                record["trace_id"]
            ].append(record)

    return {
        trace_id:
            sorted(
                steps,
                key=lambda item:
                    item.get(
                        "step_id",
                        0
                    )
            )

        for trace_id, steps
        in traces.items()
    }


def text_value(value):

    if isinstance(
        value,
        list
    ):

        return " ".join(
            text_value(item)
            for item in value
        )

    if isinstance(
        value,
        dict
    ):

        return json.dumps(
            value,
            sort_keys=True
        )

    return str(
        value or ""
    )


def evaluate_faults(records):

    by_type = defaultdict(
        lambda: {
            "total": 0,
            "exact": 0,
            "flagged": 0
        }
    )

    exact = 0
    detected = 0
    total = 0

    for record in records:

        if (
            "steps" not in record
            or "ground_truth"
            not in record
        ):
            continue

        total += 1

        truth = record[
            "ground_truth"
        ]

        metrics = by_type[
            truth["injection_type"]
        ]

        metrics["total"] += 1

        flags = run_tier1(
            record["steps"]
        )

        ids = {
            flag["step_id"]
            for flag in flags
        }

        if ids:

            detected += 1

            metrics[
                "flagged"
            ] += 1

        if (
            truth["target_step_id"]
            in ids
        ):

            exact += 1

            metrics[
                "exact"
            ] += 1

    return {
        "total": total,
        "exact": exact,
        "detected": detected,
        "by_type": dict(by_type),
    }


def flag_map(steps):

    return _group_flags(
        run_tier1(steps)
    )


def _group_flags(flags):

    grouped = defaultdict(list)

    for flag in flags:

        grouped[
            flag["step_id"]
        ].append(flag)

    return grouped


# ============================================================
# LOAD DATA
# ============================================================

clean_records = read_jsonl(
    CLEAN_PATH
)

faulty_records = read_jsonl(
    FAULTY_PATH
)

clean_traces = group_clean_steps(
    clean_records
)

fault_metrics = evaluate_faults(
    faulty_records
)


# ============================================================
# TOP NAV
# ============================================================

ui(
    """
    <div class="tw-nav">

        <div class="tw-logo">

            <div class="tw-logo-mark">
                ◈
            </div>

            TRACEWATCH

        </div>

        <div class="tw-nav-center">

            <span>
                Overview
            </span>

            <span>
                Traces
            </span>

            <span>
                Benchmarks
            </span>

            <span>
                Reliability
            </span>

        </div>

        <div class="tw-nav-right">

            <span>
                Tier 1
            </span>

            <div class="tw-nav-button">
                EXPLORE
            </div>

        </div>

    </div>
    """
)


# ============================================================
# SIMPLE PAGE NAV
# ============================================================

view = st.radio(
    "Workspace",
    [
        "Overview",
        "Trace explorer",
        "Fault benchmark",
    ],
    horizontal=True,
    label_visibility="collapsed",
)


# ============================================================
# OVERVIEW
# ============================================================

if view == "Overview":

    tool_calls = sum(
        1
        for step in clean_records
        if step.get(
            "action_type"
        ) == "tool_call"
    )

    errors = sum(
        1
        for step in clean_records
        if (
            step.get(
                "tool_result"
            )
            or {}
        ).get("error")
    )

    flagged = sum(
        1
        for steps
        in clean_traces.values()
        if run_tier1(steps)
    )

    # --------------------------------------------------------
    # HERO
    # --------------------------------------------------------

    ui(
        f"""
        <div class="tw-background">

            <section class="tw-hero">

                <div class="tw-eyebrow">

                    <span class="tw-eyebrow-dot">
                    </span>

                    AGENT RELIABILITY / LOCAL DATA

                </div>

                <div class="tw-hero-title">

                    Understand

                    <span class="accent">
                        every trace
                    </span>

                    <br>

                    without the noise.

                </div>

                <div class="tw-hero-copy">

                    Inspect execution traces,
                    identify structural failures,
                    and understand where an agent's
                    behaviour breaks down.

                </div>

                </div>


                <div class="tw-floating-grid">

                    <div class="
                        tw-float-card
                        large
                    ">

                        <div class="tw-icon">
                            ◈
                        </div>

                        <div class="tw-float-title">
                            Runtime traces
                        </div>

                        <div class="
                            tw-float-description
                        ">
                            {len(clean_traces)}
                            recorded execution
                            traces available for inspection.
                        </div>

                    </div>


                    <div class="
                        tw-float-card
                    ">

                        <div class="tw-icon">
                            ↗
                        </div>

                        <div class="tw-float-title">
                            Live analytics
                        </div>

                        <div class="
                            tw-float-description
                        ">
                            Real-time structural
                            execution checks.
                        </div>

                    </div>


                    <div class="
                        tw-float-card
                    ">

                        <div class="tw-icon">
                            ✓
                        </div>

                        <div class="tw-float-title">
                            Deterministic
                        </div>

                        <div class="
                            tw-float-description
                        ">
                            Tier 1 checks over
                            observed behaviour.
                        </div>

                    </div>

                </div>

            </section>

        </div>
        """
    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    st.markdown(
        '<div class="tw-section">',
        unsafe_allow_html=True
    )

    ui(
        """
        <div class="tw-section-header">

            <div>

                <div class="tw-section-label">
                    AT A GLANCE
                </div>

                <div class="tw-section-title">
                    What's happening.
                </div>

            </div>

            <div class="tw-section-description">
                A compact view of the execution
                dataset and the current detector
                output.
            </div>

        </div>
        """
    )

    ui(
        f"""
        <div class="tw-metrics">

            <div class="tw-metric">

                <div class="tw-metric-label">
                    CAPTURED TRACES
                </div>

                <div class="tw-metric-value">
                    {len(clean_traces)}
                </div>

                <div class="tw-metric-note">
                    total recorded runs
                </div>

            </div>


            <div class="tw-metric">

                <div class="tw-metric-label">
                    TOOL CALLS
                </div>

                <div class="tw-metric-value">
                    {tool_calls}
                </div>

                <div class="tw-metric-note">
                    across all runs
                </div>

            </div>


            <div class="tw-metric">

                <div class="tw-metric-label">
                    TOOL ERRORS
                </div>

                <div class="tw-metric-value">
                    {errors}
                </div>

                <div class="tw-metric-note">
                    explicit error fields
                </div>

            </div>


            <div class="tw-metric">

                <div class="tw-metric-label">
                    FLAGGED
                </div>

                <div class="tw-metric-value">
                    {flagged}
                </div>

                <div class="tw-metric-note">
                    traces requiring review
                </div>

            </div>

        </div>
        """
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # LOWER PANELS
    # --------------------------------------------------------

    st.markdown(
        '<div class="tw-section">',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(
        2,
        gap="large"
    )


    # --------------------------------------------------------
    # BEHAVIOUR
    # --------------------------------------------------------

    action_counts = Counter(
        step.get(
            "action_type",
            "unknown"
        )
        for step in clean_records
    )

    with col1:

        ui(
            """
            <div class="tw-panel">

                <div class="tw-panel-title">
                    Captured behaviour
                </div>
            """
        )

        max_count = max(
            action_counts.values(),
            default=1
        )

        for action, count in (
            action_counts.items()
        ):

            percentage = (
                count / max_count
            ) * 100

            ui(
                f"""
                <div class="tw-bar-row">

                    <div class="tw-bar-header">

                        <span class="tw-bar-label">
                            {action}
                        </span>

                        <span class="tw-bar-number">
                            {count}
                        </span>

                    </div>

                    <div class="tw-bar">

                        <div
                            class="tw-bar-fill"
                            style="
                                width:{percentage}%;
                            "
                        ></div>

                    </div>

                </div>
                """
            )

        ui(
            """
            </div>
            """
        )


    # --------------------------------------------------------
    # DETECTOR
    # --------------------------------------------------------

    with col2:

        ui(
            """
            <div class="tw-panel">

                <div class="tw-panel-title">
                    Detector performance
                </div>
            """
        )

        if fault_metrics["total"]:

            recall = (
                100
                * fault_metrics["exact"]
                / fault_metrics["total"]
            )

            detection = (
                100
                * fault_metrics["detected"]
                / fault_metrics["total"]
            )

            ui(
                f"""
                <div class="tw-metrics">

                    <div class="tw-metric">

                        <div class="tw-metric-label tw-metric-label-strong">
                            EXACT LOCALIZATION
                        </div>

                        <div class="tw-metric-value">
                            {recall:.1f}%
                        </div>

                        <div class="tw-metric-note">
                            correct target step
                        </div>

                    </div>

                    <div class="tw-metric">

                        <div class="tw-metric-label tw-metric-label-strong">
                            ANY DETECTION
                        </div>

                        <div class="tw-metric-value">
                            {detection:.1f}%
                        </div>

                        <div class="tw-metric-note">
                            at least one flag
                        </div>

                    </div>

                </div>
                """
            )

        else:

            st.info(
                "No fault dataset loaded."
            )

        ui(
            """
            </div>
            """
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# TRACE EXPLORER
# ============================================================

elif view == "Trace explorer":

    ui(
        """
        <div class="tw-hero"
             style="
                min-height:360px;
                margin-bottom:55px;
             ">

            <div class="tw-eyebrow">

                <span class="tw-eyebrow-dot">
                </span>

                TRACE EXPLORER

            </div>

            <div class="tw-hero-title"
                 style="font-size:clamp(3rem,6vw,5.2rem);">

                Follow the

                <span class="accent">
                    execution.
                </span>

            </div>

            <div class="tw-hero-copy">

                Inspect every model message,
                tool call, result, latency,
                and detected issue.

            </div>

        </div>
        """
    )

    query = st.text_input(
        "Filter trace IDs",
        placeholder="Search by UUID prefix..."
    )

    trace_ids = [
        trace_id
        for trace_id in clean_traces
        if query.lower()
        in trace_id.lower()
    ]

    if not trace_ids:

        ui(
            """
            <div class="tw-panel"
                 style="
                    text-align:center;
                    padding:50px;
                 ">

                <div class="tw-section-title">
                    No traces found.
                </div>

                <div style="
                    color:#8b857e;
                    font-size:11px;
                    margin-top:8px;
                ">
                    Try a different trace ID.
                </div>

            </div>
            """
        )

    else:

        selected = st.selectbox(
            "Trace",
            trace_ids,
            format_func=lambda value:
                value[:8]
                + "... / "
                + str(
                    len(
                        clean_traces[value]
                    )
                )
                + " steps"
        )

        steps = clean_traces[
            selected
        ]

        flags_by_step = flag_map(
            steps
        )

        is_flagged = bool(
            flags_by_step
        )

        status_class = (
            "issue"
            if is_flagged
            else "clean"
        )

        status_text = (
            "NEEDS REVIEW"
            if is_flagged
            else "CLEAN"
        )

        ui(
            f"""
            <div class="tw-trace-header">

                <div>

                    <div class="tw-trace-label">
                        TRACE ID
                    </div>

                    <div class="tw-trace-id">
                        {selected}
                    </div>

                </div>

                <div class="
                    tw-status
                    {status_class}
                ">
                    ● {status_text}
                </div>

            </div>

            <div class="tw-section-label">
                EXECUTION TIMELINE
            </div>

            <div class="tw-section-title"
                 style="margin-bottom:30px;">
                What happened.
            </div>
            """
        )

        for step in steps:

            step_flags = flags_by_step.get(
                step.get("step_id"),
                []
            )

            action = step.get(
                "action_type",
                "unknown"
            )

            tool_name = (
                step.get("tool_call")
                or {}
            ).get("name")

            title = (
                tool_name
                or action.replace(
                    "_",
                    " "
                )
            )

            meta = [
                f"step {step.get('step_id')}"
            ]

            if step.get(
                "latency_ms"
            ) is not None:

                meta.append(
                    f"{step['latency_ms']:.0f} ms"
                )

            body = text_value(
                step.get(
                    "raw_output"
                )
            )

            if step.get(
                "tool_result"
            ):

                result = step[
                    "tool_result"
                ]

                body = text_value(
                    result.get(
                        "output"
                    )
                    or result.get(
                        "error"
                    )
                )

            tool_call = (
                step.get(
                    "tool_call"
                )
                or {}
            )

            if tool_call.get(
                "args"
            ):

                body = (
                    "args: "
                    + json.dumps(
                        tool_call["args"]
                    )
                    + "\n\n"
                    + body
                )

            ui(
                f"""
                <div class="tw-step">

                    <div>

                        <div class="tw-step-dot">
                        </div>

                        <div class="tw-step-line">
                        </div>

                    </div>

                    <div class="tw-step-content">

                        <div class="tw-step-heading">

                            <span class="
                                tw-step-number
                            ">
                                {step.get("step_id"):02d}
                            </span>

                            <span class="
                                tw-step-title
                            ">
                                {title}
                            </span>

                        </div>

                        <div class="
                            tw-step-meta
                        ">
                            {" · ".join(meta)}
                        </div>

                        <div class="
                            tw-step-body
                        ">{body}</div>

                    </div>

                </div>
                """
            )

            for flag in step_flags:

                ui(
                    f"""
                    <div class="tw-issue">

                        <div class="
                            tw-issue-title
                        ">
                            {flag["check"]}
                        </div>

                        <div class="
                            tw-issue-detail
                        ">
                            {flag["detail"]}
                        </div>

                    </div>
                    """
                )


# ============================================================
# FAULT BENCHMARK
# ============================================================

else:

    ui(
        """
        <div class="tw-hero"
             style="
                min-height:360px;
                margin-bottom:55px;
             ">

            <div class="tw-eyebrow">

                <span class="tw-eyebrow-dot">
                </span>

                FAULT BENCHMARK

            </div>

            <div class="tw-hero-title"
                 style="font-size:clamp(3rem,6vw,5.2rem);">

                Where the checks

                <span class="accent">
                    hold up.
                </span>

            </div>

            <div class="tw-hero-copy">

                Known faults, exact localization,
                and the cases that need a smarter tier.

            </div>

        </div>
        """
    )

    if not fault_metrics["total"]:

        ui(
            """
            <div class="tw-panel"
                 style="
                    text-align:center;
                    padding:50px;
                 ">

                <div class="tw-section-title">
                    No benchmark data.
                </div>

                <div style="
                    color:#8b857e;
                    font-size:11px;
                    margin-top:8px;
                ">
                    Run the fault injector to create
                    a benchmark dataset.
                </div>

            </div>
            """
        )

    else:

        recall = (
            100
            * fault_metrics["exact"]
            / fault_metrics["total"]
        )

        detection = (
            100
            * fault_metrics["detected"]
            / fault_metrics["total"]
        )

        # ----------------------------------------------------
        # BENCHMARK METRICS
        # ----------------------------------------------------

        ui(
            f"""
            <div class="tw-metrics">

                <div class="tw-metric">

                    <div class="tw-metric-label">
                        INJECTED TRACES
                    </div>

                    <div class="tw-metric-value">
                        {fault_metrics["total"]}
                    </div>

                    <div class="tw-metric-note">
                        benchmark cases
                    </div>

                </div>


                <div class="tw-metric">

                    <div class="tw-metric-label tw-metric-label-strong">
                        EXACT LOCALIZATION
                    </div>

                    <div class="tw-metric-value">
                        {recall:.1f}%
                    </div>

                    <div class="tw-metric-note">
                        correct target step
                    </div>

                </div>


                <div class="tw-metric">

                    <div class="tw-metric-label tw-metric-label-strong">
                        ANY DETECTION
                    </div>

                    <div class="tw-metric-value">
                        {detection:.1f}%
                    </div>

                    <div class="tw-metric-note">
                        at least one flag
                    </div>

                </div>


                <div class="tw-metric">

                    <div class="tw-metric-label">
                        CHECK TIER
                    </div>

                    <div class="tw-metric-value"
                         style="font-size:25px;">
                        TIER 1
                    </div>

                    <div class="tw-metric-note">
                        deterministic
                    </div>

                </div>

            </div>
            """
        )


        # ----------------------------------------------------
        # INJECTION TYPES
        # ----------------------------------------------------

        ui(
            """
            <div class="tw-section">

                <div class="tw-section-label">
                    BENCHMARK BREAKDOWN
                </div>

                <div class="tw-section-title"
                     style="margin-bottom:25px;">
                    Detection by injection type.
                </div>

            </div>
            """
        )

        for (
            injection_type,
            metrics
        ) in sorted(
            fault_metrics[
                "by_type"
            ].items()
        ):

            percentage = (
                100
                * metrics["exact"]
                / max(
                    metrics["total"],
                    1
                )
            )

            ui(
                f"""
                <div class="tw-panel"
                     style="
                        margin-bottom:10px;
                        padding:20px;
                     ">

                    <div class="tw-bar-header">

                        <span class="
                            tw-bar-label
                        ">
                            {injection_type}
                        </span>

                        <span style="
                            color:var(--red);
                            font-family:
                                'IBM Plex Mono',
                                monospace;
                            font-size:9px;
                        ">
                            {percentage:.1f}%
                        </span>

                    </div>

                    <div class="tw-bar">

                        <div
                            class="tw-bar-fill"
                            style="
                                width:
                                {percentage}%;
                            "
                        ></div>

                    </div>

                    <div style="
                        color:#aaa29a;
                        font-family:
                            'IBM Plex Mono',
                            monospace;
                        font-size:8px;
                        margin-top:7px;
                    ">

                        {metrics["exact"]}
                        /
                        {metrics["total"]}
                        exact
                        ·
                        {metrics["flagged"]}
                        flagged

                    </div>

                </div>
                """
            )


        # ----------------------------------------------------
        # INTERPRETATION
        # ----------------------------------------------------

        ui(
            """
            <div class="tw-section">

                <div class="tw-panel">

                    <div class="tw-section-label">
                        INTERPRETATION
                    </div>

                    <div class="tw-section-title"
                         style="
                            font-size:24px;
                            margin-bottom:8px;
                         ">
                        What the benchmark tells us.
                    </div>

                    <div style="
                        color:#77716b;
                        font-size:11px;
                        line-height:1.65;
                        max-width:650px;
                    ">

                        Deterministic checks are strongest
                        when the trace violates a structural
                        contract. Ambiguous output corruption
                        may need a semantic or model-assisted
                        tier.

                    </div>

                </div>

            </div>
            """
        )
