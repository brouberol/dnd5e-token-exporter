from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Optional, Self, NamedTuple

from PIL import Image, ImageDraw, ImageFont

from .token import Token

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
BASE_TOKEN_SIZE = 280  # medium (and smaller) creatures have a 280x280px size
FONT_SIZE = 10
FONT = ImageFont.truetype("Monaco.ttf", FONT_SIZE)


SlotCoords = NamedTuple("SlotCoords", [("row", int), ("column", int)])


class PageFormat(StrEnum):
    A4 = "A4"
    A3 = "A3"

    @property
    def width_mm(self) -> int:
        if self.value == "A4":
            return A4_WIDTH_MM
        elif self.value == "A3":
            return A3_WIDTH_MM
        raise NotImplementedError(f"Dimension {self.value} is not supported")

    @property
    def height_mm(self) -> int:
        if self.value == "A4":
            return A4_HEIGHT_MM
        elif self.value == "A3":
            return A3_HEIGHT_MM
        raise NotImplementedError(f"Dimension {self.value} is not supported")

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
        # Note: this scans the entire grid whenever it its called, which is only fine
        # due the small amount of tokens and grid slots. We could optimize this method
        # by not re-scanning used slots from the get go and keeping track of all available
        # top-right empty slots we've alreadyt encountered.
        for row_idx in range(len(self.grid)):
            for col_idx in range(len(self.grid[row_idx])):
                if (
                    self.grid[row_idx][col_idx] is False
                    and len(self.grid[row_idx]) >= col_idx + width_size_factor
                    and len(self.grid) >= row_idx + height_size_factor
                ):
                    return (row_idx, col_idx)
        return None

    def fill_slot(self, row_idx: int, col_idx: int, image: Image.Image):
        width_size_factor, height_size_factor = self.size_factor(*image.size)
        for i in range(width_size_factor):
            for j in range(height_size_factor):
                self.grid[row_idx + i][col_idx + j] = True

    def slot_coordinates(self, row_idx: int, col_idx: int) -> SlotCoords:
        start_x, start_y = int(1.5 * MARGIN_SIZE_PX), int(1.5 * MARGIN_SIZE_PX)
        slot_start_x = start_x + (TOKEN_SIZE_PX * col_idx)
        slot_start_y = start_y + (TOKEN_SIZE_PX * row_idx)
        return SlotCoords(slot_start_x, slot_start_y)

    def add_legend(
        self,
        draw: ImageDraw.ImageDraw,
        token: Token,
        image: Image.Image,
        slot_coords: SlotCoords,
    ):
        text_coords = (
            slot_coords.row + int(image.size[0] / 3),
            slot_coords.column + image.size[1] + FONT_SIZE / 2,
        )
        draw.text(text_coords, token.name, (0, 0, 0), font=FONT)


@dataclass
class Page:
    image: Image.Image
    draw: ImageDraw.ImageDraw
    grid: PageGrid
    page_format: PageFormat

    @classmethod
    def of_format(cls, page_format: PageFormat) -> Self:
        page_img = Image.new(
            "RGB", (page_format.width_px, page_format.height_px), "white"
        )
        draw = ImageDraw.Draw(page_img)
        grid = PageGrid(page_format)
        return cls(image=page_img, draw=draw, grid=grid, page_format=page_format)

    def binpack_images(
        self, images: list[tuple[Token, Image.Image]], show_names: bool
    ) -> list[tuple[Token, Image.Image]]:
        """Add as many token images in the page as possible.

        If the page is full, return a list of remaining tokens to add to a new page.

        """
        remaining_images = []
        for i, (token, image) in enumerate(images):
            if slot := self.grid.next_available_slot(*image.size):
                self.grid.fill_slot(*slot, image=image)
                slot_coords = self.grid.slot_coordinates(*slot)
                self.image.paste(image, slot_coords)
                if show_names:
                    self.grid.add_legend(self.draw, token, image, slot_coords)
            else:
                remaining_images = images[i:]
                break
        return remaining_images


def generate_token_page(
    tokens: list[Token],
    output_filename: Path,
    page_format: PageFormat = PageFormat.A4,
    show_names: bool = False,
):
    # Create a new image with white background
    pages: list[Page] = []
    images = [(token, token.as_image()) for token in tokens]
    remaining_images = sorted(
        images, key=lambda t: t[1].size, reverse=True
    )  # insert large tokens first, for efficient bin-packing

    while remaining_images:
        page = Page.of_format(page_format)
        remaining_images = page.binpack_images(remaining_images, show_names)
        pages.append(page)

    print(f"Generating {output_filename}")
    extra_images = [page.image for page in pages[1:] if len(pages) > 1] or []
    pages[0].image.save(
        output_filename, dpi=(DPI, DPI), save_all=True, append_images=extra_images
    )
