#!/usr/bin/env python3
"""Exercise the shipped QML timers with an isolated, non-locking test instance."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError('Test seam changed; inspect the service before running: ' + old)
    return text.replace(old, new, 1)


def make_test():
    source = (ROOT / 'Service.qml').read_text()
    source = replace_once(source, '  property var shell: null', '''  property var shell: ({shellConfig: {idle: {screensaver: 2, lock: 4}}})
  property var testActions: []
  property int testFailures: 0
  function check(value, message) {
    if (!value) { root.testFailures++; console.log("FAIL: " + message) }
  }''')
    source = replace_once(source, '  function runProcess(process, label, command) {',
                          '  function runProcess(process, label, command) {\n    root.testActions.push(label); return true;')
    source = replace_once(source, 'command: ["pkill", "-f", "[o]rg.omarchy.screensaver"]',
                          'command: ["/usr/bin/true"]')
    source = replace_once(source, 'command: ["/usr/bin/python", "-u", Qt.resolvedUrl("gamepad_activity.py").toString().replace("file://", "")]',
                          'command: ["/usr/bin/true"]')
    source = replace_once(source, '''  IdleMonitor {
    id: idleMonitor
    enabled: root.idleEnabled
    timeout: root.firstIdleTimeoutSeconds
    respectInhibitors: true''', '''  QtObject {
    id: idleMonitor
    property bool isIdle: true''')
    source = replace_once(source, '  function refreshStayAwakeState() {',
                          '  function refreshStayAwakeState() {\n    root.stayAwakeStateLoaded = true; return;')
    source = replace_once(source, 'target: "idle"', 'target: "controllerIdleIsolatedTest"')
    source = replace_once(source, '''    refreshStayAwakeState()
  }

  IpcHandler''', '''    refreshStayAwakeState()
    root.controllerActivity()
    root.handleIdleChanged()
  }

  Timer { interval: 1000; running: true; onTriggered: {
    root.check(root.testActions.length === 0, "Idled during controller activity")
    root.controllerActivity()
  } }
  Timer { interval: 2300; running: true; onTriggered: {
    root.check(root.testActions.length === 0, "New input failed to reset countdown")
  } }
  Timer { interval: 3400; running: true; onTriggered: {
    root.check(root.testActions.join(",") === "screensaver", "Inactivity did not start screensaver")
  } }
  Timer { interval: 3600; running: true; onTriggered: {
    root.controllerActivity()
    root.check(!root.idledThisCycle, "Returning controller input failed to cancel idle")
    root.check(!lockTimer.running, "Pending lock survived controller activity")
  } }
  Timer { interval: 6200; running: true; onTriggered: {
    root.check(root.testActions.join(",") === "screensaver,wake,screensaver", "Timeout did not restart after returning input")
  } }
  Timer { interval: 8200; running: true; onTriggered: {
    root.check(root.testActions.join(",") === "screensaver,wake,screensaver,lock", "Normal lock deadline not restored")
    if (root.testFailures === 0) console.log("PASS: controller resets, resume, screensaver and lock deadlines")
    Qt.quit()
  } }

  IpcHandler''')
    return source


def main():
    with tempfile.TemporaryDirectory(prefix='controller-idle-test-') as temp:
        directory = Path(temp)
        (directory / 'shell.qml').write_text(make_test())
        shutil.copy2(ROOT / 'IdleModel.js', directory)
        result = subprocess.run(['quickshell', '--no-color', '-p', str(directory)],
                                capture_output=True, text=True, timeout=15)
        output = result.stdout + result.stderr
        print(output)
        if result.returncode or 'PASS: controller resets' not in output or 'FAIL:' in output:
            raise SystemExit('Idle timing regression test failed')


if __name__ == '__main__':
    main()
