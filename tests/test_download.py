import subprocess

import pytest

from baixador import download
from baixador.download import FORMATOS, FalhaNoDownload, baixar, montar_comando

LINK = "https://exemplo.com/video"


@pytest.fixture
def programas_instalados(monkeypatch):
    monkeypatch.setattr(download.shutil, "which", lambda programa: programa)


def simular_execucao(monkeypatch, codigo_de_saida):
    """Troca o subprocess.run por um dublê e devolve os comandos recebidos."""
    chamadas = []

    def executar(comando):
        chamadas.append(comando)
        return subprocess.CompletedProcess(comando, codigo_de_saida)

    monkeypatch.setattr(download.subprocess, "run", executar)
    return chamadas


def test_comando_usa_mp4_por_padrao():
    comando = montar_comando(LINK)

    assert comando[0] == "yt-dlp"
    assert comando[comando.index("--preset-alias") + 1] == "mp4"


def test_comando_mp3_usa_o_preset_de_audio():
    comando = montar_comando(LINK, "mp3")

    assert comando[comando.index("--preset-alias") + 1] == "mp3"


def test_comando_wav_extrai_o_audio_e_converte():
    comando = montar_comando(LINK, "wav")

    assert "--extract-audio" in comando
    assert comando[comando.index("--audio-format") + 1] == "wav"


@pytest.mark.parametrize("formato", FORMATOS)
def test_comando_baixa_um_unico_item(formato):
    comando = montar_comando(LINK, formato)

    assert "--no-playlist" in comando
    assert comando[comando.index("--playlist-items") + 1] == "1"


@pytest.mark.parametrize("formato", FORMATOS)
def test_link_vem_depois_do_separador_de_opcoes(formato):
    assert montar_comando(LINK, formato)[-2:] == ["--", LINK]


@pytest.mark.usefixtures("programas_instalados")
@pytest.mark.parametrize("formato", FORMATOS)
def test_baixar_executa_o_comando_do_formato(monkeypatch, formato):
    chamadas = simular_execucao(monkeypatch, codigo_de_saida=0)

    baixar(LINK, formato)

    assert chamadas == [montar_comando(LINK, formato)]


@pytest.mark.usefixtures("programas_instalados")
def test_codigo_de_saida_diferente_de_zero_vira_falha(monkeypatch):
    simular_execucao(monkeypatch, codigo_de_saida=1)

    with pytest.raises(FalhaNoDownload, match="código 1"):
        baixar(LINK)


@pytest.mark.parametrize("ausente", ["yt-dlp", "ffmpeg", "ffprobe"])
def test_programa_ausente_vira_falha_sem_executar_nada(monkeypatch, ausente):
    monkeypatch.setattr(
        download.shutil,
        "which",
        lambda programa: None if programa == ausente else programa,
    )
    chamadas = simular_execucao(monkeypatch, codigo_de_saida=0)

    with pytest.raises(FalhaNoDownload, match=ausente):
        baixar(LINK)

    assert chamadas == []
