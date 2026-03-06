from dataclasses import dataclass

from lib.openpilot.process_management import (
    OpenpilotDockerEnv,
    RunningProcess,
    _parse_pid,
    _remote_kill_extraction_processes_script,
    _remote_kill_script,
)


@dataclass(slots=True)
class OpenpilotExtractionManager:
    env: OpenpilotDockerEnv

    def start(self, output_dir: str, *, log_path: str = "/tmp/op_extract.log") -> RunningProcess:
        """
        Detached extraction + tail logs, killable via remote PID.
        """
        start_inner = f"""
rm -f "{log_path}"
nohup python ./selfdrive/modeld/extract_data.py --output_dir "{output_dir}" > "{log_path}" 2>&1 < /dev/null &
echo $!
""".strip()

        pid = _parse_pid(self.env.run_capture(start_inner))

        tail_inner = f"""
    while [ ! -f "{log_path}" ]; do
      kill -0 {pid} >/dev/null 2>&1 || break
      sleep 0.1
    done
    tail --pid={pid} -n 200 -f "{log_path}" || true
    """.strip()
        rp = self.env.run_stream(tail_inner)
        rp.remote_pid = pid

        def stop_remote(force: bool) -> None:
            _ = self.env.run_capture(_remote_kill_script(pid, force=force) + "\ntrue")
            if force:
                _ = self.env.run_capture(_remote_kill_extraction_processes_script() + "\ntrue")

        rp.stop_remote = stop_remote
        return rp

    def stop_all(self) -> None:
        _ = self.env.run_capture(_remote_kill_extraction_processes_script() + "\ntrue")

    def run_foreground(self, output_dir: str) -> RunningProcess:
        """
        Foreground extraction (exact exit code), streams python output directly.
        NOTE: stopping is less deterministic than detached PID approach.
        """
        inner = f'python ./selfdrive/modeld/extract_data.py --output_dir "{output_dir}"'
        return self.env.run_stream(inner)
