from enum import Enum
from pathlib import Path
from uuid import uuid4



def log_route(route: str, container: str = "custom_openpilot-dev-1") -> str:
    """_summary_

    Args:
        route (str): _description_
        container (str, optional): _description_. Defaults to "custom_openpilot-dev-1".

    Returns:
        Path: Path to the directory where the files were saved
    """

    unique_str = uuid4().hex
    output_dir = f"/workspace/data/{unique_str}"

    env = OpenpilotDockerEnv(container=container)
    replay_manager = OpenpilotReplayManager(env=env)
    extraction_manager = OpenpilotExtractionManager(env=env)

    # Start extraction first
    extraction_job = extraction_manager.start(output_dir=output_dir)

    # start replay
    replay_job = replay_manager.start(replay_id=route)

    # wait for extraction job to say it is done
    extraction_job.wait()

    # kill both
    extraction_job.stop(force=True)
    replay_job.stop(force=True)

    return output_dir