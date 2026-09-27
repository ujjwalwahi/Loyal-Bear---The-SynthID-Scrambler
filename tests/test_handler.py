"""Runpod request validation and image response behavior."""

import base64
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

import handler
import batch_runner


def image_base64() -> str:
    image = Image.new("RGB", (4, 4), "red")
    image.info["comment"] = "source metadata"
    stream = io.BytesIO()
    image.save(stream, format="PNG", pnginfo=None)
    return base64.b64encode(stream.getvalue()).decode("ascii")


class HandlerTests(unittest.TestCase):
    def test_rejects_invalid_requests_before_model_load(self):
        with patch.object(handler, "_get_pipeline") as load:
            bad_inputs = [
                ({}, "image_base64"),
                ({"image_base64": "invalid"}, "base64"),
                ({"image_base64": image_base64(), "strength": []}, "strength"),
                ({"image_base64": image_base64(), "prompt": 1}, "prompt"),
            ]
            for request, message in bad_inputs:
                with self.subTest(request=request), self.assertRaisesRegex(ValueError, message):
                    handler.handler({"input": request})
            load.assert_not_called()

    def test_processes_image_with_desktop_strength_and_returns_clean_png(self):
        source = image_base64()
        pipe = object()
        generated = Image.new("RGB", (4, 4), "blue")
        generated.info["secret"] = "source metadata"
        run = Mock(return_value=generated)
        pipeline = types.ModuleType("src.pipeline")
        pipeline.run_img2img = run
        with patch.object(handler, "_get_pipeline", return_value=pipe), patch.dict(
            sys.modules, {"src.pipeline": pipeline}
        ):
            result = handler.handler({"input": {
                "image_base64": f"data:image/png;base64,{source}",
                "prompt": "a blue image",
                "strength": "Strong",
            }})

        self.assertEqual(result["mime_type"], "image/png")
        self.assertEqual(result["strength"], "Strong")
        self.assertEqual(run.call_args.kwargs["denoise"], 0.1)
        self.assertIs(run.call_args.args[0], pipe)
        with Image.open(io.BytesIO(base64.b64decode(result["image_base64"]))) as image:
            self.assertEqual(image.getpixel((0, 0)), (0, 0, 255))
            self.assertEqual(image.info, {})

    def test_folder_client_saves_png_and_clears_job_state(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "input.jpg"
            source.write_bytes(base64.b64decode(image_base64()))
            output_dir = Path(scratch) / "output"
            output_dir.mkdir()
            replies = [{"id": "job-1"}, {"status": "COMPLETED", "output": {"image_base64": image_base64()}}]
            with patch.object(batch_runner, "api_request", side_effect=replies) as request:
                target = batch_runner.process_image(source, output_dir, "key", "endpoint", "a bear", "Strong", 1)
            self.assertEqual(Path(target).name, "input.jpg.png")
            self.assertEqual(Path(target).read_bytes(), source.read_bytes())
            self.assertFalse((output_dir / ".runpod_jobs" / "input.jpg.json").exists())
            self.assertEqual(request.call_args_list[0].args[2]["input"]["strength"], "Strong")


if __name__ == "__main__":
    unittest.main()
