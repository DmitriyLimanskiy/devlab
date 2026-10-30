"""Проверки настоящей сессии bash во вложенном PTY (macOS)"""

import fcntl
import os
import pty
import select
import json
import re
import signal
import struct
import subprocess
import sys
import termios
import time
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "darwin", "Первая версия рассчитана на macOS")
class TerminalTest(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.TemporaryDirectory()
        self.addCleanup(self.project.cleanup)
        self.master, self.slave = pty.openpty()
        self.original = termios.tcgetattr(self.slave)
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"), NO_COLOR="1", DEVLAB_OFFLINE="1")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "devlab"], stdin=self.slave,
            stdout=self.slave, stderr=self.slave, env=env,
        )
        self.read_until("Папка проекта".encode())
        os.write(self.master, self.project.name.encode() + b"\n")
        startup = self.read_until(b" > ")
        self.snapshot = Path(re.search(rb"(/[^\r\n]+/state.json)", startup).group(1).decode())

    def tearDown(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=5)
        os.close(self.master)
        os.close(self.slave)

    def read_until(self, expected):
        output = b""
        deadline = time.monotonic() + 5
        while expected not in output and time.monotonic() < deadline:
            if select.select([self.master], [], [], 0.1)[0]:
                output += os.read(self.master, 65536)
        self.assertIn(expected, output)
        return output

    def assert_terminal_restored(self):
        restored = termios.tcgetattr(self.slave)
        # macOS выставляет PENDIN при возврате в канонический режим:
        # это служебный флаг повторной обработки ожидающего ввода
        restored[3] &= ~getattr(termios, "PENDIN", 0)
        original = self.original.copy()
        original[3] &= ~getattr(termios, "PENDIN", 0)
        self.assertEqual(restored, original)

    def test_commands_resize_interrupt_and_exit(self):
        os.write(self.master, b"printf 'RESULT:%s\\n' $((6*7))\n")
        self.read_until(b"RESULT:42")
        size = struct.pack("HHHH", 31, 97, 0, 0)
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, size)
        os.kill(self.process.pid, signal.SIGWINCH)
        os.write(self.master, b"stty size\n")
        self.read_until(b"31 97")
        os.write(self.master, b"sleep 30\n")
        time.sleep(0.2)
        os.write(self.master, b"\x03")
        self.read_until(b" > ")
        os.write(self.master, b"exit 7\n")
        self.read_until("Сессия DevLab завершена".encode())
        self.assertEqual(self.process.wait(timeout=5), 7)
        self.assertTrue(self.snapshot.exists())
        self.assert_terminal_restored()

    def test_eof_exits_and_restores_terminal(self):
        os.write(self.master, b"\x04")
        self.read_until("Сессия DevLab завершена".encode())
        self.assertEqual(self.process.wait(timeout=5), 0)
        self.assert_terminal_restored()


if __name__ == "__main__":
    unittest.main()
