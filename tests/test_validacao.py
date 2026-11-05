import pytest

from baixador.validacao import LinkInvalido, validar_link


@pytest.mark.parametrize(
    "link",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "http://exemplo.com.br/video.mp4",
        "HTTPS://EXEMPLO.COM/video",
        "https://exemplo.com:8080/video",
        "https://vídeos.exemplo.com/aula",
    ],
)
def test_aceita_links_validos(link):
    assert validar_link(link) == link


def test_remove_espacos_das_pontas():
    assert validar_link("  https://exemplo.com/video\n") == "https://exemplo.com/video"


@pytest.mark.parametrize("link", ["", "   ", "\n\t"])
def test_recusa_link_vazio(link):
    with pytest.raises(LinkInvalido, match="vazio"):
        validar_link(link)


@pytest.mark.parametrize(
    "link",
    [
        "https://exemplo.com/meu video",
        "https://exem\nplo.com/video",
        "https://exemplo.com/vi\tdeo",
    ],
)
def test_recusa_espacos_no_meio(link):
    with pytest.raises(LinkInvalido, match="espaços"):
        validar_link(link)


@pytest.mark.parametrize(
    "link",
    [
        "youtube.com/watch?v=abc",
        "https//exemplo.com/video",
        "ftp://exemplo.com/video.mp4",
        "file:///C:/Users/lucas/segredo.txt",
        "ytsearch:musica",
        "--exec=calc.exe",
    ],
)
def test_recusa_o_que_nao_comeca_com_http_ou_https(link):
    with pytest.raises(LinkInvalido, match="http:// ou https://"):
        validar_link(link)


@pytest.mark.parametrize(
    "link",
    [
        "https://",
        "http:/exemplo.com",
        "https://youtube",
        "https://.com",
        "https://exemplo.",
        "https://exem$plo.com",
    ],
)
def test_recusa_dominio_invalido(link):
    with pytest.raises(LinkInvalido, match="domínio"):
        validar_link(link)


@pytest.mark.parametrize(
    "link",
    [
        "https://[exemplo.com/video",
        "https://exemplo.com:porta/video",
    ],
)
def test_recusa_link_malformado(link):
    with pytest.raises(LinkInvalido, match="malformado"):
        validar_link(link)
