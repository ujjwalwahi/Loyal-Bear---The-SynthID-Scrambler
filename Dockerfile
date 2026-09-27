FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    HF_HOME=/runpod-volume/huggingface \
    XDG_CACHE_HOME=/runpod-volume/.cache \
    LOYALBEAR_MODEL_PATH=/runpod-volume/models/epicrealismXL_pureFix.safetensors

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.10 python3.10-venv python3-pip libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && python3.10 -m venv "$VIRTUAL_ENV"

WORKDIR /opt/loyalbear
COPY requirements-runpod.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install torch==2.6.0 torchvision==0.21.0 \
        --index-url https://download.pytorch.org/whl/cu118 \
    && python -m pip install -r requirements-runpod.txt \
    && python -c 'import torch; assert torch.version.cuda == "11.8"' \
    && python -c 'from diffusers import StableDiffusionXLImg2ImgPipeline' \
    && python -c 'import runpod; assert callable(runpod.serverless.start)'

COPY src/ ./src/
COPY handler.py ./handler.py
CMD ["python", "-u", "/opt/loyalbear/handler.py"]
