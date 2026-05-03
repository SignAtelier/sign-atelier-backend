from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.ai.generate_sign import transform_signature_image


STYLES = ["luxury", "simple", "fast", "bold", "wide"]
THUMB_WIDTH = 480
THUMB_HEIGHT = 190
LABEL_HEIGHT = 34
OUT_PATH = Path("signature_transform_preview_sheet.png")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/preview_transform_signature.py <signature-image-path>")

    source_path = Path(sys.argv[1])
    image_bytes = source_path.read_bytes()
    thumbs = []

    for style in STYLES:
        buffer = transform_signature_image(image_bytes, style)
        image = Image.open(buffer).convert("RGB")
        image.thumbnail((THUMB_WIDTH, THUMB_HEIGHT - LABEL_HEIGHT))

        thumb = Image.new("RGB", (THUMB_WIDTH, THUMB_HEIGHT), "white")
        x = (THUMB_WIDTH - image.width) // 2
        y = LABEL_HEIGHT + (THUMB_HEIGHT - LABEL_HEIGHT - image.height) // 2
        thumb.paste(image, (x, y))

        draw = ImageDraw.Draw(thumb)
        draw.text((12, 10), style, fill=(0, 0, 0))
        thumbs.append(thumb)

    sheet = Image.new("RGB", (THUMB_WIDTH, THUMB_HEIGHT * len(STYLES)), "white")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, (0, index * THUMB_HEIGHT))

    sheet.save(OUT_PATH)
    print(OUT_PATH.resolve())


if __name__ == "__main__":
    main()
