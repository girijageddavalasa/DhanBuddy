# Day 4 demo — DhanBuddy memory

## First call

1. Start the backend and frontend.
2. Open DhanBuddy in the same browser you will use for both calls.
3. Say: “My name is Asha. I prefer Hindi.”
4. Say: “मैं कॉलेज फीस के लिए पाँच लाख रुपये बचाना चाहती हूँ।”
5. Complete the target, deadline, current savings, and monthly savings questions.
6. When DhanBuddy asks to remember the profile, say: “हाँ।”
7. Say: “Bye.”

## Restart test

Fully stop and restart the backend:

```powershell
cd C:\DLGM\DhanBuddy\backend
uv run python src\agent.py dev
```

Keep the same browser profile. Start a second call. DhanBuddy should call its
lookup tool, greet Asha by name, and mention the saved college-fees goal.

## Consent refusal test

Use a private browser window or clear only the DhanBuddy caller cookie. Begin a
new call and say “No” when asked to save. Restart and call again. DhanBuddy must
not remember that profile.

## Forget-me test

1. Say: “Forget everything you remember about me.”
2. DhanBuddy must explain that deletion is permanent and ask for confirmation.
3. Say: “Yes.”
4. End the call and call again.
5. DhanBuddy should treat the browser as a caller with no saved profile.

Never show `.env.local`, API keys, or the contents of the SQLite database in the
recording.
