"""
config.py - Configuracoes centralizadas da aplicacao
Carrega segredos e parametros sensiveis de variaveis de ambiente,
com valores de desenvolvimento seguros como fallback.
"""
import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.environ.get("LOJAOS_DB", os.path.join(BASE_DIR, "loja.db"))

SECRET_KEY = os.environ.get("LOJAOS_SECRET_KEY") or secrets.token_hex(32)

DEBUG = os.environ.get("LOJAOS_DEBUG", "false").lower() in ("1", "true", "yes")

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get("LOJAOS_HTTPS", "false").lower() in ("1", "true", "yes")

PERMISSOES = {
    "admin": {"estoque", "vendas", "clientes", "fornecedores", "relatorios", "usuarios"},
    "vendedor": {"vendas", "clientes"},
}
