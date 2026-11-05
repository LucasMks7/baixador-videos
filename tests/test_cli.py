import os
import subprocess
import sys

import pytest

from baixador import __version__, cli
from baixador.cli import main
from baixador.download import FalhaNoDownload


def test_version_mostra_a_versao_do_pacote(capsys):
    with pytest.raises(SystemExit) as saida:
        main(["--version"])

    assert saida.value.code == 0
    assert capsys.readouterr().out.strip() == f"baixar {__version__}"


def test_sem_link_termina_com_erro_de_uso(capsys):
    with pytest.raises(SystemExit) as saida:
        main([])

    assert saida.value.code == 2
    assert "link" in capsys.readouterr().err


def test_link_valido_baixa_o_video_e_termina_sem_erro(capsys, monkeypatch):
    baixados = []
    monkeypatch.setattr(cli, "baixar_mp4", baixados.append)

    assert main(["  https://exemplo.com/video\n"]) == 0

    capturado = capsys.readouterr()
    assert baixados == ["https://exemplo.com/video"]
    assert "concluído" in capturado.out
    assert capturado.err == ""


def test_link_invalido_mostra_erro_e_nao_tenta_baixar(capsys, monkeypatch):
    baixados = []
    monkeypatch.setattr(cli, "baixar_mp4", baixados.append)

    assert main(["exemplo.com/video"]) == 2

    capturado = capsys.readouterr()
    assert baixados == []
    assert capturado.err.startswith("baixar: erro: ")
    assert "http:// ou https://" in capturado.err
    assert capturado.out == ""


def test_falha_no_download_mostra_erro_e_termina_com_codigo_1(capsys, monkeypatch):
    def falhar(link):
        raise FalhaNoDownload("O yt-dlp terminou com o código 1.")

    monkeypatch.setattr(cli, "baixar_mp4", falhar)

    assert main(["https://exemplo.com/video"]) == 1

    capturado = capsys.readouterr()
    assert capturado.err == "baixar: erro: O yt-dlp terminou com o código 1.\n"
    assert capturado.out == ""


def test_saida_redirecionada_usa_utf8():
    ambiente = {**os.environ, "PYTHONUTF8": "0"}
    ambiente.pop("PYTHONIOENCODING", None)

    resultado = subprocess.run(
        [sys.executable, "-c", "from baixador.cli import main; main(['--help'])"],
        capture_output=True,
        env=ambiente,
    )

    assert resultado.returncode == 0
    assert "Baixa vídeos".encode("utf-8") in resultado.stdout
