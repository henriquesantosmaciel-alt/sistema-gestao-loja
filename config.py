"""
config.py - Configuracoes centralizadas da aplicacao LojaOS
Carrega segredos e parametros sensiveis de variaveis de ambiente.
Se LOJAOS_SECRET_KEY nao for definida, uma chave e gerada uma unica vez
e persistida em disco (instance/secret_key) para que as sessoes dos
usuarios nao sejam invalidadas a cada reinicio do servidor.
"""
import os
import secrets
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.environ.get("LOJAOS_DB", os.path.join(BASE_DIR, "loja.db"))


def _obter_secret_key():
    env_key = os.environ.get("LOJAOS_SECRET_KEY")
    if env_key:
        return env_key

    pasta = Path(BASE_DIR) / "instance"
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / "secret_key"

    if arquivo.exists():
        chave = arquivo.read_text(encoding="utf-8").strip()
        if chave:
            return chave

    chave = secrets.token_hex(32)
    arquivo.write_text(chave, encoding="utf-8")
    return chave


SECRET_KEY = _obter_secret_key()

DEBUG = os.environ.get("LOJAOS_DEBUG", "false").lower() in ("1", "true", "yes")

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get("LOJAOS_HTTPS", "false").lower() in ("1", "true", "yes")

PERMISSOES = {
    "admin": {"estoque", "vendas", "clientes", "fornecedores", "relatorios", "usuarios"},
    "vendedor": {"vendas", "clientes"},
}

# Protecao basica contra tentativas de login por forca bruta
LOGIN_MAX_TENTATIVAS = 5
LOGIN_BLOQUEIO_SEGUNDOS = 60
