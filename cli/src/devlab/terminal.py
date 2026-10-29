"""Интерактивный bash через PTY: ввод, вывод и размер терминала."""

import errno
import fcntl
import os
import pty
import select
import signal
import sys
import termios
import tty


def _write_all(fd: int, data: bytes) -> None:
    while data:
        data = data[os.write(fd, data):]


def run_bash(bash: str, rc_path: str, folder, snapshot, write_snapshot=True) -> int:
    stdin, stdout = sys.stdin.fileno(), sys.stdout.fileno()
    original = termios.tcgetattr(stdin)
    from .observer import Observer

    events, notify = os.pipe()
    os.set_inheritable(notify, True)
    with open(rc_path, "a") as rc:
        rc.write("\nPROMPT_COMMAND='__devlab_status=$?; printf \"%s\\n\" \"$__devlab_status\" >&" + str(notify) + "'\n")
    pid, master = pty.fork()
    if pid == 0:
        try:
            os.close(events)
            os.chdir(folder)
            os.environ["BASH_SILENCE_DEPRECATION_WARNING"] = "1"
            os.execv(bash, [bash, "--noprofile", "--rcfile", rc_path, "-i"])
        except OSError:
            os.write(2, b"DevLab: cannot start bash\n")
            os._exit(127)

    os.close(notify)
    observer = Observer(folder, events, snapshot, os.path.join(os.path.dirname(rc_path), "command-status.json"))
    observer.preserve_existing = not write_snapshot
    observer.thread.start()

    def resize(_signum=None, _frame=None):
        size = fcntl.ioctl(stdin, termios.TIOCGWINSZ, b"\0" * 8)
        fcntl.ioctl(master, termios.TIOCSWINSZ, size)

    previous = signal.signal(signal.SIGWINCH, resize)
    finished = False
    try:
        resize()
        tty.setraw(stdin)
        while True:
            readable, _, _ = select.select([stdin, master], [], [])
            if master in readable:
                try:
                    output = os.read(master, 65536)
                except OSError as error:
                    if error.errno != errno.EIO:
                        raise
                    break
                if not output:
                    break
                _write_all(stdout, output)
            if stdin in readable:
                data = os.read(stdin, 65536)
                if not data:
                    break
                _write_all(master, data)
        _, status = os.waitpid(pid, 0)
        finished = True
        code = os.waitstatus_to_exitcode(status)
        return code if code >= 0 else 128 - code
    finally:
        termios.tcsetattr(stdin, termios.TCSADRAIN, original)
        signal.signal(signal.SIGWINCH, previous)
        os.close(master)
        if not finished:
            # Закрытие master посылает SIGHUP терминальной сессии.
            os.waitpid(pid, 0)
        observer.close()
        os.close(events)
