# Runpod Serverless endpoint

The root [Dockerfile](../Dockerfile) builds a CUDA worker for a **Queue**
endpoint. Its root-level `handler.py` starts `runpod.serverless.start`. The
worker uses Loyal Bear's existing image pipeline and returns a PNG with image
metadata removed. The desktop app in `main.py` remains available separately.

## Deploy

Import this repository in the Runpod Serverless console using `Dockerfile` as
the Dockerfile path, or build and push an image from the repository root:

```bash
docker build --platform linux/amd64 -t YOUR_REGISTRY/loyalbear:runpod .
docker push YOUR_REGISTRY/loyalbear:runpod
```

Select an NVIDIA GPU endpoint with enough VRAM for SDXL image to image
inference. Attach a network volume with room for the approximately 6.9 GB
model and its download/cache files. The worker defaults to:

```text
LOYALBEAR_MODEL_PATH=/runpod-volume/models/epicrealismXL_pureFix.safetensors
HF_HOME=/runpod-volume/huggingface
XDG_CACHE_HOME=/runpod-volume/.cache
```

Runpod mounts a Serverless network volume at `/runpod-volume`. The model
downloads on the first request and is reused on subsequent requests. Set
`HF_TOKEN` if the model repository requires authentication. Allow a longer
execution timeout for the first download and model load.

## Request

Send PNG, JPEG, or WebP bytes as plain base64 or a base64 data URL. Input and
output image bytes each have a 16 MiB limit, and input images may have up to
36 megapixels. `prompt` is the image description used by the desktop app;
`strength` accepts `Light` (default) or `Strong`.

```json
{
  "input": {
    "image_base64": "BASE64_IMAGE_BYTES",
    "prompt": "Describe the image",
    "strength": "Light"
  }
}
```

The output contains `image_base64`, `mime_type` (`image/png`), and `strength`.
For longer inference jobs, submit to `/run` and poll `/status/{job_id}`:

```python
import base64
import os
import time
from pathlib import Path

import requests

endpoint = "YOUR_ENDPOINT_ID"
headers = {"Authorization": f"Bearer {os.environ['RUNPOD_API_KEY']}"}
response = requests.post(
    f"https://api.runpod.ai/v2/{endpoint}/run",
    headers=headers,
    json={"input": {
        "image_base64": base64.b64encode(Path("input.png").read_bytes()).decode(),
        "prompt": "A detailed photograph",
        "strength": "Light",
    }},
    timeout=30,
)
response.raise_for_status()
job_id = response.json()["id"]
while True:
    response = requests.get(
        f"https://api.runpod.ai/v2/{endpoint}/status/{job_id}",
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    job = response.json()
    if job["status"] == "COMPLETED":
        break
    if job["status"] in {"FAILED", "CANCELLED", "TIMED_OUT"}:
        raise RuntimeError(job)
    time.sleep(5)

Path("clean.png").write_bytes(base64.b64decode(job["output"]["image_base64"]))
```

## Process a folder

From the repository root, put images in `input/`, then run:

```bash
export RUNPOD_API_KEY="your-api-key"
export RUNPOD_ENDPOINT_ID="your-endpoint-id"
python3 batch_runner.py --prompt "A detailed photograph" --strength Light
```

The client submits one image at a time, polls the job, and writes PNG results
to `output/` as `original-filename.png`. It skips existing outputs and saves
in-progress job IDs under `output/.runpod_jobs/` so a stopped run can resume.
Use `--limit 1` for a first request or `--dry-run` to list pending files.

Invalid input or processing failures result in a failed Runpod job. The worker
accepts image bytes only, not remote URLs or video files.
