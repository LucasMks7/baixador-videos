import pytest

from baixador import __version__
from baixador.cli import main


def test_version_mostra_a_versao_do_pacote(capsys):
    with pytest.raises(SystemExit) as saida:
        main(["--version"])

    assert saida.value.code == 0
    assert capsys.readouterr().out.strip() == f"baixar {__version__}"


def test_sem_argumentos_termina_sem_erro():
    assert main([]) == 0
