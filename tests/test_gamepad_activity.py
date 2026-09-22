import struct
import unittest
from gamepad_activity import State, BUTTON, AXIS, INIT, controller_bits


class FilteringTests(unittest.TestCase):
    def setUp(self):
        self.s = State([0, 1, 2, 3, 4, 5, 16, 17, 40])
        for i, v in enumerate([0, 0, -32767, 0, 0, -32767, 0, 0, 12000]):
            self.assertFalse(self.s.feed(v, AXIS | INIT, i))

    def test_rest_and_drift(self):
        for v in [-2000, 2000, 0]:
            self.assertFalse(self.s.feed(v, AXIS, 0))
            self.assertFalse(self.s.active())

    def test_held_button_and_release(self):
        self.assertTrue(self.s.feed(1, BUTTON, 0))
        self.assertTrue(self.s.active())
        self.assertFalse(self.s.feed(0, BUTTON, 0))
        self.assertFalse(self.s.active())

    def test_stick_trigger_and_hat_return_to_rest(self):
        for axis, value, rest in [(0, 8000, 0), (2, 0, -32767), (6, -32767, 0)]:
            self.assertTrue(self.s.feed(value, AXIS, axis))
            self.assertTrue(self.s.active())
            self.s.feed(rest, AXIS, axis)
            self.assertFalse(self.s.active())

    def test_sensor_noise_ignored(self):
        self.assertFalse(self.s.feed(25000, AXIS, 8))
        self.assertFalse(self.s.active())

    def test_attachment_not_activity(self):
        self.assertFalse(self.s.feed(1, BUTTON | INIT, 0))
        self.assertFalse(self.s.active())

    def test_slow_stick_movement_crosses_deadzone(self):
        for v in range(0, 5000, 500):
            self.assertFalse(self.s.feed(v, AXIS, 0))
        self.assertTrue(self.s.feed(5500, AXIS, 0))
        self.assertTrue(self.s.active())

    def test_drift_after_button_release_stays_idle(self):
        self.s.feed(1, BUTTON, 0)
        self.s.feed(0, BUTTON, 0)
        self.s.feed(1000, AXIS, 0)
        self.assertFalse(self.s.active())

    def test_devices_do_not_share_held_state(self):
        second = State([0])
        self.s.feed(1, BUTTON, 0)
        self.assertTrue(self.s.active())
        self.assertFalse(second.active())


class DiscoveryTests(unittest.TestCase):
    @staticmethod
    def words(bits):
        width = struct.calcsize('L') * 8
        text = f'{bits:x}'
        text = text.zfill(((len(text) + width // 4 - 1) // (width // 4)) * (width // 4))
        return [text[i:i + width // 4] for i in range(0, len(text), width // 4)]

    def test_gamepads_joysticks_and_wheels(self):
        for bit in [288, 304, 320]:
            self.assertTrue(controller_bits(self.words(1 << bit)))

    def test_keyboards_and_non_controller_hid_excluded(self):
        self.assertFalse(controller_bits(self.words((1 << 30) | (1 << 272))))
        self.assertFalse(controller_bits(['0']))


if __name__ == '__main__':
    unittest.main()
