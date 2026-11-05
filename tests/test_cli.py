import os
import subprocess
import sys

import pytest

from baixador import __version__
from baixador.cli import main


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


def test_link_valido_termina_sem_erro(capsys):
    assert main(["https://exemplo.com/video"]) == 0

    capturado = capsys.readouterr()
    assert "https://exemplo.com/video" in capturado.out
    assert capturado.err == ""


def test_link_invalido_mostra_erro_e_termina_com_codigo_2(capsys):
    assert main(["exemplo.com/video"]) == 2

    capturado = capsys.readouterr()
    assert capturado.err.startswith("baixar: erro: ")
    assert "http:// ou https://" in capturado.err
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
