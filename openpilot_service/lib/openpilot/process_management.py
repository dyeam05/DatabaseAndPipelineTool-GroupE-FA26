import subprocess
import shlex
from dataclasses import dataclass
from collections.abc import Sequence, Iterator, Callable


Cmd = str | Sequence[str]


@dataclass(slots=True)
class RunningProcess:
    """
    Represents a streaming job whose output is available as an iterator of lines.
    Optionally includes a 'remote_pid' for the process inside the docker container.
    """
    popen: subprocess.Popen[str]
    lines: Iterator[str]

    container: str | None = None
    remote_pid: int | None = None
    remote_pgid: int | None = None
    remote_sid: int | None = None
    remote_start_time: int | None = None
    remote_cmd_substr: str | None = None

    # optional stop hook that kills the in-container process
    stop_remote: Callable[[bool], None] | None = None  # arg = force

    def wait(self) -> int:
        return self.popen.wait()

    @property
    def returncode(self) -> int | None:
        return self.popen.returncode

    def stop(self, *, force: bool = False) -> None:
        """
        Best-effort stop:
          1) stop the remote PID (if configured)
          2) stop the local streaming process (tail -f)
        """
        if self.stop_remote is not None:
            self.stop_remote(force)

        # stop local streamer (e.g., tail -f)
        if self.popen.poll() is None:
            try:
                self.popen.terminate()
            except Exception:
                pass

        if force and self.popen.poll() is None:
            try:
                self.popen.kill()
            except Exception:
                pass


@dataclass(slots=True)
class OpenpilotDockerEnv:
    """
    Shared environment bootstrap for commands that must run inside the openpilot container.

    Sets up:
      - TERM
      - conda.sh
      - conda activate
      - venv activate
      - cd to workdir
    """
    container: str
    workdir: str = "/workspace/openpilot"
    conda_sh: str = "~/miniconda3/etc/profile.d/conda.sh"
    conda_env: str = "openpilot"
    venv_activate: str = "./.venv/bin/activate"
    term: str = "xterm"

    def bash_script(self, inner: str) -> str:
        return f"""
set -euo pipefail
export TERM={self.term}
source {self.conda_sh}
cd {self.workdir}
conda activate {self.conda_env}
source {self.venv_activate}
{inner}
""".strip()

    def docker_exec_cmd(self, inner: str, *, interactive_stdin: bool, allocate_tty: bool = False) -> list[str]:
        cmd = ["docker", "exec"]
        if interactive_stdin:
            cmd.append("-i")
        if allocate_tty:
            cmd.append("-t")
        cmd += [self.container, "bash", "-lc", self.bash_script(inner)]
        return cmd

    def run_capture(self, inner: str) -> str:
        """
        Run inside container and return stdout (merged with stderr).
        Raises CalledProcessError on nonzero exit.
        """
        cmd = self.docker_exec_cmd(inner, interactive_stdin=False)
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return out.strip()

    def run_stream(self, inner: str) -> RunningProcess:
        """
        Run inside container and stream stdout+stderr merged; yields lines (does not print).
        """
        cmd = self.docker_exec_cmd(inner, interactive_stdin=True)
        p: subprocess.Popen[str] = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        def iter_lines() -> Iterator[str]:
            assert p.stdout is not None
            for line in p.stdout:
                yield line

        return RunningProcess(popen=p, lines=iter_lines(), container=self.container)

    def run_detached_with_pty(self, inner: str, *, log_path: str) -> int:
        """
        Start command detached inside the container with an allocated PTY using `script`.
        Returns the remote PID.
        """
        quoted_inner = shlex.quote(inner)
        start_inner = f"""
rm -f "{log_path}"
setsid nohup script -q -f -c {quoted_inner} "{log_path}" < /dev/null > /dev/null 2>&1 &
echo $!
""".strip()
        return _parse_pid(self.run_capture(start_inner))


def _parse_pid(s: str) -> int:
    # sometimes extra output sneaks in; last token should be PID
    return int(s.split()[-1])


