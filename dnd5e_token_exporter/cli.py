import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from .image import Token, generate_token_page


@dataclass
class CliToken:
    name: str
    times: int
    local: bool
    # If the source is unspecified, we assume that the monster comes from the Monster Manual
    source: str = field(default="MM")

    @classmethod
    def from_str(cls, s: str) -> Self:
        if ":" in s:
            token, times = s.split(":")
            times = int(times)
        else:
            token, times = s, 1
        if token.count("/") == 1:
            source, name = token.split("/")
            kwargs = {"name": name, "source": source}
        else:
            kwargs = {"name": token}
        local = Path(token).exists()
        return CliToken(times=times, local=local, **kwargs)


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
        out.extend(
            [Token(name=token.name, local=token.local, source=token.source)]
            * token.times
        )
    return out


def main():
    args = parse_args()
    generate_token_page(
        tokens=resolve_tokens_repetitions(args.tokens), output_filename=args.output
    )
