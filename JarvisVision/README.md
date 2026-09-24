# Jarvis Vision

iPad-first visual relay for Jarvis.

## Architecture
1. iPadOS ScreenCaptureKit captures user-selected screen/app/window content.
2. Jarvis Vision samples frames locally and sends encrypted JPEG frames to a relay endpoint.
3. Relay exposes an authenticated latest-frame/session API for an AI vision consumer.
4. Actions are routed through Apple-supported App Intents / Shortcuts when an app exposes them. Arbitrary cross-app tapping is deliberately not attempted.

## Apple automation strategy
- **Vision:** ScreenCaptureKit + SCContentSharingPicker (preferred over legacy ReplayKit).
- **Actions:** App Intents / App Shortcuts and URL schemes where supported.
- **Human-in-loop navigation:** Jarvis returns tap/type instructions for apps that do not expose automatable actions.
- **Testing only:** XCUIAutomation is not used as a production remote-control mechanism.

## Security
No silent capture. iPadOS screen-sharing permission is required. Relay must use TLS and bearer authentication. Do not persist frames by default.

## Status
MVP scaffold: capture coordinator, frame relay client, session model, and server relay API.
