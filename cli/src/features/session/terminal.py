import errno
import fcntl
import os
import pty
import select
import signal
import sys
import tempfile
import termios
import tty


def _write_all(fd: int, data: bytes) -> None:
    """Передать все байты в дескриптор с учётом неполной записи"""
    while data:
        data = data[os.write(fd, data) :]


def run_bash(
    bash: str, rc_path: str, folder, snapshot, write_snapshot=True, sender=None
) -> int:
    """Запустить bash через PTY с наблюдением Git и восстановлением терминала"""
    stdin, stdout = sys.stdin.fileno(), sys.stdout.fileno()
    original = termios.tcgetattr(stdin)
    from cli.src.features.git_practice.observer import Observer

    events, notify = os.pipe()
    os.set_inheritable(notify, True)
    with open(rc_path, "a") as rc:
        rc.write(
            '\nPROMPT_COMMAND=\'__stack_forge_status=$?; printf "%s\\n" "$__stack_forge_status" >&'
            + str(notify)
            + "'\n"
        )
    from cli.src.features.session.control import LocalControl

    control_directory = tempfile.TemporaryDirectory(
        prefix="stack-forge-control-", dir="/tmp"
    )
    control = LocalControl(os.path.join(control_directory.name, "control.sock"), None)
    pid, master = pty.fork()
    if pid == 0:
        try:
            os.close(events)
            control.listener.close()
            os.environ["STACK_FORGE_CONTROL_SOCKET"] = str(control.path)
            os.chdir(folder)
            os.environ["BASH_SILENCE_DEPRECATION_WARNING"] = "1"
            os.execv(bash, [bash, "--noprofile", "--rcfile", rc_path, "-i"])
        except OSError:
            os.write(2, b"Stack Forge: cannot start bash\n")
            os._exit(127)

    os.close(notify)
    # Потоки запускаются после fork: не наследуем блокировки фонового отправителя
    runtime = None
    if sender is not None:
        from cli.src.features.git_practice.runtime import PracticeRuntime

        runtime = PracticeRuntime(sender, folder, snapshot)
        control.runtime = runtime
        runtime.start()
    observer = Observer(
        folder,
        events,
        snapshot,
        os.path.join(os.path.dirname(rc_path), "command-status.json"),
        on_state=runtime.publish if runtime is not None else None,
        on_worktree=runtime.seed if runtime is not None else None,
        internal_dir=sender.pending_path.parent if sender is not None else None,
    )
    if runtime is not None:
        runtime.observer = observer
    control.start()
    observer.preserve_existing = not write_snapshot
    observer.thread.start()

    def resize(_signum=None, _frame=None):
        """Передать актуальный размер внешнего терминала дочернему PTY"""
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
            # Закрытие master посылает SIGHUP терминальной сессии
            os.waitpid(pid, 0)
        control.close()
        control_directory.cleanup()
        observer.close()
        os.close(events)
        if runtime is not None:
            runtime.close()
            if message := runtime.sender.summary():
                print(f"\n  Синхронизация: {message}", flush=True)
