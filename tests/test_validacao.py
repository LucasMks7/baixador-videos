from pathlib import Path

import pytest

from baixador.validacao import (
    LinkInvalido,
    PastaInvalida,
    preparar_pasta,
    validar_link,
)


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


def test_pasta_existente_e_mantida_com_o_conteudo(tmp_path):
    arquivo = tmp_path / "antigo.txt"
    arquivo.touch()

    assert preparar_pasta(str(tmp_path)) == tmp_path.resolve()
    assert arquivo.exists()


def test_cria_pasta_com_as_intermediarias(tmp_path):
    destino = tmp_path / "a" / "b"

    assert preparar_pasta(str(destino)) == destino.resolve()
    assert destino.is_dir()


def test_caminho_relativo_vira_absoluto(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert preparar_pasta("nova") == (tmp_path / "nova").resolve()


def test_til_vira_a_pasta_do_usuario(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    assert preparar_pasta("~/nova") == (tmp_path / "nova").resolve()


@pytest.mark.parametrize("pasta", ["", "   "])
def test_recusa_pasta_vazia(pasta):
    with pytest.raises(PastaInvalida, match="vazia"):
        preparar_pasta(pasta)


def test_recusa_caminho_que_e_um_arquivo(tmp_path):
    arquivo = tmp_path / "arquivo.txt"
    arquivo.touch()

    with pytest.raises(PastaInvalida, match="onde deveria haver uma pasta"):
        preparar_pasta(str(arquivo))


def test_recusa_pasta_dentro_de_um_arquivo(tmp_path):
    arquivo = tmp_path / "arquivo.txt"
    arquivo.touch()

    with pytest.raises(PastaInvalida, match="onde deveria haver uma pasta"):
        preparar_pasta(str(arquivo / "sub"))


def test_falta_de_permissao_vira_pasta_invalida(tmp_path, monkeypatch):
    def negar(*args, **kwargs):
        raise PermissionError("acesso negado")

    monkeypatch.setattr(Path, "mkdir", negar)

    with pytest.raises(PastaInvalida, match="acesso negado"):
        preparar_pasta(str(tmp_path / "nova"))


def test_erro_do_sistema_mostra_so_o_motivo(tmp_path, monkeypatch):
    def falhar(*args, **kwargs):
        raise OSError(3, "Caminho não encontrado", "Q:\\")

    monkeypatch.setattr(Path, "mkdir", falhar)

    with pytest.raises(PastaInvalida) as erro:
        preparar_pasta(str(tmp_path / "nova"))

    assert str(erro.value).endswith("Caminho não encontrado.")


def test_aspa_no_caminho_ganha_dica_sobre_a_barra_final(tmp_path, monkeypatch):
    def falhar(*args, **kwargs):
        raise OSError(22, "Nome inválido")

    monkeypatch.setattr(Path, "mkdir", falhar)

    with pytest.raises(PastaInvalida, match="não o termine com"):
        preparar_pasta(str(tmp_path / 'Minha Pasta"'))
