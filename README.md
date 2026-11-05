# Baixador de vídeos

Ferramenta minimalista para baixar um vídeo em MP4 ou extrair o áudio em MP3 ou WAV.

> **Status:** em desenvolvimento. Por enquanto, o comando salva sempre na pasta atual. A escolha da qualidade e da pasta ainda não foi implementada.

## Requisitos

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) e [ffmpeg](https://ffmpeg.org/), com o ffprobe que o acompanha, instalados e disponíveis no PATH.

## Uso atual

```text
baixar <link>                  # vídeo em MP4
baixar <link> --formato mp3    # apenas o áudio, em MP3
baixar <link> --formato wav    # apenas o áudio, em WAV
```

O comando baixa um único item. Se o link for de uma playlist, apenas o primeiro é baixado.

## Uso previsto

```text
baixar <link> --formato mp3 --pasta "C:\Musicas"
```

## Desenvolvimento

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows com Git Bash
# .venv\Scripts\Activate.ps1    # Windows com PowerShell
pip install -e ".[dev]"
pytest
```

Se o projeto estiver em uma pasta sincronizada, como o OneDrive, crie o ambiente virtual fora dela para evitar sincronização pesada.

## Uso responsável

Este projeto é para uso pessoal, apenas com conteúdo próprio ou autorizado. Ele não contorna DRM, paywalls nem bloqueios de acesso. Os Termos de Serviço do YouTube restringem downloads, e cada pessoa é responsável por respeitá-los e por respeitar os direitos autorais.

## Licença

[MIT](LICENSE)
