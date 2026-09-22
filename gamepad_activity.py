#!/usr/bin/python
"""Report actual controller use without grabbing or changing game input.

Uses Linux's read-only joystick interface. No keyboard/mouse access, injected
events, packages, root service, or application-specific rules are needed.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import selectors
import struct
import sys
import time

EVENT = struct.Struct('IhBB')
BUTTON, AXIS, INIT = 1, 2, 128
STICKS = {0, 1, 3, 4}  # ABS_X/Y/RX/RY
TRIGGERS = {2, 5, 6, 9, 10}  # Z/RZ/THROTTLE/GAS/BRAKE
HATS = set(range(16, 24))


class State:
    def __init__(self, axis_map):
        self.axis_map = axis_map
        self.axes = {}
        self.buttons = {}
        self.armed = False

    def feed(self, value, kind, number):
        initial = bool(kind & INIT)
        kind &= ~INIT
        if kind == BUTTON:
            self.buttons[number] = value != 0
            meaningful = value != 0
        elif kind == AXIS and number < len(self.axis_map):
            code = self.axis_map[number]
            self.axes[code] = value
            # Ignore center jitter; hats are discrete. Trigger rest is -32767.
            meaningful = ((code in HATS and value != 0)
                          or (code in STICKS and abs(value) > 5000)
                          or (code in TRIGGERS and value > -27767))
        else:
            return False
        if initial:
            return False
        if meaningful:
            self.armed = True
        return meaningful

    def active(self):
        if not self.armed:
            return False
        if any(self.buttons.values()):
            return True
        return any(
            (code in STICKS and abs(value) > 5000)
            or (code in TRIGGERS and value > -27767)
            or (code in HATS and value != 0)
            for code, value in self.axes.items()
        )


def controller_bits(words):
    """Decode the kernel's native-word bitmap and reject unrelated HID devices."""
    bits = 0
    for word in words:
        bits = (bits << (struct.calcsize('L') * 8)) | int(word, 16)
    return bool(bits & ((1 << 288) | (1 << 304) | (1 << 320)))


def inventory(sysfs=Path('/sys/class/input')):
    for device in sorted(sysfs.glob('js*')):
        try:
            words = (device / 'device/capabilities/key').read_text().split()
            path = '/dev/input/' + device.name
            yield {
                'path': path,
                'name': (device / 'device/name').read_text().strip(),
                'controller': controller_bits(words),
                'readable': os.access(path, os.R_OK),
            }
        except (OSError, ValueError):
            continue


def gamepads():
    return (device['path'] for device in inventory() if device['controller'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='Show joystick device diagnostics and exit')
    if parser.parse_args().list:
        print(json.dumps(list(inventory()), indent=2))
        return
    selector = selectors.DefaultSelector()
    devices = {}
    failures = {}
    next_scan = 0.0
    last_report = -10.0

    def remove(path):
        fd, _ = devices.pop(path)
        selector.unregister(fd)
        os.close(fd)
        print('Disconnected: ' + path, file=sys.stderr, flush=True)

    while True:
        now = time.monotonic()
        if now >= next_scan:
            present = set(gamepads())
            failures = {p: e for p, e in failures.items() if p in present}
            for path in set(devices) - present:
                remove(path)
            for path in present - set(devices):
                fd = None
                try:
                    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
                    axis_map = bytearray(64)
                    fcntl.ioctl(fd, 0x80406A32, axis_map, True)  # JSIOCGAXMAP
                    state = State(axis_map)
                    devices[path] = (fd, state)
                    selector.register(fd, selectors.EVENT_READ, path)
                    failures.pop(path, None)
                    print('Watching: ' + path, file=sys.stderr, flush=True)
                except OSError as error:
                    if fd is not None:
                        os.close(fd)
                    if failures.get(path) != str(error):
                        print(f'Cannot watch {path}: {error}', file=sys.stderr, flush=True)
                        failures[path] = str(error)
            next_scan = now + 3

        meaningful = False
        for key, _ in selector.select(0.25):
            path = key.data
            fd, state = devices[path]
            try:
                data = os.read(fd, EVENT.size * 256)
                if not data:
                    remove(path)
                    continue
                for _, value, kind, number in EVENT.iter_unpack(data):
                    meaningful = state.feed(value, kind, number) or meaningful
            except BlockingIOError:
                pass
            except OSError:
                remove(path)

        now = time.monotonic()
        if (meaningful or any(s.active() for _, s in devices.values())) and now - last_report >= 1:
            print('activity', flush=True)
            last_report = now


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass
