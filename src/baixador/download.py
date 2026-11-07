"""Download de vídeos e áudios, delegado ao yt-dlp e ao ffmpeg instalados no PC."""

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from baixador.erros import traduzir_erro

# O ffprobe acompanha o ffmpeg, e o yt-dlp precisa dele para extrair o áudio.
PROGRAMAS_NECESSARIOS = ("yt-dlp", "ffmpeg", "ffprobe")

OPCOES_POR_FORMATO = {
    # Prefere H.264 e AAC, para o arquivo abrir na maioria dos players.
    "mp4": ("--preset-alias", "mp4"),
    # Prefere uma fonte que já esteja em MP3, evitando recomprimir o áudio.
    "mp3": ("--preset-alias", "mp3"),
    # O yt-dlp não tem um preset para WAV.
    "wav": ("--extract-audio", "--audio-format", "wav"),
}
FORMATOS = tuple(OPCOES_POR_FORMATO)
FORMATO_PADRAO = "mp4"

QUALIDADE_PADRAO = "melhor"
QUALIDADES = (QUALIDADE_PADRAO, "1080", "720", "480", "360")
# Em MP3 e WAV, a resolução não se aplica.
FORMATOS_COM_QUALIDADE = ("mp4",)

ETAPA_BAIXANDO = "baixando"
ETAPA_PROCESSANDO = "processando"

# Marcam as linhas que o programa pediu ao yt-dlp, para separá-las do resto da saída.
MARCA_PROGRESSO = "[baixador-progresso]"
MARCA_PROCESSANDO = "[baixador-processando]"
MARCA_ARQUIVO = "[baixador-arquivo]"
MARCA_ERRO = "ERROR:"

MODELO_PROGRESSO = (
    f"download:{MARCA_PROGRESSO}"
    "%(progress._percent)s|%(progress._speed_str)s|%(progress._eta_str)s"
)
MODELO_PROCESSANDO = f"postprocess:{MARCA_PROCESSANDO}"
MODELO_ARQUIVO = f"after_move:{MARCA_ARQUIVO}%(filepath)s"

# O que o yt-dlp escreve quando ainda não sabe o valor.
VALORES_DESCONHECIDOS = ("NA", "Unknown")


class FalhaNoDownload(RuntimeError):
    """O download não pôde ser iniciado ou não terminou com sucesso."""


@dataclass(frozen=True)
class Progresso:
    """Situação do download. Os campos ficam vazios enquanto o valor é desconhecido."""

    etapa: str
    percentual: float | None = None
    velocidade: str | None = None
    restante: str | None = None


def _valor_conhecido(texto: str) -> str | None:
    texto = texto.strip()
    if not texto or any(texto.startswith(valor) for valor in VALORES_DESCONHECIDOS):
        return None
    return texto


def interpretar_progresso(dados: str) -> Progresso:
    """Converte "percentual|velocidade|restante", o formato de MODELO_PROGRESSO."""
    percentual, velocidade, restante = dados.split("|")

    try:
        numero = float(percentual)
    except ValueError:
        numero = None

    return Progresso(
        ETAPA_BAIXANDO, numero, _valor_conhecido(velocidade), _valor_conhecido(restante)
    )


def montar_comando(
    link: str,
    formato: str = FORMATO_PADRAO,
    qualidade: str = QUALIDADE_PADRAO,
    pasta: Path | None = None,
) -> list[str]:
    """Monta o comando do yt-dlp que baixa um único item com as opções pedidas."""
    opcoes_de_qualidade = []
    if qualidade != QUALIDADE_PADRAO and formato in FORMATOS_COM_QUALIDADE:
        # Pega a maior resolução até o limite ou, se não houver, a menor disponível.
        # Precisa vir depois do preset: antes dele, o yt-dlp ignora o limite.
        opcoes_de_qualidade = ["--format-sort", f"res:{qualidade}"]

    # O prefixo "home:" evita que o começo do caminho seja lido como outro tipo.
    opcoes_de_pasta = [] if pasta is None else ["--paths", f"home:{pasta}"]

    return [
        "yt-dlp",
        *OPCOES_POR_FORMATO[formato],
        *opcoes_de_qualidade,
        *opcoes_de_pasta,
        # Sem isto, o Windows entrega os acentos na codificação do sistema.
        "--encoding",
        "utf-8",
        "--no-warnings",
        # --print deixa o yt-dlp silencioso; --progress traz de volta só o progresso.
        "--print",
        MODELO_ARQUIVO,
        "--progress",
        "--newline",
        "--progress-template",
        MODELO_PROGRESSO,
        "--progress-template",
        MODELO_PROCESSANDO,
        # --no-playlist cobre o link de um vídeo dentro de uma playlist;
        # --playlist-items cobre o link da própria playlist.
        "--no-playlist",
        "--playlist-items",
        "1",
        # Tudo depois de "--" é tratado como link, nunca como opção.
        "--",
        link,
    ]


def baixar(
    link: str,
    formato: str = FORMATO_PADRAO,
    qualidade: str = QUALIDADE_PADRAO,
    pasta: Path | None = None,
    ao_progredir: Callable[[Progresso], None] | None = None,
) -> Path | None:
    """Baixa o item e devolve o caminho do arquivo final, ou levanta FalhaNoDownload.

    Salva na pasta indicada ou, sem ela, na atual. A interface recebe o andamento
    por ao_progredir, então este módulo não precisa saber se é terminal ou janela.
    """
    avisar = ao_progredir or (lambda progresso: None)
    for programa in PROGRAMAS_NECESSARIOS:
        if shutil.which(programa) is None:
            raise FalhaNoDownload(f"O programa {programa} não foi encontrado no PATH.")

    arquivo = None
    erro = None
    processando = False

    # O stderr vai para o mesmo tubo: ler dois tubos em sequência poderia travar,
    # com o yt-dlp esperando que o tubo cheio fosse lido.
    with subprocess.Popen(
        montar_comando(link, formato, qualidade, pasta),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    ) as processo:
        try:
            for linha in processo.stdout:
                linha = linha.rstrip("\r\n")
                if linha.startswith(MARCA_PROGRESSO):
                    avisar(interpretar_progresso(linha.removeprefix(MARCA_PROGRESSO)))
                elif linha.startswith(MARCA_PROCESSANDO):
                    # O yt-dlp avisa várias vezes, uma para cada pós-processador.
                    if not processando:
                        processando = True
                        avisar(Progresso(ETAPA_PROCESSANDO))
                elif linha.startswith(MARCA_ARQUIVO):
                    arquivo = Path(linha.removeprefix(MARCA_ARQUIVO))
                elif linha.startswith(MARCA_ERRO):
                    erro = linha
        except BaseException:
            # Inclui o Ctrl+C: sem isto, o yt-dlp continuaria baixando sozinho.
            processo.kill()
            raise

    if processo.returncode != 0:
        if erro is not None:
            raise FalhaNoDownload(traduzir_erro(erro))
        raise FalhaNoDownload(f"O yt-dlp terminou com o código {processo.returncode}.")

    return arquivo
