"""Validação do link e da pasta de destino, sem acesso à rede."""

import re
from pathlib import Path
from urllib.parse import urlsplit

ESQUEMAS_ACEITOS = {"http", "https"}
DOMINIO = re.compile(r"[\w-]+(\.[\w-]+)+")


class LinkInvalido(ValueError):
    """O texto recebido não pode ser usado como link de um vídeo."""


class PastaInvalida(ValueError):
    """O caminho recebido não pode ser usado como pasta de destino."""


def validar_link(link: str) -> str:
    """Devolve o link sem espaços nas pontas ou levanta LinkInvalido."""
    link = link.strip()

    if not link:
        raise LinkInvalido("O link está vazio.")

    # A checagem vem antes do urlsplit, que remove quebras de linha e
    # tabulações em silêncio e deixaria passar um link corrompido.
    if re.search(r"\s", link):
        raise LinkInvalido(f"O link não pode conter espaços: {link!r}")

    try:
        partes = urlsplit(link)
        partes.port  # Só é interpretada, e pode falhar, quando é lida.
    except ValueError as erro:
        raise LinkInvalido(f"O link está malformado: {link}") from erro

    if partes.scheme not in ESQUEMAS_ACEITOS:
        raise LinkInvalido(f"O link precisa começar com http:// ou https://: {link}")

    if not DOMINIO.fullmatch(partes.hostname or ""):
        raise LinkInvalido(f"O link não tem um domínio válido: {link}")

    return link


def preparar_pasta(pasta: str) -> Path:
    """Cria a pasta, se preciso, e devolve o caminho absoluto, ou levanta PastaInvalida."""
    # Sem esta checagem, Path("") viraria a pasta atual em silêncio.
    if not pasta.strip():
        raise PastaInvalida("A pasta de destino está vazia.")

    try:
        caminho = Path(pasta).expanduser().resolve()
        caminho.mkdir(parents=True, exist_ok=True)
    # Quando o arquivo está no meio do caminho, o Windows levanta FileExistsError
    # e o Linux, NotADirectoryError.
    except (FileExistsError, NotADirectoryError) as erro:
        raise PastaInvalida(
            f"O caminho tem um arquivo onde deveria haver uma pasta: {pasta}"
        ) from erro
    # O expanduser levanta RuntimeError quando não encontra o usuário de "~nome".
    except (OSError, RuntimeError) as erro:
        raise PastaInvalida(f"Não foi possível usar a pasta {pasta}: {erro}") from erro

    return caminho
