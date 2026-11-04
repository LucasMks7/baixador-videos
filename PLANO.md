# Baixador de vídeos

Ferramenta minimalista para baixar um vídeo em MP4 ou extrair o áudio em MP3 ou WAV.

## Decisões

- **Formato:** primeiro linha de comando; depois uma janela simples que reutiliza o mesmo núcleo.
- **Base:** yt-dlp e ffmpeg, já instalados no PC. O projeto não reimplementa o download.
- **Linguagem:** Python.
- **Repositório:** público, com licença MIT.

## Uso previsto

```text
baixar <link> --formato mp3 --pasta "C:\Musicas"
```

## Fora do escopo

- Contornar DRM, paywall ou bloqueios de acesso.
- Baixar playlists inteiras na v1.

## Aviso para o README

Uso pessoal, apenas para conteúdo próprio ou autorizado. Os Termos de Serviço do YouTube restringem downloads, e cada pessoa é responsável por respeitá-los e por respeitar os direitos autorais.

## Pronto quando

- Os três formatos funcionam na linha de comando e na janela.
- Links inválidos e falhas de rede geram mensagens claras.
- Os testes rodam no CI sem depender da rede.
