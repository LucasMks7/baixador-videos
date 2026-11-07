# Baixador de vídeos

Ferramenta minimalista para baixar um vídeo em MP4 ou extrair o áudio em MP3 ou WAV.

> **Status:** em desenvolvimento.

## Requisitos

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) e [ffmpeg](https://ffmpeg.org/), com o ffprobe que o acompanha, instalados e disponíveis no PATH.

## Uso

```text
baixar <link>                                # vídeo em MP4, na melhor qualidade
baixar <link> --qualidade 720                # vídeo em MP4, até 720p
baixar <link> --formato mp3                  # apenas o áudio, em MP3
baixar <link> --formato wav                  # apenas o áudio, em WAV
baixar <link> --formato mp3 --pasta "C:\Musicas"
```

| Opção | Valores | Padrão |
| --- | --- | --- |
| `--formato` | `mp4`, `mp3`, `wav` | `mp4` |
| `--qualidade` | `melhor`, `1080`, `720`, `480`, `360` (apenas em MP4) | `melhor` |
| `--pasta` | qualquer caminho; a pasta é criada se não existir | a pasta atual |

`--qualidade` é um limite: o comando baixa a maior resolução até o valor pedido. Se o vídeo só existir em resoluções maiores, baixa a menor delas.

No PowerShell, um caminho com espaços não pode terminar em `\`: use `"C:\Minhas Musicas"`, e não `"C:\Minhas Musicas\"`.

O comando baixa um único item. Se o link for de uma playlist, apenas o primeiro é baixado.

Durante o download, o terminal mostra a porcentagem, a velocidade e o tempo restante. Um vídeo em que imagem e som são baixados separadamente mostra a porcentagem duas vezes, uma para cada parte. `Ctrl+C` cancela o download e deixa o arquivo parcial (`.part`) na pasta de destino.

| Código de saída | Significado |
| --- | --- |
| `0` | Download concluído |
| `1` | O download falhou (rede, vídeo indisponível, acesso negado etc.) |
| `2` | Entrada inválida (link, pasta ou opções) |
| `130` | Cancelado com `Ctrl+C` |

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
