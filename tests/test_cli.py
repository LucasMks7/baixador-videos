import os
import subprocess
import sys

import pytest

from baixador import __version__, cli
from baixador.cli import main
from baixador.download import (
    ETAPA_ATUALIZANDO,
    ETAPA_BAIXANDO,
    ETAPA_PROCESSANDO,
    QUALIDADES,
    FalhaNoDownload,
    Progresso,
)


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


@pytest.fixture
def baixados(monkeypatch):
    """Troca o download por um dublê e devolve os pedidos recebidos."""
    pedidos = []

    def registrar(*pedido, **opcoes):
        pedidos.append(pedido)

    monkeypatch.setattr(cli, "baixar", registrar)
    return pedidos


def test_link_valido_baixa_com_os_padroes_e_termina_sem_erro(capsys, baixados):
    assert main(["  https://exemplo.com/video\n"]) == 0

    capturado = capsys.readouterr()
    assert baixados == [("https://exemplo.com/video", "mp4", "melhor", None)]
    assert "concluído" in capturado.out
    assert "erro" not in capturado.err


@pytest.mark.parametrize("formato", ["mp4", "mp3", "wav"])
def test_formato_escolhido_chega_ao_download(baixados, formato):
    assert main(["https://exemplo.com/video", "--formato", formato]) == 0

    assert baixados == [("https://exemplo.com/video", formato, "melhor", None)]


@pytest.mark.parametrize("qualidade", QUALIDADES)
def test_qualidade_escolhida_chega_ao_download(baixados, qualidade):
    assert main(["https://exemplo.com/video", "--qualidade", qualidade]) == 0

    assert baixados == [("https://exemplo.com/video", "mp4", qualidade, None)]


def test_qualidade_desconhecida_termina_com_erro_de_uso(capsys, baixados):
    with pytest.raises(SystemExit) as saida:
        main(["https://exemplo.com/video", "--qualidade", "4k"])

    assert saida.value.code == 2
    assert baixados == []
    assert "--qualidade" in capsys.readouterr().err


@pytest.mark.parametrize("formato", ["mp3", "wav"])
def test_qualidade_em_formato_de_audio_termina_com_erro_de_uso(
    capsys, baixados, formato
):
    with pytest.raises(SystemExit) as saida:
        main(["https://exemplo.com/video", "--formato", formato, "--qualidade", "720"])

    assert saida.value.code == 2
    assert baixados == []
    assert f"não se aplica ao formato {formato}" in capsys.readouterr().err


def test_pasta_escolhida_e_criada_e_chega_ao_download(baixados, tmp_path):
    destino = tmp_path / "nova"

    assert main(["https://exemplo.com/video", "--pasta", str(destino)]) == 0

    assert destino.is_dir()
    assert baixados == [("https://exemplo.com/video", "mp4", "melhor", destino.resolve())]


def test_pasta_invalida_mostra_erro_e_nao_tenta_baixar(capsys, baixados, tmp_path):
    arquivo = tmp_path / "arquivo.txt"
    arquivo.touch()

    assert main(["https://exemplo.com/video", "--pasta", str(arquivo)]) == 2

    capturado = capsys.readouterr()
    assert baixados == []
    assert capturado.err.startswith("baixar: erro: ")
    assert "onde deveria haver uma pasta" in capturado.err
    assert capturado.out == ""


def test_link_invalido_nao_cria_a_pasta(baixados, tmp_path):
    destino = tmp_path / "nova"

    assert main(["exemplo.com/video", "--pasta", str(destino)]) == 2

    assert not destino.exists()
    assert baixados == []


def test_formato_desconhecido_termina_com_erro_de_uso(capsys, baixados):
    with pytest.raises(SystemExit) as saida:
        main(["https://exemplo.com/video", "--formato", "flac"])

    assert saida.value.code == 2
    assert baixados == []
    assert "--formato" in capsys.readouterr().err


def test_link_invalido_mostra_erro_e_nao_tenta_baixar(capsys, baixados):
    assert main(["exemplo.com/video"]) == 2

    capturado = capsys.readouterr()
    assert baixados == []
    assert capturado.err.startswith("baixar: erro: ")
    assert "http:// ou https://" in capturado.err
    assert capturado.out == ""


