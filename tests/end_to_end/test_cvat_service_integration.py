import json
import os
from pathlib import Path

import pytest
from PIL import Image
from cvat_sdk import make_client

os.environ.setdefault("CVAT_EMAIL", os.environ.get("CVAT_EMAIL", ""))
os.environ.setdefault("CVAT_PASSWORD", os.environ.get("CVAT_PASSWORD", ""))
os.environ.setdefault("CVAT_HOST", os.environ.get("CVAT_HOST", "http://cvat-server:8080"))
os.environ.setdefault("CVAT_SHARE_ROOT", os.environ.get("CVAT_SHARE_ROOT", "/tmp"))

from services.cvat_service import CVATService
from cvat_annotation_functions.cvat_detr_detection import CVATDetrDetection

CVAT_HOST = os.environ["CVAT_HOST"]
CVAT_EMAIL = os.environ["CVAT_EMAIL"]
CVAT_PASSWORD = os.environ["CVAT_PASSWORD"]


def generate_images(directory: Path, count: int) -> list[Path]:
    paths = []
    for i in range(count):
        img_path = directory / f"test_image_{i}.png"
        img = Image.new("RGB", (64, 64), color=(i % 256, 0, 0))
        img.save(img_path)
        paths.append(img_path)
    return paths


def make_fake_cvat_function(labels: dict[int, str] = {0: "car", 1: "person"}):
    """Creates a CVATDetrDetection without loading the model, for use in non-inference tests."""
    func = CVATDetrDetection.__new__(CVATDetrDetection)
    func.raw_labels = labels
    return func


@pytest.fixture
def cvat_client():
    with make_client(CVAT_HOST, credentials=(CVAT_EMAIL, CVAT_PASSWORD)) as client:
        yield client


@pytest.fixture
def service() -> CVATService:
    return CVATService()


@pytest.fixture
def cleanup_tasks(cvat_client):
    task_ids: list[int] = []
    yield task_ids
    for task_id in task_ids:
        try:
            cvat_client.tasks.retrieve(task_id).remove()
        except Exception:
            print(f"Could not delete task {task_id}")


# ==============================================================================
# Connection Tests
# ==============================================================================

class TestCVATConnection:
    def test_check_cvat_connection_succeeds(self, service: CVATService) -> None:
        # Should not raise when CVAT is actually running
        service.check_cvat_connection()

    def test_wait_for_cvat_returns_within_timeout(self, service: CVATService) -> None:
        # With CVAT running, should return well before timeout
        service.wait_for_cvat(max_wait_seconds=30)


# ==============================================================================
# Task Creation Tests
# ==============================================================================

class TestCreateTask:
    def test_create_task_uploads_correct_image_count(
        self, tmp_path: Path, service: CVATService, cvat_client, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 5)
        task_id = service.create_new_task_for_img_dir(
            segment_dir=tmp_path,
            cvat_function=make_fake_cvat_function(),
        )
        cleanup_tasks.append(task_id)

        task = cvat_client.tasks.retrieve(task_id)
        assert task.size == 5

    def test_create_task_returns_positive_integer_id(
        self, tmp_path: Path, service: CVATService, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 2)
        task_id = service.create_new_task_for_img_dir(
            segment_dir=tmp_path,
            cvat_function=make_fake_cvat_function(),
        )
        cleanup_tasks.append(task_id)

        assert isinstance(task_id, int)
        assert task_id > 0

    def test_create_task_name_matches_segment_dir(
        self, tmp_path: Path, service: CVATService, cvat_client, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 2)
        task_id = service.create_new_task_for_img_dir(
            segment_dir=tmp_path,
            cvat_function=make_fake_cvat_function(),
        )
        cleanup_tasks.append(task_id)

        task = cvat_client.tasks.retrieve(task_id)
        assert task.name == str(tmp_path)

    def test_create_task_empty_dir_creates_task_with_no_images(
        self, tmp_path: Path, service: CVATService, cvat_client, cleanup_tasks: list
    ) -> None:
        # No PNGs in directory - CVAT creates the task but with 0 images
        task_id = service.create_new_task_for_img_dir(
            segment_dir=tmp_path,
            cvat_function=make_fake_cvat_function(),
        )
        cleanup_tasks.append(task_id)

        task = cvat_client.tasks.retrieve(task_id)
        assert task.size == 0

    def test_create_two_tasks_get_different_ids(
        self, tmp_path: Path, service: CVATService, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 2)
        id_1 = service.create_new_task_for_img_dir(tmp_path, make_fake_cvat_function())
        id_2 = service.create_new_task_for_img_dir(tmp_path, make_fake_cvat_function())
        cleanup_tasks.extend([id_1, id_2])

        assert id_1 != id_2


