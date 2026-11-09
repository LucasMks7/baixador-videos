"""Interface de linha de comando."""

import argparse
import re
import sys
from collections.abc import Sequence

from baixador import __version__
from baixador.download import (
    ETAPA_ATUALIZANDO,
    ETAPA_PROCESSANDO,
    FORMATO_PADRAO,
    FORMATOS,
    FORMATOS_COM_QUALIDADE,
    QUALIDADE_PADRAO,
    QUALIDADES,
    FalhaNoDownload,
    Progresso,
    baixar,
)
from baixador.validacao import (
    LinkInvalido,
    PastaInvalida,
    preparar_pasta,
    validar_link,
)

CODIGO_FALHA_NO_DOWNLOAD = 1
# Mesmo código que o argparse usa para erros de uso.
CODIGO_ENTRADA_INVALIDA = 2
# Convenção dos terminais para programa interrompido com Ctrl+C.
CODIGO_CANCELADO = 130

LARGURA_DA_LINHA = 70

# O argparse só escreve em inglês. Mensagens fora desta lista seguem como estão.
TRADUCOES_DO_ARGPARSE = (
    (r"the following arguments are required: (.+)", r"falta informar: \1"),
    (
        r"argument (.+): invalid choice: (.+) \(choose from (.+)\)",
        r"valor inválido para \1: \2. Opções: \3",
    ),
    (r"argument (.+): expected one argument", r"a opção \1 precisa de um valor"),
    (r"unrecognized arguments: (.+)", r"opção desconhecida: \1"),
)


class ParserEmPortugues(argparse.ArgumentParser):
    """Escreve os erros de uso no mesmo formato e idioma dos demais erros."""

    def error(self, message: str):
        for padrao, traducao in TRADUCOES_DO_ARGPARSE:
            message = re.sub(padrao, traducao, message)
        self.exit(
            CODIGO_ENTRADA_INVALIDA,
            f"{self.prog}: erro: {message}\nUse {self.prog} --help para ver as opções.\n",
        )


def usar_utf8_na_saida() -> None:
    """Mantém os acentos corretos quando a saída é redirecionada no Windows."""
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")


def formatar_progresso(progresso: Progresso) -> str:
    if progresso.etapa == ETAPA_PROCESSANDO:
        return "Processando o arquivo..."
    if progresso.etapa == ETAPA_ATUALIZANDO:
        return "O download falhou. Atualizando o yt-dlp para tentar de novo..."

    partes = ["Baixando"]
    if progresso.percentual is not None:
        partes[0] += f" {progresso.percentual:5.1f}%"
    if progresso.velocidade:
        partes.append(progresso.velocidade)
    if progresso.restante:
        partes.append(f"restam {progresso.restante}")
    return " | ".join(partes)


def mostrar_progresso(progresso: Progresso) -> None:
    """Reescreve a mesma linha do terminal; redirecionada, a saída fica sem progresso."""
    # Vai para o stderr para não misturar com o resultado, escrito no stdout.
    if sys.stderr.isatty():
        texto = formatar_progresso(progresso).ljust(LARGURA_DA_LINHA)
        print(f"\r{texto}", end="", file=sys.stderr, flush=True)


def limpar_progresso() -> None:
    if sys.stderr.isatty():
        print("\r" + " " * LARGURA_DA_LINHA + "\r", end="", file=sys.stderr, flush=True)


def criar_parser() -> argparse.ArgumentParser:
    parser = ParserEmPortugues(
        prog="baixar",
        description="Baixa um vídeo em MP4 ou extrai o áudio em MP3 ou WAV.",
    )
    parser.add_argument("link", help="link do vídeo, começando com http:// ou https://")
    parser.add_argument(
        "--formato",
        choices=FORMATOS,
        default=FORMATO_PADRAO,
        help="formato do arquivo final (padrão: %(default)s)",
    )
    parser.add_argument(
        "--qualidade",
        choices=QUALIDADES,
        default=QUALIDADE_PADRAO,
        help="resolução máxima do vídeo, apenas em MP4 (padrão: %(default)s)",
    )
    parser.add_argument(
        "--pasta",
        help="pasta de destino, criada se não existir (padrão: a pasta atual)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    usar_utf8_na_saida()
    parser = criar_parser()
    argumentos = parser.parse_args(argv)

    if (
        argumentos.qualidade != QUALIDADE_PADRAO
        and argumentos.formato not in FORMATOS_COM_QUALIDADE
    ):
        parser.error(f"--qualidade não se aplica ao formato {argumentos.formato}")

    try:
        link = validar_link(argumentos.link)
        # Vem depois do link, para um link errado não deixar uma pasta vazia para trás.
        pasta = None if argumentos.pasta is None else preparar_pasta(argumentos.pasta)
    except (LinkInvalido, PastaInvalida) as erro:
        print(f"baixar: erro: {erro}", file=sys.stderr)
        return CODIGO_ENTRADA_INVALIDA

    print("Preparando o download...", file=sys.stderr)
    try:
        arquivo = baixar(
            link,
            argumentos.formato,
            argumentos.qualidade,
            pasta,
            ao_progredir=mostrar_progresso,
        )
    except FalhaNoDownload as erro:
        limpar_progresso()
        print(f"baixar: erro: {erro}", file=sys.stderr)
        return CODIGO_FALHA_NO_DOWNLOAD
    except KeyboardInterrupt:
        limpar_progresso()
        print("Download cancelado.", file=sys.stderr)
        return CODIGO_CANCELADO

    limpar_progresso()
    print("Download concluído.")
    if arquivo is not None:
        print(f"Arquivo salvo em: {arquivo}")
    return 0
