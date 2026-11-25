# Apple automation path

## Recommended
Use App Intents/App Shortcuts for actions that participating apps expose. Jarvis can trigger deterministic workflows through Shortcuts while Vision provides visual context.

## Screen visibility
Use ScreenCaptureKit and Apple's system content-sharing picker. This requires explicit user permission and is the supported route for iPadOS screen streaming.

## Accessibility
Voice Control and Switch Control can navigate iPadOS, but Apple does not expose them as a general-purpose third-party remote-control API. They can remain user-driven fallbacks.

## Not production automation
XCUIAutomation can manipulate UI for Xcode UI testing. It is a testing framework, not the architecture for an always-on assistant controlling arbitrary App Store apps.

## Practical capability
The planned capability is to provide selected shared content while an explicitly
authorized share is active and execute participating apps' supported
Shortcuts/App Intents. The current repository contains a scaffold: the capture
picker callback, app target, and action integration are not connected. It does
not currently provide continuous screen visibility or execute device actions.
For unsupported app UI, the intended fallback is tap/type guidance.
