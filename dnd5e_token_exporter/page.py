from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Optional, Self, NamedTuple, Generator

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


_SlotCoordinates = NamedTuple("Slotcoordinates", [("row", int), ("column", int)])
PixelCoordinates = NamedTuple("Pixel", [("row", int), ("column", int)])


class SlotCoordinates(_SlotCoordinates):

    def to_pixel_coordinates(self) -> PixelCoordinates:
        """Convert a SlotCoordinates into x/y coordinates expressed in pixels."""
        start_x, start_y = int(1.5 * MARGIN_SIZE_PX), int(1.5 * MARGIN_SIZE_PX)
        slot_start_x = start_x + (TOKEN_SIZE_PX * self.column)
        slot_start_y = start_y + (TOKEN_SIZE_PX * self.row)
        return PixelCoordinates(slot_start_x, slot_start_y)


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
    """A PageGrid represents a grid of squares over a page of a given format.

    Each square is of the size of the smallest token. For example, a tiny, small or
    medium token all fit on a single square (due to how 5e.tools handle the image
    size). A token of a large creature fits on 2x2 squares, etc.

    This allows us to implement a rudimentary (yet effective) bin-packing algorithm
    of tokens in the grid, thus using each page as much as possible, to minimize
    printing costs.

    """

    def __init__(self, page_format: PageFormat):
        self.page_format = page_format
        self.grid = [
            [False for _ in range(self.page_format.tokens_per_line)]
            for __ in range(self.page_format.tokens_per_column)
        ]

    def __iter__(self) -> Generator[SlotCoordinates, None, None]:
        """Iterate over each square in the grid"""
        for row_idx in range(self.page_format.tokens_per_column):
            for col_idx in range(self.page_format.tokens_per_line):
                yield SlotCoordinates(row_idx, col_idx)

    def size_in_slots(self, size_h: int, size_w: int) -> tuple[int, int]:
        """Returns the number of slots taken by a token dimension, in each direction"""
        width_size_in_slots = int(size_w / BASE_TOKEN_SIZE)
        height_size_in_slots = int(size_h / BASE_TOKEN_SIZE)
        return (width_size_in_slots, height_size_in_slots)

    def next_available_slot(self, size_w: int, size_h: int) -> Optional[SlotCoordinates]:
        """Find the next available top-right slot for a free square of the size of the image.

        Note: this scans the entire grid whenever it its called, which is only fine
        due the small amount of tokens and grid slots. We could optimize this method
        by not re-scanning used slots from the get go and keeping track of all available
        top-right empty slots we've already encountered.

        """
        width_size_in_slots, height_size_in_slots = self.size_in_slots(size_w, size_h)
        for slot in self:
            if (
                self.grid[slot.row][slot.column] is False
                and len(self.grid[slot.row]) >= slot.column + width_size_in_slots
                and len(self.grid) >= slot.row + height_size_in_slots
            ):
                return slot
        return None

    def fill_square_slots(self, slot: SlotCoordinates, image: Image.Image):
        """Mark each slot in the square fitting the argument image as filled."""
        width_size_in_slots, height_size_in_slots = self.size_in_slots(*image.size)
        for i in range(width_size_in_slots):
            for j in range(height_size_in_slots):
                self.grid[slot.row + i][slot.column + j] = True

    def add_legend(
        self,
        draw: ImageDraw.ImageDraw,
        token: Token,
        image: Image.Image,
        pixel_coordinates: PixelCoordinates,
    ):
        """Add the token name underneath the token"""
        text_coordinates = (
            pixel_coordinates.row + int(image.size[0] / 3),
            pixel_coordinates.column + image.size[1] + FONT_SIZE / 2,
        )
        draw.text(text_coordinates, token.name, (0, 0, 0), font=FONT)


@dataclass
class Page:
    image: Image.Image
    draw: ImageDraw.ImageDraw
    grid: PageGrid
    page_format: PageFormat

    @classmethod
    def of_format(cls, page_format: PageFormat) -> Self:
        """Create a new Page with attribute page format"""
        # Create a new image with white background
        page_img = Image.new("RGB", (page_format.width_px, page_format.height_px), "white")
        draw = ImageDraw.Draw(page_img)
        grid = PageGrid(page_format)
        return cls(image=page_img, draw=draw, grid=grid, page_format=page_format)

    def binpack_images(
        self, images: list[tuple[Token, Image.Image]], show_names: bool
    ) -> list[tuple[Token, Image.Image]]:
        """Binpack as many token images in the page as possible.

        If the page is full, return a list of remaining tokens to add to a new page.

        """
        remaining_images = []
        for i, (token, image) in enumerate(images):
            if slot := self.grid.next_available_slot(*image.size):
                self.grid.fill_square_slots(slot, image=image)
                pixel_coordinates = slot.to_pixel_coordinates()
                self.image.paste(image, pixel_coordinates)
                if show_names:
                    self.grid.add_legend(self.draw, token, image, pixel_coordinates)
            else:
                remaining_images = images[i:]
                break
        return remaining_images


def generate_token_multipage_pdf(
    tokens: list[Token],
    output_filename: Path,
    page_format: PageFormat = PageFormat.A4,
    show_names: bool = False,
):
    """Produce a multipage PDF with the token images organized in a way that minimizes whitespace"""
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
    pages[0].image.save(output_filename, dpi=(DPI, DPI), save_all=True, append_images=extra_images)
