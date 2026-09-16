"""
clientes.py - Modulo de gestao de clientes
"""
from database import get_connection
from validators import validar_texto_obrigatorio, validar_email


def cadastrar_cliente(nome, telefone=None, email=None):
    nome = validar_texto_obrigatorio(nome, "nome")
    email = validar_email(email, obrigatorio=False)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, telefone, email) VALUES (?, ?, ?)",
            (nome, (telefone or "").strip() or None, email),
        )
        return cursor.lastrowid


def listar_clientes(busca=None):
    query = "SELECT * FROM clientes"
    params = []
    if busca:
        query += " WHERE nome LIKE ? OR telefone LIKE ? OR email LIKE ?"
        termo = f"%{busca}%"
        params.extend([termo, termo, termo])
    query += " ORDER BY nome"
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def buscar_cliente(cliente_id):
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        return cursor.fetchone()


def historico_compras(cliente_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT v.id, v.data, v.total, v.forma_pagamento, v.status
            FROM vendas v
            WHERE v.cliente_id = ?
            ORDER BY v.data DESC
        """, (cliente_id,))
        return cursor.fetchall()


def estatisticas_cliente(cliente_id):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS qtd_compras, COALESCE(SUM(total), 0) AS total_gasto,
                   COALESCE(AVG(total), 0) AS ticket_medio
            FROM vendas WHERE cliente_id = ? AND status = 'concluida'
        """, (cliente_id,)).fetchone()
        return dict(row)


def atualizar_cliente(cliente_id, **campos):
    if not campos:
        return
    permitidos = {"nome", "telefone", "email"}
    campos = {k: v for k, v in campos.items() if k in permitidos}
    if not campos:
        return
    colunas = ", ".join(f"{chave} = ?" for chave in campos)
    valores = list(campos.values()) + [cliente_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE clientes SET {colunas} WHERE id = ?", valores)


def remover_cliente(cliente_id):
    with get_connection() as conn:
        conn.execute("UPDATE vendas SET cliente_id = NULL WHERE cliente_id = ?", (cliente_id,))
        conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
