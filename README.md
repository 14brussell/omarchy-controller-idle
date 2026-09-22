# Controller-Aware Idle for Omarchy

Keep playing with a controller without the screensaver interrupting you.

Controller activity resets your existing screensaver and lock timers. Put the
controller down and normal idle behavior resumes—even with the game still open.
Small stick drift is ignored.

## Install

```bash
omarchy plugin add https://github.com/14brussell/omarchy-controller-idle.git --enable
omarchy restart shell
```

Restart while unlocked. Disable any other custom idle plugin first: this plugin
replaces Omarchy's built-in idle service.

## Compatibility

Requires Omarchy's Quickshell shell, Python 3, and read access to a Linux joystick
device (`/dev/input/js*`, via `joydev`). No additional Python packages or root
service are needed.

Supports Steam Input virtual gamepads and other Linux joystick devices.
HIDAPI-only controllers and unusual axis mappings may need additional support.

**Preview:** checked on Omarchy 4.0.4 and Quickshell 0.3.1. Automated tests pass;
physical gameplay and full-duration idle verification are still pending.

## Troubleshooting

```bash
omarchy-shell idle status
python "$HOME/.config/omarchy/plugins/io.github.14brussell.controller-idle/gamepad_activity.py" --list
```

`controllerActivityReports` should increase while using the controller and stop
when you release it. `--list` shows detected devices and read permissions.

Your existing `idle.screensaver` and `idle.lock` settings in
`~/.config/omarchy/shell.json` still apply, as do other apps' idle inhibitors.

## Remove

```bash
omarchy plugin disable io.github.14brussell.controller-idle
omarchy plugin enable omarchy.idle
omarchy restart shell
omarchy plugin remove io.github.14brussell.controller-idle
```

## Development

```bash
python -m unittest discover -s tests -v
omarchy plugin validate .
python tests/test_timing.py
```

The timing test uses mocked screensaver and lock actions in a separate Quickshell
instance. Build an archive with `python build_release.py`.

Derived from Omarchy's idle service; review upstream changes when updating.
[MIT license](LICENSE) · [Changelog](CHANGELOG.md)
