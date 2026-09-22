# Changelog

## 0.1.0

Initial preview release for Omarchy 4.0.4 / Quickshell 0.3.1.

- Observe controller buttons, sticks, triggers and D-pads without grabbing input.
- Treat held controls as activity; ignore centered stick drift and sensor axes.
- Preserve the configured screensaver and lock timeouts after activity stops.
- Discover reconnecting controllers, including Steam Input virtual gamepads.
- Keep the existing Stay Awake switch and idle IPC interface.
- Include input-filter tests, isolated idle-timer tests, diagnostics and removal instructions.

Automated timing/filter tests pass. Live controller gameplay and the full
150/300-second idle cycle still need validation before declaring this stable.
