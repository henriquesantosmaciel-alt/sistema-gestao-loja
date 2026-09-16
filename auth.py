"""
auth.py - Autenticacao simples de usuarios (hash de senha com salt)
"""
import hashlib
import os
from database import get_connection


def _hash_senha(senha, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + senha).encode("utf-8")).hexdigest()
    return f"{salt}${h}"


def verificar_senha(senha, senha_hash):
    salt, _ = senha_hash.split("$")
    return _hash_senha(senha, salt) == senha_hash


def criar_usuario(username, senha, nome=None):
    senha_hash = _hash_senha(senha)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (username, senha_hash, nome) VALUES (?, ?, ?)",
            (username, senha_hash, nome or username),
        )
        return cursor.lastrowid


def autenticar(username, senha):
    with get_connection() as conn:
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
    if not usuario:
        return None
    if verificar_senha(senha, usuario["senha_hash"]):
        return usuario
    return None


def usuario_existe():
    with get_connection() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"]
    return n > 0
