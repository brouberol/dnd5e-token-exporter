import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self, Optional

from .page import PageFormat, Token, generate_token_multipage_pdf


@dataclass
class CliToken:
    name: str
    times: int
    local: bool
    source: Optional[str]

    @classmethod
    def from_str(cls, s: str) -> Self:
        # Parse token repetitions
        if ":" in s:
            token, times_str = s.split(":")
            times = int(times_str)
        else:
            token, times = s, 1

        # Parse token source
        if token.count("/") == 1:
            source, name = token.split("/")
        else:
            source, name = "MM", token  # Assume Monster Manual by default

        # Set source to None for local tokens
        if local := Path(token).exists():
            source = None

        return cls(name=name, times=times, local=local, source=source)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export dnd5e tokens ready for print",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--tokens",
        nargs="+",
        help=(
            "Tokens to export. [<book>]/<creature>[:<times>] or <local-path>[:<times>] "
            "If book is unspecified, MM is assumed."
            "Example: MM/Goblin:6 Slaad ~/Documents/token.png:2 'PaBTSO/Mind Flayer Prophet'"
        ),
        type=CliToken.from_str,
        required=True,
    )
    parser.add_argument(
        "--format",
        help="Page format",
        type=PageFormat,
        default=PageFormat.A4,
        choices=list(PageFormat._value2member_map_.keys()),
    )
    parser.add_argument(
        "-o",
        "--output",
        help="The name of the generated tokens file",
        type=Path,
        default="tokens.pdf",
    )
    parser.add_argument(
        "--show-names",
        help="When specified, display the monsters name beneath their tokens",
        action="store_true",
    )
    return parser.parse_args()


def resolve_tokens_repetitions(tokens: list[CliToken]) -> list[Token]:
    out = []
    for token in tokens:
        out.extend([Token(name=token.name, local=token.local, source=token.source)] * token.times)
    return out


def main():
    args = parse_args()
    tokens = resolve_tokens_repetitions(args.tokens)
    generate_token_multipage_pdf(
        tokens=tokens,
        output_filename=args.output,
        page_format=args.format,
        show_names=args.show_names,
    )
