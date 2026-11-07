import pytest

from baixador.erros import traduzir_erro


@pytest.mark.parametrize(
    ("linha", "esperado"),
    [
        (
            "ERROR: [generic] x: Unable to download webpage: HTTPSConnection("
            "host='a.invalid', port=443): Failed to resolve 'a.invalid' "
            "([Errno 11001] getaddrinfo failed)",
            "Verifique a internet",
        ),
        ("ERROR: [youtube] abc: This video is unavailable", "não está disponível"),
        (
            "ERROR: [generic] x: Unable to download webpage: HTTP Error 404: Not Found "
            "(caused by <HTTPError 404: Not Found>)",
            "não está disponível",
        ),
        ("ERROR: Unsupported URL: https://www.example.com/", "não é suportado"),
        (
            "ERROR: [youtube] abc: Requested format is not available. "
            "Use --list-formats for a list of available formats",
            "formato pedido",
        ),
        ("ERROR: [youtube] abc: Private video", "acesso a este vídeo foi negado"),
        ("ERROR: [youtube] abc: Sign in to confirm your age", "acesso a este vídeo"),
        ("ERROR: [x] abc: HTTP Error 401: Unauthorized", "acesso a este vídeo"),
        # Saída real em um vídeo público: não pode sugerir que ele seja privado.
        ("ERROR: unable to download video data: HTTP Error 403: Forbidden", "erro 403"),
        ("ERROR: [x] abc: This video is DRM protected", "DRM"),
        ("ERROR: unable to write data: [Errno 28] No space left on device", "espaço"),
        ("ERROR: unable to open: [Errno 13] Permission denied: 'a.mp4'", "permissão"),
        ("ERROR: unable to open: [WinError 5] Acesso negado", "permissão"),
        ("ERROR: [x] abc: HTTP Error 429: Too Many Requests", "excesso de acessos"),
        # Contém "Unavailable", mas o problema é do servidor, não do vídeo.
        ("ERROR: [x] abc: HTTP Error 503: Service Unavailable", "com problemas"),
        ("ERROR: [x] abc: HTTP Error 500: Internal Server Error", "com problemas"),
        ("ERROR: [x] abc: The read operation timed out", "Verifique a internet"),
    ],
)
def test_traduz_os_erros_conhecidos(linha, esperado):
    assert esperado in traduzir_erro(linha)


def test_erro_desconhecido_mantem_o_texto_original():
    linha = "ERROR: [youtube:tab] PL1: Unable to download API page: HTTP Error 400"

    assert traduzir_erro(linha) == (
        "O yt-dlp falhou: [youtube:tab] PL1: Unable to download API page: HTTP Error 400"
    )
