"""Interface de linha de comando."""

import argparse
import sys
from collections.abc import Sequence

from baixador import __version__
from baixador.download import FORMATO_PADRAO, FORMATOS, FalhaNoDownload, baixar
from baixador.validacao import LinkInvalido, validar_link

CODIGO_FALHA_NO_DOWNLOAD = 1
# Mesmo código que o argparse usa para erros de uso.
CODIGO_ENTRADA_INVALIDA = 2


def usar_utf8_na_saida() -> None:
    """Mantém os acentos corretos quando a saída é redirecionada no Windows."""
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="baixar",
        description="Baixa um vídeo em MP4 ou extrai o áudio em MP3 ou WAV, na pasta atual.",
    )
    parser.add_argument("link", help="link do vídeo, começando com http:// ou https://")
    parser.add_argument(
        "--formato",
        choices=FORMATOS,
        default=FORMATO_PADRAO,
        help="formato do arquivo final (padrão: %(default)s)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    usar_utf8_na_saida()
    argumentos = criar_parser().parse_args(argv)

    try:
        link = validar_link(argumentos.link)
    except LinkInvalido as erro:
        print(f"baixar: erro: {erro}", file=sys.stderr)
        return CODIGO_ENTRADA_INVALIDA

    try:
        baixar(link, argumentos.formato)
    except FalhaNoDownload as erro:
        print(f"baixar: erro: {erro}", file=sys.stderr)
        return CODIGO_FALHA_NO_DOWNLOAD

    print("Download concluído.")
    return 0
