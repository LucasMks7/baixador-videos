import subprocess
import sys
from pathlib import Path

import pytest

from baixador import download
from baixador.download import (
    ETAPA_BAIXANDO,
    ETAPA_PROCESSANDO,
    FORMATOS,
    Cancelamento,
    DownloadCancelado,
    FalhaNoDownload,
    Progresso,
    baixar,
    interpretar_progresso,
    montar_comando,
)

LINK = "https://exemplo.com/video"

encerrar_de_verdade = download.encerrar


@pytest.fixture(autouse=True)
def encerrar_sem_taskkill(monkeypatch):
    """Os processos falsos não têm PID; o taskkill só roda no teste que o cobre."""
    monkeypatch.setattr(download, "encerrar", lambda processo: processo.kill())


@pytest.fixture
def programas_instalados(monkeypatch):
    monkeypatch.setattr(download.shutil, "which", lambda programa: programa)


class ProcessoFalso:
    """Imita o subprocess.Popen, entregando linhas prontas em vez de rodar o yt-dlp."""

    def __init__(self, linhas, codigo_de_saida):
        self.stdout = iter(linhas)
        self.codigo_de_saida = codigo_de_saida
        self.returncode = None
        self.encerrado = False

    def __enter__(self):
        return self

    def __exit__(self, *erro):
        self.returncode = self.codigo_de_saida

    def kill(self):
        self.encerrado = True


def simular_execucao(monkeypatch, codigo_de_saida, linhas=()):
    """Troca o subprocess.Popen por um dublê e devolve os comandos recebidos."""
    chamadas = []

    def executar(comando, **opcoes):
        chamadas.append(comando)
        return ProcessoFalso(linhas, codigo_de_saida)

    monkeypatch.setattr(download.subprocess, "Popen", executar)
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


@pytest.mark.parametrize("qualidade", ["1080", "720", "480", "360"])
def test_limite_de_qualidade_vem_depois_do_preset(qualidade):
    comando = montar_comando(LINK, "mp4", qualidade)

    posicao_do_limite = comando.index("--format-sort")
    assert comando[posicao_do_limite + 1] == f"res:{qualidade}"
    # Antes do preset, o yt-dlp ignoraria o limite sem avisar.
    assert comando.index("--preset-alias") < posicao_do_limite


@pytest.mark.parametrize("formato", FORMATOS)
def test_qualidade_padrao_nao_limita_a_resolucao(formato):
    assert "--format-sort" not in montar_comando(LINK, formato)


@pytest.mark.parametrize("formato", ["mp3", "wav"])
def test_qualidade_nao_afeta_formatos_de_audio(formato):
    assert montar_comando(LINK, formato, "720") == montar_comando(LINK, formato)


def test_pasta_vai_para_o_yt_dlp_como_destino_final(tmp_path):
    comando = montar_comando(LINK, pasta=tmp_path)

    assert comando[comando.index("--paths") + 1] == f"home:{tmp_path}"


def test_sem_pasta_o_comando_usa_a_pasta_atual():
    assert "--paths" not in montar_comando(LINK)


@pytest.mark.usefixtures("programas_instalados")
@pytest.mark.parametrize("formato", FORMATOS)
def test_baixar_executa_o_comando_do_formato(monkeypatch, formato):
    chamadas = simular_execucao(monkeypatch, codigo_de_saida=0)

    baixar(LINK, formato)

    assert chamadas == [montar_comando(LINK, formato)]


@pytest.mark.usefixtures("programas_instalados")
def test_baixar_repassa_qualidade_e_pasta(monkeypatch, tmp_path):
    chamadas = simular_execucao(monkeypatch, codigo_de_saida=0)

    baixar(LINK, "mp4", "720", tmp_path)

    assert chamadas == [montar_comando(LINK, "mp4", "720", tmp_path)]


@pytest.mark.usefixtures("programas_instalados")
def test_codigo_de_saida_diferente_de_zero_vira_falha(monkeypatch):
    simular_execucao(monkeypatch, codigo_de_saida=1)

    with pytest.raises(FalhaNoDownload, match="código 1"):
        baixar(LINK)


@pytest.mark.usefixtures("programas_instalados")
def test_erro_do_yt_dlp_vira_mensagem_traduzida(monkeypatch):
    simular_execucao(
        monkeypatch, 1, ["ERROR: Unsupported URL: https://exemplo.com/video\n"]
    )

    with pytest.raises(FalhaNoDownload, match="não é suportado"):
        baixar(LINK)


@pytest.mark.usefixtures("programas_instalados")
def test_baixar_avisa_o_progresso_e_devolve_o_arquivo(monkeypatch):
    simular_execucao(
        monkeypatch,
        0,
        [
            "[baixador-progresso]12.5| 1.00MiB/s|00:10\n",
            "linha que o programa não pediu\n",
            "[baixador-processando]\n",
            "[baixador-processando]\n",
            "[baixador-arquivo]C:\\Vídeos\\aula.mp4\r\n",
        ],
    )
    recebidos = []

    arquivo = baixar(LINK, ao_progredir=recebidos.append)

    assert arquivo == Path("C:\\Vídeos\\aula.mp4")
    # O aviso repetido de processamento chega uma única vez.
    assert recebidos == [
        Progresso(ETAPA_BAIXANDO, 12.5, "1.00MiB/s", "00:10"),
        Progresso(ETAPA_PROCESSANDO),
    ]


