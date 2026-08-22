import os
import sys
import warnings
import torch
from diffusers import StableDiffusionXLImg2ImgPipeline, EulerDiscreteScheduler
from PIL import Image

warnings.filterwarnings("ignore")
import logging
logging.getLogger("diffusers").setLevel(logging.ERROR)

NEGATIVE_PROMPT = "ugly, blurry, low quality, deformed, bad anatomy, watermark, text"
MODEL_FILENAME = "epicrealismXL_pureFix.safetensors"
MODEL_REPO = "phuaqu/zimage111"


def _download_model(path: str, cb=None):
    import huggingface_hub

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if cb:
        cb("Downloading model (~6.9 GB)...")

    huggingface_hub.hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILENAME,
        local_dir=os.path.dirname(path),
        resume_download=True,
    )


def load_pipeline(model_path: str) -> StableDiffusionXLImg2ImgPipeline:
    if not os.path.isfile(model_path):
        _download_model(model_path)

    pipe = StableDiffusionXLImg2ImgPipeline.from_single_file(
        model_path,
        torch_dtype=torch.float32,
        use_safetensors=True,
    )
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.to("cpu")
    return pipe


def run_img2img(
    pipe: StableDiffusionXLImg2ImgPipeline,
    image: Image.Image,
    prompt: str,
    denoise: float = 0.5,
    steps: int = 5,
    cfg: float = 6.6,
    seed: int = -1,
) -> Image.Image:
    generator = None
    if seed >= 0:
        generator = torch.Generator(device="cpu").manual_seed(seed)

    original_size = image.size
    image = image.resize((1024, 1024), Image.LANCZOS).convert("RGB")

    result = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        image=image,
        strength=denoise,
        num_inference_steps=100,
        guidance_scale=cfg,
        generator=generator,
    ).images[0]

    if original_size != (1024, 1024):
        result = result.resize(original_size, Image.LANCZOS)

    return result
