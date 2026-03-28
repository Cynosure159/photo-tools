from __future__ import annotations

from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"
SOURCE_IMAGE = ICONS_DIR / "app-icon-source.png"
PNG_ICON = ICONS_DIR / "app-icon.png"
ICO_ICON = ICONS_DIR / "app-icon.ico"
ICNS_ICON = ICONS_DIR / "app-icon.icns"
OUTPUT_SIZE = 1024


def build_icon_image(source_image: Image.Image) -> Image.Image:
    rgba_image = source_image.convert("RGBA")
    return rgba_image.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)


def generate_png_icon(icon_image: Image.Image) -> None:
    icon_image.save(PNG_ICON)


def generate_ico_icon(icon_image: Image.Image) -> None:
    icon_image.save(
        ICO_ICON,
        format="ICO",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )


def generate_icns_icon(icon_image: Image.Image) -> None:
    icon_image.save(ICNS_ICON)


def main() -> int:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for path in (PNG_ICON, ICO_ICON, ICNS_ICON):
        if path.exists():
            path.unlink()

    source_image = Image.open(SOURCE_IMAGE)
    icon_image = build_icon_image(source_image)
    generate_png_icon(icon_image)
    generate_ico_icon(icon_image)
    generate_icns_icon(icon_image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
