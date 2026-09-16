"""
auth.py - Autenticacao e controle de acesso de usuarios.
Usa werkzeug.security (PBKDF2) em vez de hash caseiro.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection
from validators import validar_texto_obrigatorio, validar_senha_forte, ValidationError

PAPEIS_VALIDOS = {"admin", "vendedor"}


def criar_usuario(username, senha, nome=None, papel="admin"):
    username = validar_texto_obrigatorio(username, "usuario", tamanho_maximo=50)
    validar_senha_forte(senha)
    if papel not in PAPEIS_VALIDOS:
        papel = "vendedor"

    senha_hash = generate_password_hash(senha)
    with get_connection() as conn:
        cursor = conn.cursor()
        existente = conn.execute(
            "SELECT id FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
        if existente:
            raise ValidationError("Ja existe um usuario com este nome.")
        cursor.execute(
            "INSERT INTO usuarios (username, senha_hash, nome, papel) VALUES (?, ?, ?, ?)",
            (username, senha_hash, nome or username, papel),
        )
        return cursor.lastrowid


def autenticar(username, senha):
    with get_connection() as conn:
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE username = ? AND ativo = 1", (username,)
        ).fetchone()
    if not usuario:
        return None
    if check_password_hash(usuario["senha_hash"], senha):
        return usuario
    return None


def usuario_existe():
    with get_connection() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"]
    return n > 0


def listar_usuarios():
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, username, nome, papel, ativo, criado_em FROM usuarios ORDER BY username"
        )
        return cursor.fetchall()


def buscar_usuario_por_nome(username):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()


def alterar_papel(usuario_id, papel):
    if papel not in PAPEIS_VALIDOS:
        raise ValidationError("Papel invalido.")
    with get_connection() as conn:
        conn.execute("UPDATE usuarios SET papel = ? WHERE id = ?", (papel, usuario_id))


def desativar_usuario(usuario_id):
    with get_connection() as conn:
        conn.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (usuario_id,))


def tem_permissao(papel, area):
    from config import PERMISSOES
    return area in PERMISSOES.get(papel, set())
