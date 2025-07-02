import torch
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-2-1", torch_dtype=torch.float16, revision="fp16"
)
pipe = pipe.to("cuda")

image = pipe(
    "Junoo signature, elegant calligraphy, black ink on white background",
    negative_prompt="",
    num_inference_steps=28,
    guidance_scale=7.0,
).images[0]

image.save("signature.png")
