# Day 4 — Persistent, Consent-Based Memory

## Goal

Day 4 gives DhanBuddy memory that survives agent restarts. The implementation is
designed for Financial Services, where permission and data minimisation are hard
requirements.

## What was built

### Persistent SQLite database

Caller memory is stored in `backend/data/dhanbuddy.db`. The database file is
created automatically and is ignored by Git so real caller data is never pushed.

The saved profile contains:

- anonymous caller ID,
- preferred name,
- language preference,
- savings goal,
- target amount,
- target deadline,
- amount already saved,
- monthly saving capacity,
- consent status,
- last interaction timestamp.

DhanBuddy never stores an OTP, PIN, CVV, password, Aadhaar number, account number,
or card details.

### Anonymous returning-caller ID

The Next.js token endpoint creates a random caller ID and saves it in a secure,
HTTP-only browser cookie. LiveKit uses that ID as the participant identity. This
allows the same browser to be recognised later without using a phone number or
financial identifier.

### Agent memory tools

The LLM reads and writes memory through functions:

- `lookup_caller()` finds the current caller.
- `save_caller_memory(...)` saves approved facts after explicit consent.
- `forget_caller(...)` permanently deletes the profile after confirmation.

Memory is not inserted into the system prompt. At the beginning of every call,
the agent is instructed to call `lookup_caller` before greeting.

### Consent enforcement

The agent must explain which information it wants to remember and ask permission.
The save tool independently checks the exact consent response. It refuses silence,
uncertainty, and unrelated answers.

Example:

> I can remember your name, preferred language, and this savings goal for your
> next call. Should I save them?

If the caller says no, the save tool is not called and the conversation continues
without persistent memory.

### Returning-caller greeting

When a profile exists, DhanBuddy can say:

> Welcome back, Asha. Last time you were saving for college fees. Would you like
> to continue that plan?

### Forget-me flow

When the caller asks to be forgotten, DhanBuddy explains that deletion is
permanent and asks for confirmation. Only a clear confirmation allows the delete
tool to run.

### Native-language scripts

The prompt now requires each non-English language to use its native script:

- Hindi: नमस्ते, not romanised Hindi.
- Telugu: నమస్కారం.
- Tamil: வணக்கம்.
- Kannada: ನಮಸ್ಕಾರ.
- Malayalam: നമസ്കാരം.

The same rule applies to every other supported non-English language unless the
caller explicitly requests transliteration.

## Approved RAG library

The reviewed knowledge collection is in `backend/rag/`. It contains short,
institution-neutral explanations grounded in official sources:

- SEBI Financial Education Booklet,
- SEBI Money Matters,
- RBI Financial Awareness Messages.

The collection covers savings, budgeting, goals, emergency savings, fraud safety,
monthly shortfalls, monthly surpluses, and deadline extensions. It does not provide
product recommendations, scheme eligibility, approvals, or returns.

## Professional UI update

The frontend now uses a restrained financial-service theme:

- neutral white or charcoal background,
- deep purple only for primary actions,
- fewer gradients and decorative colours,
- simpler cards and shadows,
- a visible consent-only memory notice,
- a clear reminder that callers can say “forget me”.

## Testing

- SQLite persistence is tested across separate database connections.
- Missing-caller lookup is tested.
- Permanent deletion is tested.
- English and Hindi explicit consent are tested.
- Uncertain consent is rejected.
- Native-script prompt rules are tested.
- All existing calculator, safety, language, and retrieval tests continue to pass.

## Result

DhanBuddy can now recognise the same browser after a complete agent restart, ask
before remembering anything, continue a previous savings goal, and permanently
forget the caller on request.
