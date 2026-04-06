import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import zipfile

import pytest

# These are fake creds for testing purposes only, they arent fr used 
# need them so import-time env checks don't crash during test collection
os.environ.setdefault("CVAT_EMAIL", "test@example.com")
os.environ.setdefault("CVAT_PASSWORD", "test-password")
os.environ.setdefault("CVAT_HOST", "http://localhost")
os.environ.setdefault("CVAT_SHARE_ROOT", "/tmp")

from services.cvat_service import CVATService
import services.cvat_service as cvat_service_module


@pytest.fixture
def service() -> CVATService:
    # Avoid __init__ so tests can set a mocked client explicitly.
    return CVATService.__new__(CVATService)


# Verifies that CVATService.__init__ calls create_cvat_client(), stores result in self.cvat_client
# Making sure initialization wires dependencies correctly and doesn't hide extra behavior
def test_init_creates_cvat_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = object()
    monkeypatch.setattr(cvat_service_module, "create_cvat_client", lambda: fake_client)

    created = CVATService()

    assert created.cvat_client is fake_client

# Verifies that check_cvat_connection() calls tasks.list(return_json-False) on the client
# Confirms the service is using the expected SDK call to validate connection/auth using a mock cvat_client.tasks.list
def test_check_cvat_connection_success(service: CVATService) -> None:
    tasks = SimpleNamespace(list=Mock(return_value=None))
    service.cvat_client = SimpleNamespace(tasks=tasks)

    service.check_cvat_connection()

    tasks.list.assert_called_once_with(return_json=False)

# Verifies connection/auth errors are wrapped as RuntimeError properly
# Makes sure calls get understandable errors and not some raw SDK exceptions
def test_check_cvat_connection_raises_runtime_error(service: CVATService) -> None:
    tasks = SimpleNamespace(list=Mock(side_effect=Exception("boom")))
    service.cvat_client = SimpleNamespace(tasks=tasks)

    with pytest.raises(RuntimeError, match="Failed to connect/authenticate to CVAT"):
        service.check_cvat_connection()