def test_falha_no_download_mostra_erro_e_termina_com_codigo_1(capsys, monkeypatch):
    def falhar(*pedido, **opcoes):
        raise FalhaNoDownload("O yt-dlp terminou com o código 1.")

    monkeypatch.setattr(cli, "baixar", falhar)

    assert main(["https://exemplo.com/video"]) == 1

    capturado = capsys.readouterr()
    assert capturado.err.endswith("baixar: erro: O yt-dlp terminou com o código 1.\n")
    assert capturado.out == ""


def test_ctrl_c_mostra_cancelamento_e_termina_com_codigo_130(capsys, monkeypatch):
    def interromper(*pedido, **opcoes):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "baixar", interromper)

    assert main(["https://exemplo.com/video"]) == 130

    capturado = capsys.readouterr()
    assert "cancelado" in capturado.err
    assert "concluído" not in capturado.out


def test_mostra_o_caminho_do_arquivo_final(capsys, monkeypatch):
    monkeypatch.setattr(cli, "baixar", lambda *pedido, **opcoes: "C:/Videos/aula.mp4")

    assert main(["https://exemplo.com/video"]) == 0

    assert "Arquivo salvo em: C:/Videos/aula.mp4" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("progresso", "esperado"),
    [
        (
            Progresso(ETAPA_BAIXANDO, 42.26, "1.28MiB/s", "00:12"),
            "Baixando  42.3% | 1.28MiB/s | restam 00:12",
        ),
        (Progresso(ETAPA_BAIXANDO, 100.0), "Baixando 100.0%"),
        (Progresso(ETAPA_BAIXANDO), "Baixando"),
        (Progresso(ETAPA_PROCESSANDO), "Processando o arquivo..."),
        (
            Progresso(ETAPA_ATUALIZANDO),
            "O download falhou. Atualizando o yt-dlp para tentar de novo...",
        ),
    ],
)
def test_formata_o_progresso(progresso, esperado):
    assert cli.formatar_progresso(progresso) == esperado


def baixar_avisando_progresso(*pedido, ao_progredir, **opcoes):
    ao_progredir(Progresso(ETAPA_BAIXANDO, 50.0))


def test_progresso_aparece_no_terminal_na_mesma_linha(capsys, monkeypatch):
    monkeypatch.setattr(cli, "baixar", baixar_avisando_progresso)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)

    assert main(["https://exemplo.com/video"]) == 0

    assert "\rBaixando  50.0%" in capsys.readouterr().err


def test_progresso_nao_aparece_na_saida_redirecionada(capsys, monkeypatch):
    monkeypatch.setattr(cli, "baixar", baixar_avisando_progresso)

    assert main(["https://exemplo.com/video"]) == 0

    assert "Baixando" not in capsys.readouterr().err


@pytest.mark.parametrize(
    ("argumentos", "esperado"),
    [
        ([], "falta informar: link"),
        (["https://exemplo.com", "--formato", "flac"], "valor inválido para --formato"),
        (["https://exemplo.com", "--pasta"], "a opção --pasta precisa de um valor"),
        (["https://exemplo.com", "--xyz"], "opção desconhecida: --xyz"),
    ],
)
def test_erros_de_uso_saem_em_portugues(capsys, argumentos, esperado):
    with pytest.raises(SystemExit) as saida:
        main(argumentos)

    assert saida.value.code == 2
    erro = capsys.readouterr().err
    assert erro.startswith(f"baixar: erro: {esperado}")
    assert "--help" in erro


def test_saida_redirecionada_usa_utf8():
    ambiente = {**os.environ, "PYTHONUTF8": "0"}
    ambiente.pop("PYTHONIOENCODING", None)

    resultado = subprocess.run(
        [sys.executable, "-c", "from baixador.cli import main; main(['--help'])"],
        capture_output=True,
        env=ambiente,
    )

    assert resultado.returncode == 0
    assert "Baixa um vídeo".encode("utf-8") in resultado.stdout
