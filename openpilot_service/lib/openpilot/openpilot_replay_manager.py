from dataclasses import dataclass

from lib.openpilot.process_management import (
    OpenpilotDockerEnv,
    RunningProcess,
    _parse_remote_process_snapshot,
    _remote_kill_replay_processes_script,
    _remote_is_running_script,
    _remote_kill_script,
    _remote_process_snapshot_script,
)


@dataclass(slots=True)
class OpenpilotReplayManager:
    env: OpenpilotDockerEnv

    def start(self, replay_id: str, *, log_path: str = "/tmp/op_replay.log") -> RunningProcess:
        replay_inner = f'./tools/replay/replay "{replay_id}" --all --ecam'
        pid = self.env.run_detached_with_pty(replay_inner, log_path=log_path)

        # stream via tail -f (separate process)
        tail_inner = f'tail -n 200 -f "{log_path}"'
        rp = self.env.run_stream(tail_inner)
        rp.remote_pid = pid
        rp.remote_cmd_substr = "./tools/replay/replay"

        snap = self.env.run_capture(_remote_process_snapshot_script(pid))
        alive, start_time, pgrp, sid, _ = _parse_remote_process_snapshot(snap)
        if alive:
            rp.remote_start_time = start_time
            rp.remote_pgid = pgrp
            rp.remote_sid = sid

        def stop_remote(force: bool) -> None:
            _ = self.env.run_capture(
                _remote_kill_script(
                    pid,
                    force=force,
                    pgid=rp.remote_pgid,
                    sid=rp.remote_sid,
                )
                + "\ntrue"
            )
            if force:
                _ = self.env.run_capture(_remote_kill_replay_processes_script() + "\ntrue")

        rp.stop_remote = stop_remote
        return rp

    def is_running(self, rp: RunningProcess) -> bool:
        if rp.remote_pid is None:
            raise ValueError("RunningProcess has no remote_pid")

        if rp.remote_start_time is not None or rp.remote_cmd_substr is not None:
            snap = self.env.run_capture(_remote_process_snapshot_script(rp.remote_pid))
            alive, start_time, pgrp, sid, cmdline = _parse_remote_process_snapshot(snap)
            if not alive:
                return False

            if rp.remote_start_time is not None and start_time != rp.remote_start_time:
                return False

            if rp.remote_pgid is not None and pgrp != rp.remote_pgid:
                return False

            if rp.remote_sid is not None and sid != rp.remote_sid:
                return False

            if rp.remote_cmd_substr is not None and rp.remote_cmd_substr not in cmdline:
                return False

            return True

        status = self.env.run_capture(_remote_is_running_script(rp.remote_pid))
        return status.strip() == "RUNNING"

    def stop_all(self) -> None:
        _ = self.env.run_capture(_remote_kill_replay_processes_script() + "\ntrue")
