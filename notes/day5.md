# Day 5 — Chained Savings Scenario Tools

## Goal

Day 5 gives DhanBuddy a real domain computation that the language model cannot
perform or invent on its own. It reuses the caller's consented Day 4 memory and
compares practical zero-return paths toward the saved goal.

## Tool files

The reusable calculation logic is stored separately from the agent:

```text
backend/src/tools/
├── __init__.py
└── savings_scenarios.py
```

The LiveKit function-tool wrappers are registered in `backend/src/agent.py`.

## Tool chain

### `lookup_previous_goal`

This tool retrieves the current caller's saved goal from SQLite. It returns the
target amount, months, amount already saved, monthly saving capacity, and the time
the profile was last saved. The tool description tells Gemini to call it first
whenever the caller asks to reuse or compare a remembered goal.

### `compare_goal_scenarios`

This tool receives the exact values returned by the memory lookup and computes:

- the projected amount on the current path,
- whether the current path is on track,
- the monthly amount required by the original deadline,
- the monthly increase needed,
- the total months needed at the current saving rate,
- the number of extra months required.

All calculations assume zero investment returns. No mutual fund, stock, bank,
insurance, loan, or cryptocurrency is recommended.

## Data source and freshness

This is a **local deterministic calculation**, not a live market-data API. Its
inputs come from the caller's consented SQLite memory. Every result includes an
ISO timestamp showing exactly when it was calculated and identifies its source as:

> Local deterministic calculation with zero investment returns

## Frontend result card

The calculation is sent over a reliable LiveKit data packet using the topic
`dhanbuddy.tool_result`. The frontend listens for that topic and displays three
short cards while DhanBuddy speaks:

1. Current path
2. Monthly path
3. More-time path

The card also shows the calculation time and the zero-return assumption.

## Failure handling

- If no saved goal exists, DhanBuddy says it cannot find one and asks for the
  missing goal information.
- If the saved profile is incomplete, it names only the missing non-sensitive
  field.
- If values are invalid, the calculation tool refuses to guess.
- If UI data delivery fails, the spoken calculation still continues and the tool
  reports that only the visual card was unavailable.

## Demo question

> DhanBuddy, use the college-fees goal you remember and show me ways to close my
> savings gap.

Gemini should automatically call `lookup_previous_goal`, followed by
`compare_goal_scenarios`, speak the result naturally, and show the visual cards.
