"""Tradução dos erros do yt-dlp em mensagens claras para quem usa o programa."""

import re

ERRO_EXCESSO_DE_ACESSOS = r"HTTP Error 429"
ERRO_DO_SERVIDOR = r"HTTP Error 5\d\d"
ERRO_DE_DRM = r"\bDRM\b"
ERRO_DE_DISCO = r"No space left|Errno 28|WinError 112"
ERRO_DE_PERMISSAO = r"Permission denied|Errno 13|WinError 5\b"
ERRO_DE_REDE = r"getaddrinfo|Failed to resolve|timed out|Connection|Network is unreachable"

# Erros que uma versão nova do yt-dlp não resolveria. Todos os outros podem ser
# sintoma de um yt-dlp desatualizado: os sites mudam, e a versão antiga passa a
# receber 403, "vídeo indisponível" ou pedido de login em vídeos públicos.
SEM_RELACAO_COM_A_VERSAO = (
    ERRO_EXCESSO_DE_ACESSOS,
    ERRO_DO_SERVIDOR,
    ERRO_DE_DRM,
    ERRO_DE_DISCO,
    ERRO_DE_PERMISSAO,
    ERRO_DE_REDE,
)

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
        ERRO_EXCESSO_DE_ACESSOS,
        "O site recusou o pedido por excesso de acessos. Tente mais tarde.",
    ),
    (
        ERRO_DO_SERVIDOR,
        "O site está com problemas no momento. Tente mais tarde.",
    ),
    (
        ERRO_DE_DRM,
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
        "O site recusou o download (erro 403). Tente de novo mais tarde.",
    ),
    (
        r"unavailable|not available|HTTP Error 404|has been removed",
        "Este vídeo não está disponível: ele pode ter sido removido ou o link "
        "pode estar errado.",
    ),
    (
        ERRO_DE_DISCO,
        "Não há espaço suficiente no disco.",
    ),
    (
        ERRO_DE_PERMISSAO,
        "Sem permissão para gravar na pasta de destino.",
    ),
    (
        ERRO_DE_REDE,
        "Não foi possível conectar ao site. Verifique a internet e tente de novo.",
    ),
)


def _encontrar(linha: str) -> tuple[str, str] | None:
    """Devolve o primeiro par (padrão, mensagem) que combina com a linha."""
    for padrao, mensagem in TRADUCOES:
        if re.search(padrao, linha, re.IGNORECASE):
            return padrao, mensagem
    return None


def atualizar_pode_resolver(linha: str) -> bool:
    """Diz se o erro pode ser sintoma de um yt-dlp desatualizado.

    Um erro desconhecido conta como possível sintoma: tentar atualizar custa
    poucos segundos, e deixar de tentar custa o download.
    """
    encontrado = _encontrar(linha)
    return encontrado is None or encontrado[0] not in SEM_RELACAO_COM_A_VERSAO


def traduzir_erro(linha: str) -> str:
    """Devolve a mensagem clara do erro ou, se ele for desconhecido, o texto original."""
    encontrado = _encontrar(linha)
    if encontrado is not None:
        return encontrado[1]

    return f"O yt-dlp falhou: {linha.removeprefix('ERROR:').strip()}"
