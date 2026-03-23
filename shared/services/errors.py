from uuid import UUID
from db.models.segment_artifact import ArtifactRole
# This file defines custom exceptions for the services layer. 
# These exceptions are used to indicate specific error conditions that can occur when working 
class RouteAlreadyExistsError(ValueError):
    def __init__(self, route_id: str) -> None:
        super().__init__(f"Route {route_id} already exists")


class RouteNotFoundError(ValueError):
    def __init__(self, route_id: str) -> None:
        super().__init__(f"Route {route_id} not found")

class SegmentAlreadyExistsError(ValueError):
    def __init__(self, route_id: str, segment_id: int) -> None:
        super().__init__(f"Segment {segment_id} for route {route_id} already exists")
class SegmentNotFoundError(ValueError):
    def __init__(self, route_id: str, segment_id: int) -> None:
        super().__init__(f"Segment {segment_id} for route {route_id} not found")
class FrameAlreadyExistsError(ValueError):
    def __init__(self, frame_pk: int) -> None:
        super().__init__(f"Frame {frame_pk} already exists")
class FrameNotFoundError(ValueError):
    def __init__(self, frame_pk: int) -> None:
        super().__init__(f"Frame {frame_pk} not found")

class ArtifactAlreadyExistsError(ValueError):
    def __init__(self, artifact_id: UUID) -> None:
        super().__init__(f"Artifact {artifact_id} already exists")

class ArtifactNotFoundError(ValueError):
    def __init__(self, artifact_id: UUID) -> None:
        super().__init__(f"Artifact {artifact_id} not found")

class SegmentArtifactAlreadyExistsError(ValueError):
    def __init__(self, route_id: str, segment_id: int, role: ArtifactRole) -> None:
        super().__init__(f"Segment artifact with role {role} for segment {segment_id} and route {route_id} already exists")

class SegmentArtifactNotFoundError(ValueError):
    def __init__(self, route_id: str, segment_id: int, role: ArtifactRole) -> None:
        super().__init__(f"Segment artifact with role {role} for segment {segment_id} and route {route_id} not found")

class FrameArtifactAlreadyExistsError(ValueError):
    def __init__(self, frame_pk: int, role: ArtifactRole) -> None:
        super().__init__(f"Frame artifact with role {role} for frame {frame_pk} already exists")

class FrameArtifactNotFoundError(ValueError):
    def __init__(self, frame_pk: int, role: ArtifactRole) -> None:
        super().__init__(f"Frame artifact with role {role} for frame {frame_pk} not found")

class JobDefinitionAlreadyExistsError(ValueError):
    def __init__(self, job_def_id: int) -> None:
        super().__init__(f"Job definition {job_def_id} already exists")

class JobDefinitionNotFoundError(ValueError):
    def __init__(self, job_def_id: int) -> None:
        super().__init__(f"Job definition {job_def_id} not found")

class JobRunAlreadyExistsError(ValueError):
    def __init__(self, job_run_id: UUID) -> None:
        super().__init__(f"Job run {job_run_id} already exists")

class JobRunNotFoundError(ValueError):
    def __init__(self, job_run_id: UUID) -> None:
        super().__init__(f"Job run {job_run_id} not found")

class JobFrameArtifactAlreadyExistsError(ValueError):
    def __init__(self, job_run_id: UUID, frame_pk: int, role: ArtifactRole) -> None:
        super().__init__(f"Job frame artifact with role {role} for frame {frame_pk} and job run {job_run_id} already exists")


class JobFrameArtifactNotFoundError(ValueError):
    def __init__(self, job_run_id: UUID, frame_pk: int, role: ArtifactRole) -> None:
        super().__init__(f"Job frame artifact with role {role} for frame {frame_pk} and job run {job_run_id} not found")