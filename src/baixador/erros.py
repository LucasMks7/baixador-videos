"""Tradução dos erros do yt-dlp em mensagens claras para quem usa o programa."""

import re

# A ordem importa: vale o primeiro padrão encontrado. "Unable to download webpage"
# aparece tanto em um 404 quanto em uma falha de DNS, então os erros específicos
# vêm antes dos de rede. Os erros de servidor e de formato vêm antes de vídeo
# indisponível porque "Service Unavailable" e "not available" também aparecem neles.
TRADUCOES = (
    (
        r"Unsupported URL",
        "Este site ou link não é suportado pelo yt-dlp.",
    ),
    (
        r"HTTP Error 429",
        "O site recusou o pedido por excesso de acessos. Tente mais tarde.",
    ),
    (
        r"HTTP Error 5\d\d",
        "O site está com problemas no momento. Tente mais tarde.",
    ),
    (
        r"\bDRM\b",
        "Este vídeo é protegido por DRM, e o programa não contorna essa proteção.",
    ),
    (
        r"Requested format",
        "O vídeo não está disponível no formato pedido.",
    ),
    (
        r"Private video|Sign in|\blog ?in\b|members-only|your country|HTTP Error 401",
        "O acesso a este vídeo foi negado: ele pode ser privado, exigir login ou ter "
        "restrição de região. O programa não contorna esses bloqueios.",
    ),
    (
        # O YouTube também responde 403 para vídeos públicos, então isto não indica
        # que o vídeo seja privado.
        r"HTTP Error 403",
        "O site recusou o download (erro 403). Se o vídeo for público, o yt-dlp pode "
        "estar desatualizado: tente atualizá-lo.",
    ),
    (
        r"unavailable|not available|HTTP Error 404|has been removed",
        "Este vídeo não está disponível: ele pode ter sido removido ou o link "
        "pode estar errado.",
    ),
    (
        r"No space left|Errno 28|WinError 112",
        "Não há espaço suficiente no disco.",
    ),
    (
        r"Permission denied|Errno 13|WinError 5\b",
        "Sem permissão para gravar na pasta de destino.",
    ),
    (
        r"getaddrinfo|Failed to resolve|timed out|Connection|Network is unreachable",
        "Não foi possível conectar ao site. Verifique a internet e tente de novo.",
    ),
)


def traduzir_erro(linha: str) -> str:
    """Devolve a mensagem clara do erro ou, se ele for desconhecido, o texto original."""
    for padrao, mensagem in TRADUCOES:
        if re.search(padrao, linha, re.IGNORECASE):
            return mensagem

    return f"O yt-dlp falhou: {linha.removeprefix('ERROR:').strip()}"
