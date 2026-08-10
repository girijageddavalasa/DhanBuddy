# Day 5 demo — Chained domain tools

## Preparation

Complete the Day 4 memory flow first. Save a goal with these easy demo values:

- Goal: college fees
- Target: ₹5,00,000
- Deadline: 3 years
- Already saved: ₹50,000
- Monthly saving: ₹10,000

## Successful tool-chain demonstration

Ask:

> DhanBuddy, use the college-fees goal you remember and show me ways to close my
> savings gap.

Expected calculation:

- Current projection: ₹4,10,000 after 36 months
- Required monthly saving: ₹12,500
- Monthly increase needed: ₹2,500
- Alternative deadline: 45 months total, or 9 extra months

Show that the three results also appear in the frontend while DhanBuddy explains
them naturally.

Say to the camera:

> DhanBuddy automatically chained two LiveKit function tools. The first retrieved
> my consented goal from SQLite. The second computed zero-return savings scenarios,
> added a calculation timestamp, spoke the result naturally, and pushed it to the
> interface.

## Failure demonstration

Use a private browser session with no saved profile and ask the same question.
DhanBuddy should say that no saved goal is available and ask for the missing goal
information. It must not invent amounts or remain silent.

Say to the camera:

> The source is local deterministic calculation, not live market data. When memory
> is unavailable, DhanBuddy explains the failure instead of guessing.
