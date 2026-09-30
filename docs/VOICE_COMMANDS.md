# Jarvis voice and natural conversation

Say “Siri, Jarvis” using the existing Open URLs shortcut. The dashboard starts automatically and attempts audio and microphone initialization. Safari controls permissions and autoplay: opening a URL from Siri does not guarantee a browser audio gesture. If blocked, tap ENABLE MIC. No Initialize button is required to view the dashboard.

## First use

1. Open https://jarvis-exw6.onrender.com in Safari.
2. Tap SIGN IN and enter the separate Jarvis owner access code. Safari keeps a signed HttpOnly, Secure, SameSite cookie for 30 days. Repeat on the iPhone. The code is not a Hermes provider credential.
3. Tap ENABLE MIC if Safari requires a gesture. Allow microphone/speech recognition if asked.
4. Speak a request. Jarvis sends one final utterance, pauses listening while processing and speaking, and resumes after the reply finishes.
5. Say “go to sleep” or tap the active microphone to stop listening. Siri remains the wake mechanism. Voice pauses while the page is hidden or the device is locked.

Natural conversation uses the existing bounded Hermes pilot with recent dialogue and verified control-plane state. Only a fixed set of local UI operations is executable from the model's interpreted intent. Other requested actions return explanations or proposals. Tool suppression in the Hermes worker is a prompt instruction, not a verified server-side tool sandbox; this release does not enable business writes or device control. Unknown external capabilities must be reported as absent rather than simulated. Conversation history is limited to the current page, not durable personal memory.

## Optional Siri dictation handoff

For a command without first activating Safari's microphone, edit the Jarvis shortcut:

1. Add Dictate Text before Open URLs.
2. Add URL Encode for the Dictated Text variable.
3. Set Open URLs to `https://jarvis-exw6.onrender.com/#command=` followed by the URL Encoded Text variable.
4. Say “Siri, Jarvis”, dictate when prompted, and finish dictation.

The dashboard reads the command from the fragment, immediately removes it from the address, and submits it through the same owner-authenticated conversation route. Sign in in Safari first. The fragment is not sent to the web server in the initial URL request. Browser spoken output may still require an audio gesture; Siri dictation does not bypass that restriction.

## Runtime configuration

- JARVIS_OWNER_KEY: independent random owner access code. Rotate to invalidate existing sessions.
- On Render: JARVIS_CONVERSATION_PROXY_URL=https://jarvis-lyart-sigma.vercel.app.
- On Vercel: the same JARVIS_OWNER_KEY, alongside the existing HERMES_ENABLED, HERMES_API_URL, HERMES_API_KEY and HERMES_MODEL.
- The owner key authenticates the server-to-server proxy, while the protected Hermes credential stays on Vercel.
- Without a proxy, the conversation route calls the configured local Hermes bridge.

Requests have bounded input/history size, a process-local rate limiter, two concurrent conversation slots, and a bounded worker timeout. The limiter is not a distributed anti-abuse service. Model output can never supply a browser URL, shell command, tool name, or action payload. Service-to-service requests use bearer auth; browser requests use the signed cookie and an origin check.

## Scope

This release adds automatic dashboard startup, browser speech conversation, Siri dictation handoff, and owner authentication. Full iOS read/write actions, background microphone operation, persistent conversations, external connector execution, and native App Intents are not connected by this release. These require separate integrations and per-capability permissions.
