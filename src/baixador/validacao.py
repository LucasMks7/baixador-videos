"""Validação dos links recebidos, sem acesso à rede."""

import re
from urllib.parse import urlsplit

ESQUEMAS_ACEITOS = {"http", "https"}
DOMINIO = re.compile(r"[\w-]+(\.[\w-]+)+")


class LinkInvalido(ValueError):
    """O texto recebido não pode ser usado como link de um vídeo."""


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
