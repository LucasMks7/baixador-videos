"""Download de vídeos e áudios, delegado ao yt-dlp e ao ffmpeg instalados no PC."""

import shutil
import subprocess
from pathlib import Path

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


class FalhaNoDownload(RuntimeError):
    """O download não pôde ser iniciado ou não terminou com sucesso."""


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
) -> None:
    """Baixa o item na pasta indicada, ou na atual, ou levanta FalhaNoDownload."""
    for programa in PROGRAMAS_NECESSARIOS:
        if shutil.which(programa) is None:
            raise FalhaNoDownload(f"O programa {programa} não foi encontrado no PATH.")

    # A saída não é capturada: o yt-dlp mostra o progresso direto no terminal.
    resultado = subprocess.run(montar_comando(link, formato, qualidade, pasta))

    if resultado.returncode != 0:
        raise FalhaNoDownload(
            f"O yt-dlp terminou com o código {resultado.returncode}."
        )