@pytest.mark.usefixtures("programas_instalados")
def test_interrupcao_encerra_o_yt_dlp(monkeypatch):
    def linhas_interrompidas():
        yield "[baixador-progresso]1.0|NA|NA\n"
        raise KeyboardInterrupt

    processo = ProcessoFalso(linhas_interrompidas(), 0)
    monkeypatch.setattr(download.subprocess, "Popen", lambda comando, **opcoes: processo)

    with pytest.raises(KeyboardInterrupt):
        baixar(LINK)

    assert processo.encerrado


@pytest.mark.usefixtures("programas_instalados")
def test_le_a_saida_de_um_processo_de_verdade(monkeypatch):
    """Roda um processo real, sem rede, para cobrir o tubo e a leitura em UTF-8."""
    script = (
        "import sys; sys.stderr.buffer.write('[baixador-arquivo]ação.mp4\\n'.encode())"
    )
    monkeypatch.setattr(
        download, "montar_comando", lambda *args: [sys.executable, "-c", script]
    )

    assert baixar(LINK) == Path("ação.mp4")


@pytest.mark.parametrize(
    ("dados", "esperado"),
    [
        ("42.5|  1.28MiB/s|00:12", Progresso(ETAPA_BAIXANDO, 42.5, "1.28MiB/s", "00:12")),
        ("0.1| Unknown B/s|Unknown", Progresso(ETAPA_BAIXANDO, 0.1)),
        ("100.0|1.49MiB/s|NA", Progresso(ETAPA_BAIXANDO, 100.0, "1.49MiB/s")),
        # Sem o tamanho total, como em uma transmissão ao vivo.
        ("NA|500KiB/s|NA", Progresso(ETAPA_BAIXANDO, None, "500KiB/s")),
    ],
)
def test_interpreta_o_progresso(dados, esperado):
    assert interpretar_progresso(dados) == esperado


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


def linhas_com_cancelamento(cancelamento):
    """Imita o yt-dlp sendo encerrado no meio: a saída acaba logo depois do pedido."""
    yield "[baixador-progresso]10.0|NA|NA\n"
    cancelamento.cancelar()


@pytest.mark.usefixtures("programas_instalados")
def test_cancelar_encerra_o_yt_dlp_e_vira_download_cancelado(monkeypatch):
    cancelamento = Cancelamento()
    processo = ProcessoFalso(linhas_com_cancelamento(cancelamento), 1)
    monkeypatch.setattr(download.subprocess, "Popen", lambda comando, **opcoes: processo)

    with pytest.raises(DownloadCancelado):
        baixar(LINK, cancelamento=cancelamento)

    assert processo.encerrado


@pytest.mark.usefixtures("programas_instalados")
def test_cancelar_antes_de_o_yt_dlp_abrir_encerra_assim_que_ele_abre(monkeypatch):
    cancelamento = Cancelamento()
    cancelamento.cancelar()
    processo = ProcessoFalso([], 1)
    monkeypatch.setattr(download.subprocess, "Popen", lambda comando, **opcoes: processo)

    with pytest.raises(DownloadCancelado):
        baixar(LINK, cancelamento=cancelamento)

    assert processo.encerrado


@pytest.mark.usefixtures("programas_instalados")
def test_download_que_terminou_antes_do_cancelamento_devolve_o_arquivo(monkeypatch):
    cancelamento = Cancelamento()

    def linhas():
        yield "[baixador-arquivo]aula.mp4\n"
        cancelamento.cancelar()

    processo = ProcessoFalso(linhas(), 0)
    monkeypatch.setattr(download.subprocess, "Popen", lambda comando, **opcoes: processo)

    assert baixar(LINK, cancelamento=cancelamento) == Path("aula.mp4")


@pytest.mark.usefixtures("programas_instalados")
def test_cancelar_depois_do_fim_nao_mexe_no_processo(monkeypatch):
    cancelamento = Cancelamento()
    processo = ProcessoFalso([], 0)
    monkeypatch.setattr(download.subprocess, "Popen", lambda comando, **opcoes: processo)

    baixar(LINK, cancelamento=cancelamento)
    cancelamento.cancelar()

    assert not processo.encerrado


@pytest.mark.usefixtures("programas_instalados")
def test_falha_sem_pedido_de_cancelamento_continua_sendo_falha(monkeypatch):
    simular_execucao(monkeypatch, codigo_de_saida=1)

    with pytest.raises(FalhaNoDownload):
        baixar(LINK, cancelamento=Cancelamento())


@pytest.mark.skipif(sys.platform != "win32", reason="a árvore só é encerrada no Windows")
def test_encerrar_leva_tambem_os_processos_filhos():
    """Roda processos reais: o filho faz o papel do ffmpeg aberto pelo yt-dlp."""
    pai = (
        "import subprocess, sys, time;"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],"
        " stdout=sys.stdout);"
        "print('pronto', flush=True);"
        "time.sleep(30)"
    )
    processo = subprocess.Popen(
        [sys.executable, "-c", pai], stdout=subprocess.PIPE, encoding="utf-8"
    )
    assert processo.stdout.readline() == "pronto\n"

    encerrar_de_verdade(processo)

    # O filho herdou a saída do pai: a leitura só termina quando os dois morrem.
    # Com o filho vivo, isto estouraria o tempo.
    processo.communicate(timeout=10)
