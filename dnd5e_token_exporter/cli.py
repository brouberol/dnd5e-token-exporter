import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from .image import Token, generate_token_page


@dataclass
class CliToken:
    token: str
    times: int
    local: bool

    @classmethod
    def from_str(cls, s: str) -> Self:
        if ":" in s:
            token, times = s.split(":")
            times = int(times)
        else:
            token, times = s, 1
        local = Path(token).exists()
        return CliToken(token=token, times=times, local=local)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export dnd5e tokens ready to print")
    parser.add_argument(
        "--tokens",
        nargs="+",
        help=(
            "Tokens to export. <book>/<creature>[:<times>] or <local-path>[:<times>]"
            "Example: MM/Goblin:6 local-token.png:2"
        ),
        type=CliToken.from_str,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="The name of the generated tokens file",
        type=Path,
        default="tokens.pdf",
    )
    return parser.parse_args()


def resolve_tokens_repetitions(tokens: CliToken) -> list[str]:
    out = []
    for token in tokens:
        out.extend([Token(name=token.token, local=token.local)] * token.times)
    return out


def main():
    args = parse_args()
    generate_token_page(
        tokens=resolve_tokens_repetitions(args.tokens), output_filename=args.output
    )
