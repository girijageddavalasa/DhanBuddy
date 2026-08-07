upgraded DhanBuddy into a safer, multilingual, voice-first savings assistant.

## What I will build

1. **Structured agent prompt**

   Organize the instructions into:

   - Identity
   - Objectives
   - Knowledge boundaries
   - Language behaviour
   - Guardrails
   - Speaking style

2. **Three call objectives**

   A successful call will:

   - Understand one savings goal
   - Calculate whether the user is on track
   - Explain the result and one practical next step

3. **Strong financial guardrails**

   DhanBuddy will refuse to:

   - Request or process OTPs, PINs, CVVs, passwords, account numbers, Aadhaar numbers, or card details
   - Recommend specific stocks, mutual funds, banks, insurance products, cryptocurrencies, or schemes
   - Guarantee returns, profits, loan approval, scholarship approval, or scheme eligibility

4. **Escalation path**

   For account problems, eligibility questions, or personalized financial advice, it will direct the user to:

   - The relevant official organization
   - Their bank’s official support channel
   - A qualified financial professional

   It will also remind them not to share sensitive credentials.

5. **English, Hindi, and Hinglish support**

   DhanBuddy will:

   - Detect the user’s language style
   - Mirror English, Hindi, or Hinglish
   - Handle code-mixed sentences
   - Change language when the user changes language

6. **Improved greeting**

   It will begin with:

   > “Namaste! I’m DhanBuddy. I can help you check whether your monthly savings can reach one financial goal. What are you saving for?”

7. **Deterministic savings calculator**

   Exact Python calculations will continue to determine:

   - Projected amount
   - Required monthly savings
   - Monthly shortfall or surplus
   - Whether the goal is on track

   No investment returns will be assumed.

8. **Small local RAG knowledge base**

   I will add approved educational explanations for terms such as:

   - Savings goal
   - Monthly shortfall
   - Monthly surplus
   - Emergency fund
   - Deadline extension
   - Educational estimate

   RAG will explain concepts only. It will not perform calculations or recommend products.

9. **Silence handling**

   - First silence: give a short re-prompt
   - Second silence: close the conversation politely

10. **Voice-first responses**

   Spoken responses will have:

   - Short sentences
   - One question at a time
   - No markdown
   - No bullet points
   - No brackets
   - No emojis
   - No long legal-style disclaimer

11. **Red-team testing**

   Create `RED_TEAM.md` containing at least ten prompts that test:

   - Sensitive-data requests
   - Guaranteed-return claims
   - Product recommendations
   - Prompt injection
   - Repetition
   - Confused users
   - Unrelated questions
   - Hinglish requests
   - Language switching
   - Silence

12. **Automated tests and documentation**

   I will update:

   - Backend tests
   - README
   - Demo conversation
   - Guardrail examples
   - Language examples
   - Silence behaviour

Finally, I’ll run the checks, commit everything, and push it to GitHub.