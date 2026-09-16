"""
clientes.py - Módulo de gestão de clientes
"""
from database import get_connection


def cadastrar_cliente(nome, telefone=None, email=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, telefone, email) VALUES (?, ?, ?)",
            (nome, telefone, email),
        )
        return cursor.lastrowid


def listar_clientes():
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM clientes ORDER BY nome")
        return cursor.fetchall()


def buscar_cliente(cliente_id):
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        return cursor.fetchone()


def historico_compras(cliente_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT v.id, v.data, v.total, v.forma_pagamento
            FROM vendas v
            WHERE v.cliente_id = ?
            ORDER BY v.data DESC
        """, (cliente_id,))
        return cursor.fetchall()


def atualizar_cliente(cliente_id, **campos):
    if not campos:
        return
    colunas = ", ".join(f"{chave} = ?" for chave in campos)
    valores = list(campos.values()) + [cliente_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE clientes SET {colunas} WHERE id = ?", valores)


def remover_cliente(cliente_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
