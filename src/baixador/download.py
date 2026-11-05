"""Download de vídeos e áudios, delegado ao yt-dlp e ao ffmpeg instalados no PC."""

import shutil
import subprocess

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


class FalhaNoDownload(RuntimeError):
    """O download não pôde ser iniciado ou não terminou com sucesso."""


def montar_comando(link: str, formato: str = FORMATO_PADRAO) -> list[str]:
    """Monta o comando do yt-dlp que baixa um único item no formato pedido."""
    return [
        "yt-dlp",
        *OPCOES_POR_FORMATO[formato],
        # --no-playlist cobre o link de um vídeo dentro de uma playlist;
        # --playlist-items cobre o link da própria playlist.
        "--no-playlist",
        "--playlist-items",
        "1",
        # Tudo depois de "--" é tratado como link, nunca como opção.
        "--",
        link,
    ]


def baixar(link: str, formato: str = FORMATO_PADRAO) -> None:
    """Baixa o item na pasta atual, no formato pedido, ou levanta FalhaNoDownload."""
    for programa in PROGRAMAS_NECESSARIOS:
        if shutil.which(programa) is None:
            raise FalhaNoDownload(f"O programa {programa} não foi encontrado no PATH.")

    # A saída não é capturada: o yt-dlp mostra o progresso direto no terminal.
    resultado = subprocess.run(montar_comando(link, formato))

    if resultado.returncode != 0:
        raise FalhaNoDownload(
            f"O yt-dlp terminou com o código {resultado.returncode}."
        )