# ==============================================================================
# Export Tests
# ==============================================================================

class TestExportTask:
    def test_export_creates_json_file_on_disk(
        self, tmp_path: Path, service: CVATService, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 3)
        task_id = service.create_new_task_for_img_dir(tmp_path, make_fake_cvat_function())
        cleanup_tasks.append(task_id)

        out_path = service.export_task_coco(task_id=task_id, output_dir=tmp_path)

        assert out_path.exists()
        assert out_path.suffix == ".json"

    def test_export_produces_valid_coco_structure(
        self, tmp_path: Path, service: CVATService, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 3)
        task_id = service.create_new_task_for_img_dir(tmp_path, make_fake_cvat_function())
        cleanup_tasks.append(task_id)

        out_path = service.export_task_coco(task_id=task_id, output_dir=tmp_path)
        data = json.loads(out_path.read_text())

        assert "images" in data
        assert "annotations" in data
        assert "categories" in data

    def test_export_image_count_matches_uploaded(
        self, tmp_path: Path, service: CVATService, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 5)
        task_id = service.create_new_task_for_img_dir(tmp_path, make_fake_cvat_function())
        cleanup_tasks.append(task_id)

        out_path = service.export_task_coco(task_id=task_id, output_dir=tmp_path)
        data = json.loads(out_path.read_text())

        assert len(data["images"]) == 5

    def test_export_has_no_annotations_before_annotation_run(
        self, tmp_path: Path, service: CVATService, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 3)
        task_id = service.create_new_task_for_img_dir(tmp_path, make_fake_cvat_function())
        cleanup_tasks.append(task_id)

        out_path = service.export_task_coco(task_id=task_id, output_dir=tmp_path)
        data = json.loads(out_path.read_text())

        assert data["annotations"] == []

    def test_export_cleans_up_zip_after_success(
        self, tmp_path: Path, service: CVATService, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 2)
        task_id = service.create_new_task_for_img_dir(tmp_path, make_fake_cvat_function())
        cleanup_tasks.append(task_id)

        service.export_task_coco(task_id=task_id, output_dir=tmp_path)

        assert not (tmp_path / f"task_{task_id}.zip").exists()

    def test_export_nonexistent_task_raises(
        self, tmp_path: Path, service: CVATService
    ) -> None:
        with pytest.raises(Exception):
            service.export_task_coco(task_id=999999999, output_dir=tmp_path)


# ==============================================================================
# Full Pipeline Tests
# ==============================================================================

class TestGetDetectionsForSegment:
    def test_raises_if_segment_dir_missing(
        self, tmp_path: Path, service: CVATService
    ) -> None:
        missing_dir = tmp_path / "does_not_exist"

        with pytest.raises(RuntimeError, match=f"Directory {missing_dir} does not exist"):
            service.get_detections_for_segment(
                segment_dir=missing_dir,
                cvat_function=make_fake_cvat_function(),
                output_dir=tmp_path,
            )

    def test_output_path_naming_convention(
        self, tmp_path: Path, service: CVATService, cvat_client, cleanup_tasks: list
    ) -> None:
        # Verify the output file is named task_<id>.json by checking the pattern
        # Uses a real task but skips model inference by mocking annotate_task
        generate_images(tmp_path, 2)
        func = make_fake_cvat_function()

        from unittest.mock import patch
        with patch.object(service, "annotate_task"):
            out_path = service.get_detections_for_segment(
                segment_dir=tmp_path,
                cvat_function=func,
                output_dir=tmp_path,
            )

        # cleanup the task that was created
        all_tasks = cvat_client.tasks.list()
        for task in all_tasks:
            if task.name == str(tmp_path):
                cleanup_tasks.append(task.id)

        assert out_path.name.startswith("task_")
        assert out_path.suffix == ".json"
        assert out_path.exists()

    # NOTE: This test runs the DETR model - it will be slow and requires the model weights
    @pytest.mark.slow
    def test_full_pipeline_produces_valid_coco(
        self, tmp_path: Path, service: CVATService, cvat_client, cleanup_tasks: list
    ) -> None:
        generate_images(tmp_path, 3)
        cvat_function = CVATDetrDetection()

        out_path = service.get_detections_for_segment(
            segment_dir=tmp_path,
            cvat_function=cvat_function,
            output_dir=tmp_path,
        )

        all_tasks = cvat_client.tasks.list()
        for task in all_tasks:
            if task.name == str(tmp_path):
                cleanup_tasks.append(task.id)

        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert "images" in data
        assert "annotations" in data
        assert len(data["images"]) == 3
