"""
tasks.py
Task set used for trace collection. Mix of easy, multi-tool, and
deliberately ambiguous/edge-case tasks -- the edge cases are there
on purpose, to surface NATURAL agent failures, not just synthetic
ones from fault_injector.py. Both kinds matter for your dataset.
"""

TASKS = [
    # easy, single tool
    "What is 45 * 12?",
    "What's the weather in Mumbai right now?",
    "Look up order B456 for me.",

    # multi-tool, should require chaining
    "Check the status of order A123 and tell me the weather in Delhi.",
    "If an order costs 45 and there's a 12% tax, what's the total? Also check order A123's status.",

    # ambiguous / edge-case, likely to induce natural failures
    "Look up order C999.",                            # doesn't exist
    "What's the weather in Atlantis?",                 # invalid city
    "Calculate the weather in Delhi divided by 2.",    # nonsensical, tests grounding
    "Check my order status.",                          # no order ID given, tests clarification behavior
    "What's 10 / 0?",                                  # tests error handling
]