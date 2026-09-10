# JARVIS Audio Protocol

## iOS / iPadOS unlock
Safari requires audio creation/resume and the first speech request to occur within a direct user gesture. `INITIALIZE WITH AUDIO` now calls `AudioContext.resume()` and immediately plays an audible handshake plus queues the first speech utterance before any asynchronous boot delay.

## Voice test
The persistent `TEST` control is a direct user-gesture diagnostic. It forces Voice on, resumes Web Audio, plays two tones, and immediately speaks a confirmation line. If tones work but speech does not, the issue is device/browser speech synthesis. If neither works, check device volume/output route and browser audio permissions.

## Visual state coupling
The central JARVIS core has `thinking`, `speaking`, and `idle` states. Particle velocity, radial voice bars, glow, and pulse rate change with those states. This is intentionally a living voice/thought visualization rather than a card dashboard.
