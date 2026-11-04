# Baixador de vídeos

Ferramenta minimalista para baixar um vídeo em MP4 ou extrair o áudio em MP3 ou WAV.

> **Status:** em desenvolvimento. Por enquanto, só a estrutura do projeto e o comando `baixar --version` funcionam. O download ainda não foi implementado.

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
