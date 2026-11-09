import tkinter as tk
from pathlib import Path

import pytest

from baixador import janela as modulo
from baixador.download import FalhaNoDownload
from baixador.janela import (
    TEXTO_BAIXANDO,
    TEXTO_INICIAL,
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

    def registrar(*pedido):
        pedidos.append(pedido)
        return tmp_path / "aula.mp4"

    monkeypatch.setattr(modulo, "baixar", registrar)
    avisos = []

    executar(Pedido(LINK, "mp4", "720", tmp_path), avisos.append)

    assert pedidos == [(LINK, "mp4", "720", tmp_path)]
    assert avisos == [
        Resultado(True, f"Download concluído. Arquivo salvo em: {tmp_path / 'aula.mp4'}")
    ]


def test_executar_sem_o_nome_do_arquivo_avisa_a_pasta(monkeypatch, tmp_path):
    monkeypatch.setattr(modulo, "baixar", lambda *pedido: None)
    avisos = []

    executar(Pedido(LINK, "mp4", "melhor", tmp_path), avisos.append)

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
    def falhar(*pedido):
        raise erro

    monkeypatch.setattr(modulo, "baixar", falhar)
    avisos = []

    executar(Pedido(LINK, "mp4", "melhor", tmp_path), avisos.append)

    assert len(avisos) == 1
    assert not avisos[0].sucesso
    assert avisos[0].texto.startswith(esperado)


# --- Janela de verdade: precisa de uma tela, então é pulada no Linux do CI. ---


@pytest.fixture
def janela(monkeypatch, tmp_path):
    monkeypatch.setattr(modulo, "pasta_inicial", lambda: tmp_path)
    try:
        raiz = tk.Tk()
    except tk.TclError:
        pytest.skip("não há tela para abrir a janela")
    raiz.withdraw()
    yield Janela(raiz)
    raiz.destroy()


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


def test_qualidade_fica_desabilitada_em_formato_de_audio(janela):
    janela.formato.set("mp3")
    janela._ajustar_qualidade()
    assert str(janela.campo_da_qualidade.cget("state")) == "disabled"

    janela.formato.set("mp4")
    janela._ajustar_qualidade()
    assert str(janela.campo_da_qualidade.cget("state")) == "readonly"


def test_link_invalido_mostra_o_erro_e_nao_comeca_o_download(janela, monkeypatch):
    chamadas = []
    monkeypatch.setattr(modulo, "baixar", lambda *pedido: chamadas.append(pedido))
    janela.link.set("exemplo.com/video")

    janela.iniciar()

    assert janela.situacao.get().startswith("Erro: O link precisa começar com http")
    assert not janela.baixando
    assert chamadas == []


def test_download_trava_o_botao_e_mostra_o_resultado_no_fim(janela, monkeypatch, tmp_path):
    monkeypatch.setattr(modulo, "baixar", lambda *pedido: tmp_path / "aula.mp4")
    janela.link.set(LINK)

    janela.iniciar()

    assert janela.baixando
    assert janela.situacao.get() == TEXTO_BAIXANDO
    assert str(janela.botao_baixar.cget("state")) == "disabled"

    esperar_o_fim(janela)

    assert not janela.baixando
    assert janela.situacao.get().endswith(str(tmp_path / "aula.mp4"))
    assert str(janela.botao_baixar.cget("state")) == "normal"


def test_segundo_clique_durante_o_download_e_ignorado(janela, monkeypatch):
    chamadas = []
    monkeypatch.setattr(modulo, "baixar", lambda *pedido: chamadas.append(pedido))
    janela.link.set(LINK)

    janela.iniciar()
    janela.iniciar()
    esperar_o_fim(janela)

    assert len(chamadas) == 1


def test_falha_no_download_aparece_na_janela_e_libera_o_botao(janela, monkeypatch):
    def falhar(*pedido):
        raise FalhaNoDownload("Não foi possível conectar ao site.")

    monkeypatch.setattr(modulo, "baixar", falhar)
    janela.link.set(LINK)

    janela.iniciar()
    esperar_o_fim(janela)

    assert janela.situacao.get() == "Erro: Não foi possível conectar ao site."
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
