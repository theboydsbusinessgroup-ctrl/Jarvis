# JARVIS Voice Commands

The browser uses `SpeechRecognition` / `webkitSpeechRecognition` when available. A microphone tap begins a single utterance, displays interim transcription, sends the final transcript to `/api/command`, and speaks Jarvis's response.

The server command router is policy-gated. Safe control-plane reads and local UI commands execute immediately. High-impact voice commands involving spending, money movement, destructive actions, credentials, security changes, contracts, or live trading are never executed from an unconfirmed utterance. Commands requiring external authenticated tools are acknowledged as not connected rather than falsely reported as executed.

Current executable examples: `status report`, `show revenue`, `what needs me`, `show projects`, `refresh systems`, `voice off`, `voice on`, `sound off`, `sound on`, and `reboot`.

Cross-service execution should be added through an authenticated executor bridge that invokes the existing autonomy policy and Access Broker before any external side effect.
