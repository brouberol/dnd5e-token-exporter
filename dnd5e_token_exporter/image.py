import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image

INCH_IN_MM = 25.4
DPI = 300

# A4 dimensions in millimeters
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297

# Convert to pixels (assuming 300 DPI)
A4_WIDTH_PX = int(A4_WIDTH_MM * DPI / INCH_IN_MM)  # 25.4 mm/inch
A4_HEIGHT_PX = int(A4_HEIGHT_MM * DPI / INCH_IN_MM)

TOKENS_PER_LINE = 7
TOKENS_PER_COLUMN = 10
TOKEN_URL_TPL = "https://5e.tools/img/bestiary/tokens/{token_name}.webp"


@dataclass
class Token:
    name: str
    local: bool


def fetch_data(token: Token) -> Path:
    if token.local:
        return token.name
    cached_file = Path(f"{tempfile.gettempdir()}/{token.name.replace('/', '_')}.webp")
    if cached_file.exists():
        return cached_file
    token_url = TOKEN_URL_TPL.format(token_name=token.name)
    resp = requests.get(token_url)
    resp.raise_for_status()
    cached_file.write_bytes(resp.content)
    return cached_file


def download_token(token_name: str) -> Image:
    filename = fetch_data(token_name)
    return Image.open(filename)


def generate_token_page(tokens: list[Token], output_filename: Path):
    # Create a new image with white background
    page = Image.new("RGBA", (A4_WIDTH_PX, A4_HEIGHT_PX), "white")
    images = [download_token(token) for token in tokens]

    token_dimension = int(25 * DPI / INCH_IN_MM)
    margin_size = int(4 * DPI / INCH_IN_MM)

    start_x, start_y = int(1.5 * margin_size), int(1.5 * margin_size)
    for i in range(TOKENS_PER_COLUMN):
        for j in range(TOKENS_PER_LINE):
            index = i * TOKENS_PER_LINE + j
            if index >= len(images):
                continue
            image = images[index].resize((token_dimension, token_dimension))
            coords = (
                start_x + (token_dimension + margin_size) * j,
                start_y + (token_dimension + margin_size) * i,
            )
            page.paste(image, coords)
    print(f"Generating {output_filename}")
    page.save(output_filename)
