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

This is not yet a working capture application. The repository has no Xcode project
or configured app target. `Start Vision` activates the picker, but no picker
observer calls `attach(filter:)`, so it does not start a capture stream. Confirm
the intended device's SDK support, create and build the target, and connect the
permission/picker lifecycle before testing frame delivery on a real device.
