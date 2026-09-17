"""
seguranca.py - Protecoes leves de aplicacao: limite de tentativas de login
e cabecalhos de seguranca HTTP.
"""
import time
from collections import defaultdict

from config import LOGIN_MAX_TENTATIVAS, LOGIN_BLOQUEIO_SEGUNDOS

_tentativas = defaultdict(list)


def registrar_falha_login(identificador):
    agora = time.time()
    _tentativas[identificador] = [t for t in _tentativas[identificador] if agora - t < LOGIN_BLOQUEIO_SEGUNDOS]
    _tentativas[identificador].append(agora)


def limpar_tentativas(identificador):
    _tentativas.pop(identificador, None)


def login_bloqueado(identificador):
    agora = time.time()
    tentativas = [t for t in _tentativas.get(identificador, []) if agora - t < LOGIN_BLOQUEIO_SEGUNDOS]
    _tentativas[identificador] = tentativas
    return len(tentativas) >= LOGIN_MAX_TENTATIVAS


def segundos_restantes_bloqueio(identificador):
    tentativas = _tentativas.get(identificador, [])
    if not tentativas:
        return 0
    mais_antiga = min(tentativas)
    restante = LOGIN_BLOQUEIO_SEGUNDOS - (time.time() - mais_antiga)
    return max(0, int(restante))


def aplicar_cabecalhos_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:;"
    )
    return response