def _remote_kill_script(pid: int, *, force: bool, pgid: int | None = None, sid: int | None = None) -> str:
    """
    Best-effort kill:
      - try process group (-PID)
      - then PID
      - then children (pkill -P)
    """
    pgid_kill_term = f"kill -TERM -- -{pgid} 2>/dev/null || true" if pgid is not None else ""
    sid_kill_term = f"pkill -TERM -s {sid} 2>/dev/null || true" if sid is not None else ""

    hard = ""
    if force:
        pgid_kill_kill = f"kill -KILL -- -{pgid} 2>/dev/null || true" if pgid is not None else ""
        sid_kill_kill = f"pkill -KILL -s {sid} 2>/dev/null || true" if sid is not None else ""
        hard = f"""
sleep 0.3
{pgid_kill_kill}
{sid_kill_kill}
kill -KILL -- -{pid} 2>/dev/null || kill -KILL {pid} 2>/dev/null || true
pkill -KILL -P {pid} 2>/dev/null || true
""".strip()

    return f"""
pid={pid}
{pgid_kill_term}
{sid_kill_term}

kill -TERM -- -$pid 2>/dev/null || kill -TERM $pid 2>/dev/null || true
pkill -TERM -P $pid 2>/dev/null || true

{hard}
""".strip()


def _remote_is_running_script(pid: int) -> str:
    return f"kill -0 {pid} >/dev/null 2>&1 && echo RUNNING || echo DEAD"


def _remote_process_snapshot_script(pid: int) -> str:
    return f"""
pid={pid}
if [ ! -d "/proc/$pid" ]; then
  echo DEAD
  exit 0
fi

start_time=$(awk '{{print $22}}' "/proc/$pid/stat" 2>/dev/null || true)
pgrp=$(awk '{{print $5}}' "/proc/$pid/stat" 2>/dev/null || true)
sid=$(awk '{{print $6}}' "/proc/$pid/stat" 2>/dev/null || true)
cmd=$(tr '\\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)

if [ -z "$start_time" ] || [ -z "$pgrp" ] || [ -z "$sid" ]; then
  echo DEAD
  exit 0
fi

echo "RUNNING|$start_time|$pgrp|$sid|$cmd"
""".strip()


def _parse_remote_process_snapshot(raw: str) -> tuple[bool, int | None, int | None, int | None, str]:
    s = raw.strip()
    if not s.startswith("RUNNING|"):
        return False, None, None, None, ""

    parts = s.split("|", 4)
    start_time: int | None = None
    pgrp: int | None = None
    sid: int | None = None
    if len(parts) > 1 and parts[1].isdigit():
        start_time = int(parts[1])
    if len(parts) > 2 and parts[2].isdigit():
        pgrp = int(parts[2])
    if len(parts) > 3 and parts[3].isdigit():
        sid = int(parts[3])
    cmdline = parts[4] if len(parts) > 4 else ""
    return True, start_time, pgrp, sid, cmdline


def _remote_kill_replay_processes_script() -> str:
    return """
for pid in $(ps -eo pid=,args= | awk '/[t]ools\/replay\/replay / {print $1}'); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill -TERM "$pid" 2>/dev/null || true
done

for pid in $(ps -eo pid=,args= | awk '/[s]cript -q -f -c .*tools\/replay\/replay/ {print $1}'); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill -TERM "$pid" 2>/dev/null || true
done

sleep 0.5

for pid in $(ps -eo pid=,args= | awk '/[t]ools\/replay\/replay / {print $1}'); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill -KILL "$pid" 2>/dev/null || true
done

for pid in $(ps -eo pid=,args= | awk '/[s]cript -q -f -c .*tools\/replay\/replay/ {print $1}'); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill -KILL "$pid" 2>/dev/null || true
done
""".strip()


def _remote_kill_extraction_processes_script() -> str:
    return """
for pid in $(ps -eo pid=,args= | awk '/[p]ython .*selfdrive\/modeld\/extract_data.py / {print $1}'); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill -TERM "$pid" 2>/dev/null || true
done

sleep 0.5

for pid in $(ps -eo pid=,args= | awk '/[p]ython .*selfdrive\/modeld\/extract_data.py / {print $1}'); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill -KILL "$pid" 2>/dev/null || true
done
""".strip()
