"""Janela simples sobre o mesmo núcleo da linha de comando."""

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, ttk

from baixador.download import (
    FORMATO_PADRAO,
    FORMATOS,
    FORMATOS_COM_QUALIDADE,
    QUALIDADE_PADRAO,
    QUALIDADES,
    FalhaNoDownload,
    baixar,
)
from baixador.validacao import (
    LinkInvalido,
    PastaInvalida,
    preparar_pasta,
    validar_link,
)

# De quanto em quanto tempo a janela olha a fila de mensagens da thread de trabalho.
INTERVALO_DA_FILA_MS = 100

TEXTO_INICIAL = "Cole o link e clique em Baixar."
TEXTO_BAIXANDO = "Baixando... A janela avisa quando terminar."


@dataclass(frozen=True)
class Pedido:
    """O que a pessoa pediu na janela, já validado."""

    link: str
    formato: str
    qualidade: str
    pasta: Path


@dataclass(frozen=True)
class Resultado:
    """Como o download terminou, com o texto que a janela mostra."""

    sucesso: bool
    texto: str


def pasta_inicial() -> Path:
    """Sugere a pasta Downloads: a pasta atual de um programa com janela é arbitrária."""
    downloads = Path.home() / "Downloads"
    return downloads if downloads.is_dir() else Path.home()


def preparar_pedido(link: str, formato: str, qualidade: str, pasta: str) -> Pedido:
    """Valida os campos da janela ou levanta LinkInvalido ou PastaInvalida."""
    link = validar_link(link)
    if formato not in FORMATOS_COM_QUALIDADE:
        # O campo de qualidade fica desabilitado, mas ainda guarda o último valor.
        qualidade = QUALIDADE_PADRAO
    # Vem depois do link, para um link errado não deixar uma pasta vazia para trás.
    return Pedido(link, formato, qualidade, preparar_pasta(pasta))


def executar(pedido: Pedido, avisar: Callable[[Resultado], None]) -> None:
    """Faz o download e avisa o resultado. Roda fora da thread da janela."""
    try:
        arquivo = baixar(pedido.link, pedido.formato, pedido.qualidade, pedido.pasta)
    except FalhaNoDownload as erro:
        avisar(Resultado(False, f"Erro: {erro}"))
    except Exception as erro:
        # Sem isto, um erro imprevisto mataria a thread em silêncio e a janela
        # ficaria em "Baixando..." para sempre.
        avisar(Resultado(False, f"Erro inesperado: {erro}"))
    else:
        destino = pedido.pasta if arquivo is None else arquivo
        avisar(Resultado(True, f"Download concluído. Arquivo salvo em: {destino}"))


class Janela:
    """Monta os campos e mantém a janela respondendo enquanto o download roda."""

    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        # O Tkinter só pode ser usado pela thread que o criou. A thread de trabalho
        # deixa as mensagens nesta fila, e a janela as lê de tempos em tempos.
        self.fila: queue.Queue[Resultado] = queue.Queue()
        self.thread: threading.Thread | None = None

        self.link = tk.StringVar()
        self.formato = tk.StringVar(value=FORMATO_PADRAO)
        self.qualidade = tk.StringVar(value=QUALIDADE_PADRAO)
        self.pasta = tk.StringVar(value=str(pasta_inicial()))
        self.situacao = tk.StringVar(value=TEXTO_INICIAL)

        raiz.title("Baixador de vídeos")
        raiz.resizable(False, False)
        self._montar()
        self._ajustar_qualidade()

    def _montar(self) -> None:
        quadro = ttk.Frame(self.raiz, padding=12)
        quadro.grid()

        ttk.Label(quadro, text="Link").grid(row=0, column=0, sticky="w")
        campo_do_link = ttk.Entry(quadro, textvariable=self.link, width=56)
        campo_do_link.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)
        campo_do_link.bind("<Return>", lambda evento: self.iniciar())
        campo_do_link.focus()

        ttk.Label(quadro, text="Formato").grid(row=1, column=0, sticky="w")
        campo_do_formato = ttk.Combobox(
            quadro, textvariable=self.formato, values=FORMATOS, state="readonly", width=8
        )
        campo_do_formato.grid(row=1, column=1, sticky="w", pady=4)
        campo_do_formato.bind(
            "<<ComboboxSelected>>", lambda evento: self._ajustar_qualidade()
        )

        ttk.Label(quadro, text="Qualidade").grid(row=1, column=2, sticky="e", padx=8)
        self.campo_da_qualidade = ttk.Combobox(
            quadro,
            textvariable=self.qualidade,
            values=QUALIDADES,
            state="readonly",
            width=8,
        )
        self.campo_da_qualidade.grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(quadro, text="Pasta").grid(row=2, column=0, sticky="w")
        ttk.Entry(quadro, textvariable=self.pasta).grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(quadro, text="Escolher...", command=self.escolher_pasta).grid(
            row=2, column=3, sticky="e", padx=(8, 0)
        )

        self.botao_baixar = ttk.Button(quadro, text="Baixar", command=self.iniciar)
        self.botao_baixar.grid(row=3, column=0, columnspan=4, pady=(8, 4))

        ttk.Label(quadro, textvariable=self.situacao, wraplength=440).grid(
            row=4, column=0, columnspan=4, sticky="w"
        )

        quadro.columnconfigure(0, minsize=64)
        quadro.columnconfigure(1, weight=1)

    def _ajustar_qualidade(self) -> None:
        """A resolução só existe em vídeo, então o campo fica apagado em MP3 e WAV."""
        com_qualidade = self.formato.get() in FORMATOS_COM_QUALIDADE
        self.campo_da_qualidade.configure(
            state="readonly" if com_qualidade else "disabled"
        )

    def escolher_pasta(self) -> None:
        escolhida = filedialog.askdirectory(
            parent=self.raiz, initialdir=self.pasta.get(), title="Pasta de destino"
        )
        # Cancelar a caixa devolve um texto vazio; nesse caso, vale a pasta de antes.
        if escolhida:
            self.pasta.set(str(Path(escolhida)))

    def iniciar(self) -> None:
        """Valida os campos e começa o download em outra thread."""
        if self.baixando:
            return

        try:
            pedido = preparar_pedido(
                self.link.get(),
                self.formato.get(),
                self.qualidade.get(),
                self.pasta.get(),
            )
        except (LinkInvalido, PastaInvalida) as erro:
            self.situacao.set(f"Erro: {erro}")
            return

        self.situacao.set(TEXTO_BAIXANDO)
        self.botao_baixar.configure(state="disabled")
        # Em outra thread porque o download bloqueia: na thread da janela, ela
        # pararia de responder. daemon=True não segura o programa aberto ao fechar.
        self.thread = threading.Thread(
            target=executar, args=(pedido, self.fila.put), daemon=True
        )
        self.thread.start()
        self.raiz.after(INTERVALO_DA_FILA_MS, self.ler_fila)

    @property
    def baixando(self) -> bool:
        return self.thread is not None

    def ler_fila(self) -> None:
        """Aplica na janela as mensagens deixadas pela thread de trabalho."""
        try:
            while True:
                self._terminar(self.fila.get_nowait())
        except queue.Empty:
            pass

        if self.baixando:
            self.raiz.after(INTERVALO_DA_FILA_MS, self.ler_fila)

    def _terminar(self, resultado: Resultado) -> None:
        self.thread = None
        self.situacao.set(resultado.texto)
        self.botao_baixar.configure(state="normal")


def main() -> None:
    raiz = tk.Tk()
    Janela(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
