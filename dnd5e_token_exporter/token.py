import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image

TOKEN_URL_TPL = "https://5e.tools/img/bestiary/tokens/{source}/{name}.webp"


@dataclass
class Token:
    source: str
    name: str
    local: bool

    def download_token_file(self) -> Path:
        if self.local:
            return Path(self.name)
        cached_file = Path(f"{tempfile.gettempdir()}/{self.source}_{self.name}.webp")
        if cached_file.exists():
            return cached_file
        token_url = TOKEN_URL_TPL.format(source=self.source, name=self.name)
        resp = requests.get(token_url, timeout=5)
        resp.raise_for_status()
        cached_file.write_bytes(resp.content)
        return cached_file

    def as_image(self) -> Image.Image:
        filename = self.download_token_file()
        rbga_img = Image.open(filename)
        img = Image.new("RGB", rbga_img.size, "white")
        img.paste(rbga_img, rbga_img)
        return img
