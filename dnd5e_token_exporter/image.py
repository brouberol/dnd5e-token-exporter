import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Optional

import requests
from PIL import Image
from PIL.WebPImagePlugin import WebPImageFile

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
BASE_TOKEN_SIZE = 280  # medium creatures take 280px

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
        return int(self.width_mm / TOKEN_SIZE_MM)

    @property
    def tokens_per_column(self) -> int:
        return int(self.height_mm / TOKEN_SIZE_MM)


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


class PageGrid:
    def __init__(self, page_format: PageFormat):
        self.page_format = page_format
        self.grid = [
            [False for _ in range(self.page_format.tokens_per_line)]
            for __ in range(self.page_format.tokens_per_column)
        ]

    def size_factor(self, size_h: int, size_w: int) -> tuple[int, int]:
        width_size_factor = int(size_w / BASE_TOKEN_SIZE)
        height_size_factor = int(size_h / BASE_TOKEN_SIZE)
        return (width_size_factor, height_size_factor)

    def next_available_slot(
        self, size_w: int, size_h: int
    ) -> Optional[tuple[int, int]]:
        width_size_factor, height_size_factor = self.size_factor(size_w, size_h)
        for row_idx in range(len(self.grid)):
            for col_idx in range(len(self.grid[row_idx])):
                if (
                    self.grid[row_idx][col_idx] is False
                    and len(self.grid[row_idx]) >= col_idx + width_size_factor
                    and len(self.grid) >= row_idx + height_size_factor
                ):
                    return (row_idx, col_idx)
        raise ValueError("The page is filled!")

    def fill_slot(self, row_idx: int, col_idx: int, image: WebPImageFile):
        width_size_factor, height_size_factor = self.size_factor(*image.size)
        for i in range(width_size_factor):
            for j in range(height_size_factor):
                self.grid[row_idx + i][col_idx + j] = True

    def slot_coordinates(self, row_idx: int, col_idx: int) -> tuple[int, int]:
        start_x, start_y = int(1.5 * MARGIN_SIZE_PX), int(1.5 * MARGIN_SIZE_PX)
        slot_start_x = start_x + (TOKEN_SIZE_PX * col_idx)
        slot_start_y = start_y + (TOKEN_SIZE_PX * row_idx)
        return (slot_start_x, slot_start_y)


def generate_token_page(
    tokens: list[Token], output_filename: Path, page_format: PageFormat = PageFormat.A4
):
    # Create a new image with white background
    page_img = Image.new("RGBA", (page_format.width_px, page_format.height_px), "white")
    grid = PageGrid(page_format)
    images = [token.as_image() for token in tokens]
    images = sorted(
        images, key=lambda img: img.size, reverse=True
    )  # insert large tokens first, for efficient bin-packing

    for image in images:
        if slot := grid.next_available_slot(*image.size):
            grid.fill_slot(*slot, image=image)
            slot_coords = grid.slot_coordinates(*slot)
            page_img.paste(image, slot_coords)

    print(f"Generating {output_filename}")
    page_img.save(output_filename)
