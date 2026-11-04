"""Interface de linha de comando."""

import argparse
from collections.abc import Sequence

from baixador import __version__


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="baixar",
        description="Baixa vídeos em MP4 ou extrai o áudio em MP3 ou WAV.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    criar_parser().parse_args(argv)
    return 0
