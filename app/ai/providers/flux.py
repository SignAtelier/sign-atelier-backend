import io
import logging
import os
from time import perf_counter

from app.ai.providers.base import SignGenerationProvider
from app.models.sign_style import SignatureStyle


logger = logging.getLogger(__name__)


STYLE_PROMPTS = {
    "luxury": (
        "luxury premium autograph, elegant long sweeping cursive strokes, "
        "ornamental flourishes, refined high-end personal signature"
    ),
    "calligraphy": (
        "extravagant abstract personal autograph mark, almost unreadable, "
        "prioritizing dramatic decorative beauty over legibility, "
        "thin elegant ink lines with very elaborate calligraphic motion, "
        "letters should merge into one artistic monogram-like flow, "
        "large sweeping curves, high-energy curves, and an integrated long tail flourish, "
        "all decoration must flow from the main signature stroke as one continuous movement, "
        "avoid clearly spelling the name, avoid readable calligraphy text, "
        "no detached decorative lines, no random accent marks, no messy scribbles, "
        "no thick or heavy strokes"
    ),
    "simple": (
        "simple clean autograph, minimal readable handwriting, few strokes, "
        "modest connected linework, easy to practice, no decorative flourish"
    ),
    "sharp": (
        "sharp angular autograph, the first letter has clearly pointed corners and angular edges, "
        "crisp geometric initial, high contrast modern strokes, controlled aggressive shape"
    ),
}


def build_flux_signature_prompt(
    name: str, style: SignatureStyle = SignatureStyle.LUXURY
) -> str:
    style_prompt = STYLE_PROMPTS[style.value]
    return (
        f'{style_prompt} for the name "{name}". '
        "Black ink only, handwritten personal signature design, "
        "smooth connected motion, stylish but realistic autograph. "
        "The visual style must strongly match the style description. "
        "clean pure white background, no paper texture, no logo, no extra words, "
        "no typed font, no printed letters."
    )


class FluxLocalProvider(SignGenerationProvider):
    name = "flux_local"

    def __init__(self):
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
        self.pipe = self._load_pipeline()

    def _torch_dtype(self):
        import torch

        if self.dtype == "float16":
            return torch.float16
        if self.dtype == "float32":
            return torch.float32
        return torch.bfloat16

    def _load_pipeline(self):
        from diffusers import Flux2KleinPipeline

        logger.info(
            "Loading FLUX signature provider. model_id=%s", self.model_id
        )
        pipe = Flux2KleinPipeline.from_pretrained(
            self.model_id,
            torch_dtype=self._torch_dtype(),
        )

        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.device)

        logger.info("FLUX signature provider loaded. model_id=%s", self.model_id)
        return pipe

    def generate(
        self,
        name: str,
        style: SignatureStyle = SignatureStyle.LUXURY,
        seed: int | None = None,
    ) -> io.BytesIO:
        import torch

        prompt = build_flux_signature_prompt(name, style)
        actual_seed = (
            seed if seed is not None else int.from_bytes(os.urandom(4), "big")
        )
        generator = torch.Generator(device=self.device).manual_seed(
            actual_seed
        )
        started_at = perf_counter()

        logger.info(
            "flux.generate.start style=%s seed=%s width=%s height=%s steps=%s",
            style,
            actual_seed,
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
            actual_seed,
            perf_counter() - started_at,
        )
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        logger.info(
            "flux.generate.done style=%s seed=%s bytes=%s elapsed=%.2fs",
            style,
            actual_seed,
            output_buffer.getbuffer().nbytes,
            perf_counter() - started_at,
        )
        return output_buffer
