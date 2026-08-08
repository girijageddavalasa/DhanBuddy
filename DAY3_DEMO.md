# Day 3 frontend demo

## Before recording

1. Start the backend and frontend.
2. Open `http://localhost:3000` and allow microphone access.
3. Confirm the page begins in the **Ready** state.

## Short camera script

"Hello, this is DhanBuddy for the Financial Services track. Today I personalised the complete voice interface using yellow, purple, and magenta. The screen clearly shows when DhanBuddy is ready, connecting, listening, speaking, or when the call has ended."

Select **Start talking**, then say:

1. "I want to save for my college fees."
2. "My target is five lakh rupees."
3. "I want to reach it in three years."
4. "I have already saved fifty thousand rupees."
5. "I can save ten thousand rupees every month."
6. "Bye."

Finish with:

"DhanBuddy gives an educational savings estimate without assuming investment returns. Saying bye ends the call, and I can start again from the Call ended screen."

## What to show

- **Ready:** one Start talking button.
- **Connecting:** a wait message and spinner.
- **Listening:** the user speaker indicator and visualiser react.
- **Speaking:** the DhanBuddy indicator and visualiser react.
- **Call ended:** a Start again button appears after saying "bye".
- **Microphone error:** block microphone access once and show the recovery message. Re-enable it from the lock or microphone icon in the browser address bar.

Do not show API keys or `.env.local` files in the recording.
