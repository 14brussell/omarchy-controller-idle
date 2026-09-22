# Controller-Aware Idle for Omarchy

Keep playing with a controller without the screensaver interrupting you.
Put the controller down and your normal screensaver and lock timers still work,
even if the game remains open.

This headless plugin counts actual button presses, held buttons, stick movement,
triggers and D-pad input as activity. It works independently of the game,
launcher and fullscreen state. Small stick drift and sensor-axis noise are
ignored. No mouse movement or keyboard events are injected.

**Preview release:** tested against Omarchy **4.0.4-1**, Quickshell **0.3.1-1**,
and Python **3.14.7**. Automated filtering and timer tests pass. Physical
controller gameplay and a complete normal-duration idle cycle remain to be
verified. Other Omarchy versions and controller models are not yet validated.

## Requirements

- Omarchy's Quickshell-based shell with the `omarchy.idle` service and service-clone routing (4.0.4 is the tested version).
- Python 3; only its standard library is used.
- A Linux joystick device under `/dev/input/js*`, provided by the kernel's `joydev` interface.
- Your desktop user must already have read access to that controller device.

Steam Input virtual gamepads are supported when they expose a joystick device.
Controllers available only through HIDAPI, or controller mappings that never
produce joystick input, are not monitored. Their normal keyboard/mouse output
can still reset Omarchy's existing idle detector.

## Install from GitHub

```bash
omarchy plugin add https://github.com/14brussell/omarchy-controller-idle.git --enable
omarchy restart shell
```

Restart while the desktop is unlocked. If you already use another replacement
for `omarchy.idle`, disable that plugin first; run only one idle replacement.

## Install from a locally built archive

To build an archive from this repository, run `python build_release.py`.

Run these commands from the directory containing the downloaded archive:

```bash
plugin_dir="$HOME/.config/omarchy/plugins/io.github.14brussell.controller-idle"
# Refuse to overwrite an existing installation.
test ! -e "$plugin_dir" || { echo "Plugin already installed"; exit 1; }
mkdir -p "$HOME/.config/omarchy/plugins"
tar -xzf omarchy-controller-idle-0.1.0.tar.gz -C "$HOME/.config/omarchy/plugins"
omarchy plugin validate "$plugin_dir"
omarchy-shell shell rescanPlugins
omarchy plugin enable io.github.14brussell.controller-idle
omarchy restart shell
```

Restart the shell while the desktop is unlocked. This loads the replacement
idle service cleanly; a rescan alone can retain the old service in memory.

If another custom idle plugin is enabled, disable it first and restart the
shell. Run only one replacement for `omarchy.idle` at a time. This includes the
early personal prototype named `brussell.idle`.

Git installations can later use `omarchy plugin update io.github.14brussell.controller-idle`,
followed by a shell restart.

## Behavior and configuration

The plugin preserves `idle.screensaver` and `idle.lock` in
`~/.config/omarchy/shell.json`. For example:

```json
"idle": { "screensaver": 150, "lock": 300 }
```

These mean 150 and 300 seconds since the most recent keyboard, mouse or
controller activity. Reports are throttled to one per second. Controller
reconnects are discovered within three seconds. Stick dead zones are about 15%
of the normalized axis range; triggers use the same margin above their rest
position. A control held outside its dead zone counts as continued activity.

Returning to the controller cancels a pending idle cycle and dismisses the
screensaver. It **never unlocks an already locked session**. The existing Stay
Awake control continues to work. Existing compositor/application idle inhibitors
also remain respected; this plugin does not remove other keep-awake rules.

## Verify and troubleshoot

```bash
omarchy-shell idle status
python "$HOME/.config/omarchy/plugins/io.github.14brussell.controller-idle/gamepad_activity.py" --list
```

The first command should include `controllerWatcherRunning: true`. While a game
is using Steam Input, press a button or move a stick: `controllerActivityReports`
and `lastControllerActivity` should change. After releasing all controls, the
report count should stop. `controllerQuietCountdownRunning` remains true until
the normal first idle timeout expires; it is not a permanent inhibitor.

To test the actual timeouts, leave **both** the controller and keyboard/mouse
untouched while a game remains open. Check that the screensaver and lock occur
at your configured intervals. A controller using a different desktop mapping
may not send joystick events until the game is focused.

`--list` prints detected joystick devices, controller classification and whether
your user can read each one. If your controller is absent, check its connection
and `joydev` support. If it is unreadable, resolve its normal desktop device
permissions. This plugin does not install udev rules, require root, change group
membership, or grant broad access to keyboard input.

If reports continue with the controller resting, inspect calibration/stick drift
and test the controller by itself. Some controllers use different trigger-axis
conventions and may require device-specific handling; report the controller
model and `--list` output with the issue.

## Disable or remove

```bash
omarchy plugin disable io.github.14brussell.controller-idle
omarchy plugin enable omarchy.idle
omarchy restart shell
```

To remove the disabled plugin:

```bash
omarchy plugin remove io.github.14brussell.controller-idle
```

No fullscreen rules, global Stay Awake setting, or system files need restoring.

## Implementation and maintenance

`Service.qml` and `IdleModel.js` derive from Omarchy 4.0.4's MIT-licensed idle
service. `gamepad_activity.py` reads controller input without consuming it
exclusively or modifying it. No network requests or input-history files are
created. Only activity counters, timestamps and device diagnostics are exposed.

The manifest deliberately retains `omarchy.clonedFrom: omarchy.idle`: this is a
replacement service, not a second independent idle manager. That metadata lets
Omarchy disable the original and restore it when this plugin is disabled. It
also routes the Stay Awake indicator to the active replacement on supported
shell versions. Older versions have had service-clone routing bugs.

Updates to Omarchy's built-in idle service do not automatically update this
copy. Maintainers should compare it against upstream when supporting a new
Omarchy release. Re-run lifecycle and idle tests before publishing updates.

## Development checks

```bash
python -m unittest discover -s tests -v
omarchy plugin validate .
python tests/test_timing.py
```

The timing test requires a running Wayland/Quickshell session. It uses a separate
short-lived test instance with a mock idle monitor and stubbed commands. It does
not launch a screensaver, lock the session, or alter the installed plugin.

MIT licensed. See [LICENSE](LICENSE) and [CHANGELOG.md](CHANGELOG.md).
