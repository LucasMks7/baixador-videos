import threading
import tkinter as tk
from pathlib import Path

import pytest

from baixador import janela as modulo
from baixador.download import (
    ETAPA_BAIXANDO,
    ETAPA_PROCESSANDO,
    Cancelamento,
    DownloadCancelado,
    FalhaNoDownload,
    Progresso,
)
from baixador.janela import (
    TEXTO_CANCELADO,
    TEXTO_CANCELANDO,
    TEXTO_INICIAL,
    TEXTO_PREPARANDO,
    Janela,
    Pedido,
    Resultado,
    executar,
    pasta_inicial,
    preparar_pedido,
)
from baixador.validacao import LinkInvalido, PastaInvalida

LINK = "https://exemplo.com/video"


# --- Lógica sem Tkinter: roda em qualquer máquina, inclusive no CI sem tela. ---


def test_pedido_valido_traz_o_link_limpo_e_a_pasta_criada(tmp_path):
    destino = tmp_path / "nova"

    pedido = preparar_pedido(f"  {LINK}\n", "mp4", "720", str(destino))

    assert pedido == Pedido(LINK, "mp4", "720", destino.resolve())
    assert destino.is_dir()


@pytest.mark.parametrize("formato", ["mp3", "wav"])
def test_pedido_de_audio_ignora_a_qualidade_que_sobrou_no_campo(tmp_path, formato):
    pedido = preparar_pedido(LINK, formato, "720", str(tmp_path))

    assert pedido.qualidade == "melhor"


def test_pedido_com_link_invalido_nao_cria_a_pasta(tmp_path):
    destino = tmp_path / "nova"

    with pytest.raises(LinkInvalido):
        preparar_pedido("exemplo.com/video", "mp4", "melhor", str(destino))

    assert not destino.exists()


def test_pedido_com_pasta_vazia_e_recusado():
    with pytest.raises(PastaInvalida):
        preparar_pedido(LINK, "mp4", "melhor", "  ")


def test_pasta_inicial_e_a_downloads_quando_ela_existe(monkeypatch, tmp_path):
    (tmp_path / "Downloads").mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert pasta_inicial() == tmp_path / "Downloads"


