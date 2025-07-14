import io

import torch
from diffusers import AutoencoderKL, DDIMScheduler, StableDiffusionPipeline
from ip_adapter import IPAdapter
from PIL import Image


BASE_MODEL_PATH = "SG161222/Realistic_Vision_V4.0_noVAE"
VAE_MODEL_PATH = "stabilityai/sd-vae-ft-mse"
IMAGE_ENCODER_PATH = "/workspace/models/image_encoder"
IP_CKPT = "/workspace/models/ip-adapter_sd15.bin"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

noise_scheduler = DDIMScheduler(
    num_train_timesteps=1000,
    beta_start=0.00085,
    beta_end=0.012,
    beta_schedule="scaled_linear",
    clip_sample=False,
    set_alpha_to_one=False,
    steps_offset=1,
)

vae = AutoencoderKL.from_pretrained(VAE_MODEL_PATH).to(dtype=torch.float16)
pipe = StableDiffusionPipeline.from_pretrained(
    BASE_MODEL_PATH,
    torch_dtype=torch.float16,
    scheduler=noise_scheduler,
    vae=vae,
    feature_extractor=None,
    safety_checker=None,
).to(DEVICE)


def generate_signature(name: str, image_bytes: io.BytesIO):
    buffer = io.BytesIO(image_bytes)
    buffer.seek(0)
    image = Image.open(buffer).convert("RGB").resize((512, 512))
    ip_model = IPAdapter(pipe, IMAGE_ENCODER_PATH, IP_CKPT, DEVICE)
    prompt = (
        f"handwritten a name {name}, centered, isolated on clean white paper"
    )
    negative_prompt = "no pen, no stamp, no logo, no frame, no desk, \
        no table, no object, no decoration, no brush, no background texture, \
        no border, no pattern, no watermark"

    images = ip_model.generate(
        pil_image=image,
        num_samples=1,
        num_inference_steps=40,
        prompt=prompt,
        negative_prompt=negative_prompt,
        scale=0.55,
    )

    result_image = images[0]
    output_buffer = io.BytesIO()
    result_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    return output_buffer