# Simulates one failed connection then success, and checks retry logic returns 
# Makes sure function returns successfully after a retry 
def test_wait_for_cvat_succeeds_after_retry(
    service: CVATService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = {"count": 0}

    def fake_check() -> None:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("not ready")

    service.check_cvat_connection = fake_check  # type: ignore[assignment]
    monkeypatch.setattr(cvat_service_module.time, "sleep", lambda _seconds: None)

    service.wait_for_cvat(max_wait_seconds=10, poll_interval=0)

    assert attempts["count"] == 2

# Simulates repeated failure until timeout and checks the timeout RuntimeError
# Makes sure RuntimeError including the timeout context is thrown, so no infinite loops and proper failure when CVAt is never ready
def test_wait_for_cvat_times_out(
    service: CVATService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service.check_cvat_connection = Mock(side_effect=RuntimeError("still down"))  # type: ignore[assignment]

    times = iter([0, 1, 3])
    monkeypatch.setattr(cvat_service_module.time, "time", lambda: next(times))
    monkeypatch.setattr(cvat_service_module.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="CVAT did not become ready within 2s"):
        service.wait_for_cvat(max_wait_seconds=2, poll_interval=0)

# Verifies image + lables are used to build a task, create_from_data is called correctly, and returned id is good
# Mocks get_pngs to return fake pics, replace TaskWriteReq with a capture class, and mock tasks.create_from_data to return id 123
# Makes sure task spec contains expected name and labels, create_from_data called with ResourceType.LOCAL and expected resources, 
# and that return value is task id 123
def test_create_new_task_for_img_dir(
    service: CVATService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_task_spec: dict = {}

    class FakeTaskWriteRequest:
        def __init__(self, **kwargs):
            captured_task_spec.update(kwargs)

    created_task = SimpleNamespace(id=123)
    create_from_data = Mock(return_value=created_task)
    service.cvat_client = SimpleNamespace(tasks=SimpleNamespace(create_from_data=create_from_data))

    monkeypatch.setattr(cvat_service_module, "TaskWriteRequest", FakeTaskWriteRequest)
    monkeypatch.setattr(cvat_service_module, "get_pngs_in_directory", lambda dir: ["img1.png", "img2.png"])

    fake_function = SimpleNamespace(labels=[{"name": "car"}])
    task_id = service.create_new_task_for_img_dir(Path("/tmp/segment"), fake_function)  # type: ignore[arg-type]

    assert task_id == 123
    assert captured_task_spec["name"] == "/tmp/segment"
    assert captured_task_spec["labels"] == [{"name": "car"}]
    create_from_data.assert_called_once()
    kwargs = create_from_data.call_args.kwargs
    assert kwargs["resource_type"] == cvat_service_module.ResourceType.LOCAL
    assert kwargs["resources"] == ["img1.png", "img2.png"]

# Verifies annotate_task() delegates to cvat_sdk.auto_annotation.annotate_task with correct args
# Makes sure the wrapper passes what the CVAT auto-annotate API needs using a mock 
def test_annotate_task_calls_sdk(service: CVATService) -> None:
    service.cvat_client = object()
    annotate_mock = Mock()
    original_annotate = cvat_service_module.cvataa.annotate_task
    cvat_service_module.cvataa.annotate_task = annotate_mock
    try:
        fake_function = SimpleNamespace()
        service.annotate_task(task_id=99, cvat_function=fake_function)  # type: ignore[arg-type]
    finally:
        cvat_service_module.cvataa.annotate_task = original_annotate

    annotate_mock.assert_called_once_with(service.cvat_client, 99, fake_function)

# Simulates a CVAT export zip containing a JSON, verifies the JSON is extracted to output path, and zip is removed
# Makes sure output json is created, file content matches the expected json, and that the intermediate zip is removed
def test_export_task_coco_extracts_json_and_deletes_zip(
    service: CVATService,
    tmp_path: Path,
) -> None:
    task_id = 7
    zip_path = tmp_path / f"task_{task_id}.zip"

    def fake_export_dataset(format_name: str, filename: Path, include_images: bool) -> None:
        assert format_name == "COCO 1.0"
        assert filename == zip_path
        assert include_images is False
        with zipfile.ZipFile(filename, "w") as zf:
            zf.writestr("annotations/default.json", '{"ok": true}')

    fake_task = SimpleNamespace(export_dataset=fake_export_dataset)
    service.cvat_client = SimpleNamespace(tasks=SimpleNamespace(retrieve=Mock(return_value=fake_task)))

    out_path = service.export_task_coco(task_id=task_id, output_dir=tmp_path)

    assert out_path == tmp_path / "task_7.json"
    assert out_path.exists()
    assert out_path.read_text() == '{"ok": true}'
    assert not zip_path.exists()

# Simulates a zip with no JSON to verify the FileNotFoundError 
# Makes sure corrupt/invalid exports fail in an expected way 
def test_export_task_coco_raises_when_no_json_in_zip(
    service: CVATService,
    tmp_path: Path,
) -> None:
    task_id = 9
    zip_path = tmp_path / f"task_{task_id}.zip"

    def fake_export_dataset(format_name: str, filename: Path, include_images: bool) -> None:
        with zipfile.ZipFile(filename, "w") as zf:
            zf.writestr("images/readme.txt", "no annotations")

    fake_task = SimpleNamespace(export_dataset=fake_export_dataset)
    service.cvat_client = SimpleNamespace(tasks=SimpleNamespace(retrieve=Mock(return_value=fake_task)))

    with pytest.raises(FileNotFoundError, match=f"No coco files found in {zip_path}"):
        service.export_task_coco(task_id=task_id, output_dir=tmp_path)

# Verifies orchestration order in get_detections_for_segment() and returned output path
# Makes sure methods called in expected pipeline with correct args, and final returned path is what export_task_coco returned
# This makes sure control and data passing is chill 
def test_get_detections_for_segment_happy_path(
    service: CVATService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    segment_dir = Path("/tmp/segment")
    output_dir = Path("/tmp/out")
    expected_output = output_dir / "task_1.json"
    fake_function = SimpleNamespace()

    monkeypatch.setattr(cvat_service_module, "does_dir_exist", lambda dir: True)
    service.wait_for_cvat = Mock()  # type: ignore[assignment]
    service.create_new_task_for_img_dir = Mock(return_value=1)  # type: ignore[assignment]
    service.annotate_task = Mock()  # type: ignore[assignment]
    service.export_task_coco = Mock(return_value=expected_output)  # type: ignore[assignment]

    result = service.get_detections_for_segment(
        segment_dir=segment_dir,
        cvat_function=fake_function,  # type: ignore[arg-type]
        output_dir=output_dir,
    )

    assert result == expected_output
    service.wait_for_cvat.assert_called_once_with()
    service.create_new_task_for_img_dir.assert_called_once_with(
        segment_dir=segment_dir,
        cvat_function=fake_function,
    )
    service.annotate_task.assert_called_once_with(task_id=1, cvat_function=fake_function)
    service.export_task_coco.assert_called_once_with(task_id=1, output_dir=output_dir)

# Verifies missing segment dir raises RuntimeError and stops before CVAT calls it
# Makes sure we error out before network/SDK work if needed 
def test_get_detections_for_segment_raises_if_dir_missing(
    service: CVATService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    segment_dir = Path("/tmp/missing")
    output_dir = Path("/tmp/out")
    fake_function = SimpleNamespace()

    monkeypatch.setattr(cvat_service_module, "does_dir_exist", lambda dir: False)
    service.wait_for_cvat = Mock()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match=f"Directory {segment_dir} does not exist."):
        service.get_detections_for_segment(
            segment_dir=segment_dir,
            cvat_function=fake_function,  # type: ignore[arg-type]
            output_dir=output_dir,
        )

    service.wait_for_cvat.assert_not_called()