def test_pasta_inicial_e_a_do_usuario_quando_nao_ha_downloads(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert pasta_inicial() == tmp_path


def test_executar_repassa_o_pedido_e_avisa_o_arquivo_salvo(monkeypatch, tmp_path):
    pedidos = []

    def registrar(*pedido, **opcoes):
        pedidos.append((pedido, opcoes["cancelamento"]))
        return tmp_path / "aula.mp4"

    monkeypatch.setattr(modulo, "baixar", registrar)
    avisos = []
    cancelamento = Cancelamento()

    executar(Pedido(LINK, "mp4", "720", tmp_path), avisos.append, cancelamento)

    assert pedidos == [((LINK, "mp4", "720", tmp_path), cancelamento)]
    assert avisos == [
        Resultado(True, f"Download concluído. Arquivo salvo em: {tmp_path / 'aula.mp4'}")
    ]


def test_executar_avisa_o_progresso_antes_do_resultado(monkeypatch, tmp_path):
    andamento = Progresso(ETAPA_BAIXANDO, 50.0)

    def baixar_com_progresso(*pedido, ao_progredir, **opcoes):
        ao_progredir(andamento)

    monkeypatch.setattr(modulo, "baixar", baixar_com_progresso)
    avisos = []

    executar(Pedido(LINK, "mp4", "melhor", tmp_path), avisos.append, Cancelamento())

    assert avisos[0] == andamento
    assert isinstance(avisos[1], Resultado)


def test_executar_avisa_o_cancelamento(monkeypatch, tmp_path):
    def cancelar(*pedido, **opcoes):
        raise DownloadCancelado

    monkeypatch.setattr(modulo, "baixar", cancelar)
    avisos = []

    executar(Pedido(LINK, "mp4", "melhor", tmp_path), avisos.append, Cancelamento())

    assert avisos == [Resultado(False, TEXTO_CANCELADO)]


def test_executar_sem_o_nome_do_arquivo_avisa_a_pasta(monkeypatch, tmp_path):
    monkeypatch.setattr(modulo, "baixar", lambda *pedido, **opcoes: None)
    avisos = []

    executar(Pedido(LINK, "mp4", "melhor", tmp_path), avisos.append, Cancelamento())

    assert avisos == [Resultado(True, f"Download concluído. Arquivo salvo em: {tmp_path}")]


@pytest.mark.parametrize(
    ("erro", "esperado"),
    [
        (FalhaNoDownload("Este vídeo não está disponível."), "Erro: Este vídeo não"),
        # Um erro imprevisto não pode matar a thread sem avisar a janela.
        (OSError("disco removido"), "Erro inesperado: disco removido"),
    ],
)
def test_executar_avisa_a_falha_em_vez_de_levantar(monkeypatch, tmp_path, erro, esperado):
    def falhar(*pedido, **opcoes):
        raise erro

    monkeypatch.setattr(modulo, "baixar", falhar)
    avisos = []

    executar(Pedido(LINK, "mp4", "melhor", tmp_path), avisos.append, Cancelamento())

    assert len(avisos) == 1
    assert not avisos[0].sucesso
    assert avisos[0].texto.startswith(esperado)


# --- Janela de verdade: precisa de uma tela, então é pulada no Linux do CI. ---


@pytest.fixture(scope="session")
def tk_da_sessao():
    """Um único Tk para todos os testes.

    Criar e destruir vários em seguida falha de vez em quando no Windows, e o
    teste seria pulado como se não houvesse tela.
    """
    try:
        raiz = tk.Tk()
    except tk.TclError:
        pytest.skip("não há tela para abrir a janela")
    raiz.withdraw()
    yield raiz
    raiz.destroy()


@pytest.fixture
def janela(monkeypatch, tmp_path, tk_da_sessao):
    monkeypatch.setattr(modulo, "pasta_inicial", lambda: tmp_path)
    # Cada teste recebe uma janela filha nova, que pode ser fechada à vontade.
    topo = tk.Toplevel(tk_da_sessao)
    topo.withdraw()
    yield Janela(topo)
    if topo.winfo_exists():
        topo.destroy()


def esperar_o_fim(janela):
    """Espera a thread de trabalho e lê a fila, como o laço da janela faria."""
    janela.thread.join(timeout=5)
    janela.ler_fila()


def test_janela_abre_com_os_padroes(janela, tmp_path):
    assert janela.formato.get() == "mp4"
    assert janela.qualidade.get() == "melhor"
    assert janela.pasta.get() == str(tmp_path)
    assert janela.situacao.get() == TEXTO_INICIAL
    assert not janela.baixando
    assert str(janela.botao_cancelar.cget("state")) == "disabled"


def test_qualidade_fica_desabilitada_em_formato_de_audio(janela):
    janela.formato.set("mp3")
    janela._ajustar_qualidade()
    assert str(janela.campo_da_qualidade.cget("state")) == "disabled"

    janela.formato.set("mp4")
    janela._ajustar_qualidade()
    assert str(janela.campo_da_qualidade.cget("state")) == "readonly"


def test_link_invalido_mostra_o_erro_e_nao_comeca_o_download(janela, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        modulo, "baixar", lambda *pedido, **opcoes: chamadas.append(pedido)
    )
    janela.link.set("exemplo.com/video")

    janela.iniciar()

    assert janela.situacao.get().startswith("Erro: O link precisa começar com http")
    assert not janela.baixando
    assert chamadas == []


def test_download_trava_o_botao_e_mostra_o_resultado_no_fim(janela, monkeypatch, tmp_path):
    monkeypatch.setattr(
        modulo, "baixar", lambda *pedido, **opcoes: tmp_path / "aula.mp4"
    )
    janela.link.set(LINK)

    janela.iniciar()

    assert janela.baixando
    assert janela.situacao.get() == TEXTO_PREPARANDO
    assert str(janela.botao_baixar.cget("state")) == "disabled"
    assert str(janela.botao_cancelar.cget("state")) == "normal"

    esperar_o_fim(janela)

    assert not janela.baixando
    assert janela.situacao.get().endswith(str(tmp_path / "aula.mp4"))
    assert janela.barra.cget("value") == 100
    assert str(janela.botao_baixar.cget("state")) == "normal"
    assert str(janela.botao_cancelar.cget("state")) == "disabled"


def test_segundo_clique_durante_o_download_e_ignorado(janela, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        modulo, "baixar", lambda *pedido, **opcoes: chamadas.append(pedido)
    )
    janela.link.set(LINK)

    janela.iniciar()
    janela.iniciar()
    esperar_o_fim(janela)

    assert len(chamadas) == 1


def test_falha_no_download_aparece_na_janela_e_libera_o_botao(janela, monkeypatch):
    def falhar(*pedido, **opcoes):
        raise FalhaNoDownload("Não foi possível conectar ao site.")

    monkeypatch.setattr(modulo, "baixar", falhar)
    janela.link.set(LINK)

    janela.iniciar()
    esperar_o_fim(janela)

    assert janela.situacao.get() == "Erro: Não foi possível conectar ao site."
    assert janela.barra.cget("value") == 0
    assert str(janela.botao_baixar.cget("state")) == "normal"


def test_escolher_pasta_preenche_o_campo(janela, monkeypatch, tmp_path):
    escolhida = tmp_path / "musicas"
    monkeypatch.setattr(
        modulo.filedialog, "askdirectory", lambda **opcoes: escolhida.as_posix()
    )

    janela.escolher_pasta()

    assert janela.pasta.get() == str(escolhida)


def test_cancelar_a_escolha_mantem_a_pasta_anterior(janela, monkeypatch, tmp_path):
    monkeypatch.setattr(modulo.filedialog, "askdirectory", lambda **opcoes: "")

    janela.escolher_pasta()

    assert janela.pasta.get() == str(tmp_path)


def test_progresso_move_a_barra_e_atualiza_o_texto(janela):
    janela.fila.put(Progresso(ETAPA_BAIXANDO, 42.26, "1.28MiB/s", "00:12"))

    janela.ler_fila()

    assert janela.situacao.get() == "Baixando 42.3% | 1.28MiB/s | restam 00:12"
    assert str(janela.barra.cget("mode")) == "determinate"
    assert janela.barra.cget("value") == pytest.approx(42.26)


@pytest.mark.parametrize(
    "progresso",
    [
        Progresso(ETAPA_PROCESSANDO),
        # Sem o tamanho total, como em uma transmissão ao vivo.
        Progresso(ETAPA_BAIXANDO, None, "500KiB/s"),
    ],
)
def test_sem_percentual_a_barra_fica_em_vaivem(janela, progresso):
    janela.fila.put(Progresso(ETAPA_BAIXANDO, 99.0))
    janela.fila.put(progresso)

    janela.ler_fila()

    assert str(janela.barra.cget("mode")) == "indeterminate"


@pytest.fixture
def download_demorado(monkeypatch):
    """Um download que só termina quando é cancelado, como o de um arquivo grande."""
    comecou = threading.Event()

    def baixar(*pedido, ao_progredir, cancelamento):
        ao_progredir(Progresso(ETAPA_BAIXANDO, 10.0))
        comecou.set()
        # O dublê não tem um processo para ser encerrado, então espera o pedido.
        while not cancelamento.pedido:
            comecou.wait(0.01)
        raise DownloadCancelado

    monkeypatch.setattr(modulo, "baixar", baixar)
    return comecou


def test_cancelar_interrompe_o_download_e_libera_a_janela(janela, download_demorado):
    janela.link.set(LINK)
    janela.iniciar()
    assert download_demorado.wait(timeout=5)

    janela.cancelar()

    assert janela.situacao.get() == TEXTO_CANCELANDO
    assert str(janela.botao_cancelar.cget("state")) == "disabled"

    esperar_o_fim(janela)

    # O progresso que ficou na fila não pode apagar o aviso de cancelamento.
    assert janela.situacao.get() == TEXTO_CANCELADO
    assert not janela.baixando
    assert janela.barra.cget("value") == 0
    assert str(janela.botao_baixar.cget("state")) == "normal"


def test_depois_de_cancelar_da_para_baixar_de_novo(janela, download_demorado, monkeypatch):
    janela.link.set(LINK)
    janela.iniciar()
    assert download_demorado.wait(timeout=5)
    janela.cancelar()
    esperar_o_fim(janela)

    monkeypatch.setattr(modulo, "baixar", lambda *pedido, **opcoes: None)
    janela.iniciar()
    esperar_o_fim(janela)

    assert janela.situacao.get().startswith("Download concluído")


def test_fechar_a_janela_cancela_o_download(janela, download_demorado):
    janela.link.set(LINK)
    janela.iniciar()
    assert download_demorado.wait(timeout=5)
    thread = janela.thread

    janela.fechar()

    thread.join(timeout=5)
    assert not thread.is_alive()
    assert janela.cancelamento.pedido


def test_cancelar_sem_download_nao_faz_nada(janela):
    janela.cancelar()

    assert janela.situacao.get() == TEXTO_INICIAL
    assert not janela.cancelamento.pedido
