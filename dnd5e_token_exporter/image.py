import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import requests
from PIL import Image

INCH_IN_MM = 25.4
DPI = 300


def mm_to_px(dim_mm: int) -> int:
    return int(dim_mm * DPI / INCH_IN_MM)


# A4 dimensions in millimeters
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
A3_WIDTH_MM = 297
A3_HEIGHT_MM = 420
TOKEN_SIZE_MM = 25
TOKEN_SIZE_PX = mm_to_px(TOKEN_SIZE_MM)
MARGIN_SIZE_MM = 4
MARGIN_SIZE_PX = mm_to_px(MARGIN_SIZE_MM)

TOKENS_PER_LINE = 7
TOKENS_PER_COLUMN = 10
TOKEN_URL_TPL = "https://5e.tools/img/bestiary/tokens/{source}/{name}.webp"


class PageFormat(StrEnum):
    A4 = "A4"
    A3 = "A3"

    @property
    def width_mm(self) -> int:
        if self.value == "A4":
            return A4_WIDTH_MM
        elif self.value == "A3":
            return A3_WIDTH_MM

    @property
    def height_mm(self) -> int:
        if self.value == "A4":
            return A4_HEIGHT_MM
        elif self.value == "A3":
            return A3_HEIGHT_MM

    @property
    def width_px(self):
        return mm_to_px(self.width_mm)

    @property
    def height_px(self):
        return mm_to_px(self.height_mm)

    @property
    def tokens_per_line(self) -> int:
        return int(self.width_mm / TOKEN_SIZE_MM * 0.85)

    @property
    def tokens_per_column(self) -> int:
        return int(self.height_mm / TOKEN_SIZE_MM * 0.85)


@dataclass
class Token:
    source: str
    name: str
    local: bool

    def download_token_file(self) -> Path:
        if self.local:
            return self.name
        cached_file = Path(f"{tempfile.gettempdir()}/{self.source}_{self.name}.webp")
        if cached_file.exists():
            return cached_file
        token_url = TOKEN_URL_TPL.format(source=self.source, name=self.name)
        resp = requests.get(token_url)
        resp.raise_for_status()
        cached_file.write_bytes(resp.content)
        return cached_file

    def as_image(self) -> Image:
        filename = self.download_token_file()
        return Image.open(filename)


def generate_token_page(
    tokens: list[Token], output_filename: Path, page_format: PageFormat = PageFormat.A4
):
    # Create a new image with white background
    page_img = Image.new("RGBA", (page_format.width_px, page_format.height_px), "white")
    images = [token.as_image() for token in tokens]

    start_x, start_y = int(1.5 * MARGIN_SIZE_PX), int(1.5 * MARGIN_SIZE_PX)
    for i in range(page_format.tokens_per_column):
        for j in range(page_format.tokens_per_line):
            index = i * page_format.tokens_per_line + j
            if index >= len(images):
                continue
            image = images[index].resize((TOKEN_SIZE_PX, TOKEN_SIZE_PX))
            coords = (
                start_x + (TOKEN_SIZE_PX + MARGIN_SIZE_PX) * j,
                start_y + (TOKEN_SIZE_PX + MARGIN_SIZE_PX) * i,
            )
            page_img.paste(image, coords)
    print(f"Generating {output_filename}")
    page_img.save(output_filename)
