# Day 6 — consented outbound savings check-ins

## What was built

DhanBuddy can now place a requested outbound phone call through a stored LiveKit
SIP trunk backed by a provider such as Twilio. The use case is a savings-goal
check-in that the caller explicitly opted into.

The call launcher creates a private LiveKit room, dispatches the named DhanBuddy
worker, and then creates the SIP participant. The agent waits for that exact
participant before starting. Its opening says who is calling, why it is calling,
and how to opt out before discussing any saved goal.

## Safety and privacy

- `--confirmed-opt-in` is mandatory.
- Only a number controlled by the tester should be used.
- The destination phone number is never placed in agent metadata or committed.
- Goal details are not spoken until the recipient confirms their preferred name.
- Saying "stop calling" records an opt-out by anonymous caller ID and ends the call.
- OTPs, PINs, account numbers, Aadhaar numbers, card details, and financial-product
  recommendations remain outside DhanBuddy's scope.

The opt-out file is local at `backend/data/outbound_preferences.json` and is
ignored by Git.

## Call outcomes

The launcher waits for the carrier answer and prints an `OUTBOUND RESULT` plus a
safe retry rule. Busy, no-answer, rejection, and trunk failures do not cause an
uncontrolled retry. Voicemail detection is not enabled, so the demo should not
claim that voicemail has been distinguished automatically.

## Data source

This Day 6 capability does not use live market data. It uses the user's
consented goal context and DhanBuddy's deterministic, zero-return savings tools.
Telephony status comes from the configured SIP provider through LiveKit.
