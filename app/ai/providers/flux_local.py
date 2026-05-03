import io
import logging
import os
from time import perf_counter

from app.ai.providers.base import SignGenerationProvider


logger = logging.getLogger(__name__)


STYLE_PROMPTS = {
    "luxury": "Luxury executive handwritten autograph signature",
    "executive": "Executive handwritten autograph signature",
    "minimal": "Minimal clean executive handwritten autograph signature",
    "simple": "Minimal clean executive handwritten autograph signature",
    "fast": "Fast celebrity-style handwritten autograph signature",
    "celebrity": "Fast celebrity-style handwritten autograph signature",
    "sharp": "Sharp angular premium handwritten autograph signature",
    "round": "Round cursive elegant handwritten autograph signature",
    "bold": "Bold confident handwritten autograph signature",
    "wide": "Wide flowing handwritten autograph signature",
}


def build_flux_signature_prompt(name: str, style: str = "luxury") -> str:
    style_key = style.lower().replace("_", "-")
    style_prompt = STYLE_PROMPTS.get(style_key, STYLE_PROMPTS["luxury"])
    return (
        f'{style_prompt} for the name "{name}". '
        "Elegant flowing black ink strokes, premium personal signature design, "
        "smooth connected motion, stylish but realistic autograph, "
        "clean pure white background, no paper texture, no logo, no extra words, "
        "no typed font, no printed letters."
    )


class FluxLocalProvider(SignGenerationProvider):
    name = "flux_local"

    def __init__(self):
        self.pipe = None
        self.model_id = os.getenv(
            "FLUX_MODEL_ID", "black-forest-labs/FLUX.2-klein-4B"
        )
        self.device = os.getenv("FLUX_DEVICE", "cuda")
        self.dtype = os.getenv("FLUX_DTYPE", "bfloat16")
        self.width = int(os.getenv("FLUX_WIDTH", "512"))
        self.height = int(os.getenv("FLUX_HEIGHT", "512"))
        self.steps = int(os.getenv("FLUX_STEPS", "4"))
        self.guidance_scale = float(os.getenv("FLUX_GUIDANCE_SCALE", "4.0"))
        self.cpu_offload = (
            os.getenv("FLUX_CPU_OFFLOAD", "true").lower() == "true"
        )

    def _torch_dtype(self):
        import torch

        if self.dtype == "float16":
            return torch.float16
        if self.dtype == "float32":
            return torch.float32
        return torch.bfloat16

    def _load(self):
        if self.pipe is not None:
            return

        from diffusers import Flux2KleinPipeline

        logger.info(
            "Loading FLUX signature provider. model_id=%s", self.model_id
        )
        self.pipe = Flux2KleinPipeline.from_pretrained(
            self.model_id,
            torch_dtype=self._torch_dtype(),
        )

        if self.cpu_offload:
            self.pipe.enable_model_cpu_offload()
        else:
            self.pipe.to(self.device)

    def generate(
        self, name: str, style: str = "luxury", seed: int | None = None
    ) -> io.BytesIO:
        import torch

        self._load()
        prompt = build_flux_signature_prompt(name, style)
        generator = torch.Generator(device=self.device).manual_seed(seed or 0)
        started_at = perf_counter()

        logger.info(
            "flux.generate.start style=%s seed=%s width=%s height=%s steps=%s",
            style,
            seed,
            self.width,
            self.height,
            self.steps,
        )

        image = self.pipe(
            prompt=prompt,
            height=self.height,
            width=self.width,
            guidance_scale=self.guidance_scale,
            num_inference_steps=self.steps,
            generator=generator,
        ).images[0]

        logger.info(
            "flux.generate.inference_done style=%s seed=%s elapsed=%.2fs",
            style,
            seed,
            perf_counter() - started_at,
        )
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        logger.info(
            "flux.generate.done style=%s seed=%s bytes=%s elapsed=%.2fs",
            style,
            seed,
            output_buffer.getbuffer().nbytes,
            perf_counter() - started_at,
        )
        return output_buffer
