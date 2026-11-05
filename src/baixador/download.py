"""Download de vídeos, delegado ao yt-dlp e ao ffmpeg instalados no PC."""

import shutil
import subprocess

PROGRAMAS_NECESSARIOS = ("yt-dlp", "ffmpeg")


class FalhaNoDownload(RuntimeError):
    """O download não pôde ser iniciado ou não terminou com sucesso."""


def montar_comando(link: str) -> list[str]:
    """Monta o comando do yt-dlp que baixa um único vídeo em MP4."""
    return [
        "yt-dlp",
        # Prefere H.264 e AAC, para o arquivo abrir na maioria dos players.
        "--preset-alias",
        "mp4",
        # --no-playlist cobre o link de um vídeo dentro de uma playlist;
        # --playlist-items cobre o link da própria playlist.
        "--no-playlist",
        "--playlist-items",
        "1",
        # Tudo depois de "--" é tratado como link, nunca como opção.
        "--",
        link,
    ]


def baixar_mp4(link: str) -> None:
    """Baixa o vídeo em MP4 na pasta atual ou levanta FalhaNoDownload."""
    for programa in PROGRAMAS_NECESSARIOS:
        if shutil.which(programa) is None:
            raise FalhaNoDownload(f"O programa {programa} não foi encontrado no PATH.")

    # A saída não é capturada: o yt-dlp mostra o progresso direto no terminal.
    resultado = subprocess.run(montar_comando(link))

    if resultado.returncode != 0:
        raise FalhaNoDownload(
            f"O yt-dlp terminou com o código {resultado.returncode}."
        )
