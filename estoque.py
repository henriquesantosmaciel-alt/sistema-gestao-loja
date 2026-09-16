"""
estoque.py - Módulo de controle de estoque
"""
from database import get_connection


def cadastrar_produto(nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo=5):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO produtos (nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo))
        return cursor.lastrowid


def atualizar_produto(produto_id, **campos):
    if not campos:
        return
    colunas = ", ".join(f"{chave} = ?" for chave in campos)
    valores = list(campos.values()) + [produto_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE produtos SET {colunas} WHERE id = ?", valores)


def remover_produto(produto_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def listar_produtos():
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM produtos ORDER BY nome")
        return cursor.fetchall()


def buscar_produto(produto_id):
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        return cursor.fetchone()


def dar_baixa_estoque(produto_id, quantidade):
    produto = buscar_produto(produto_id)
    if not produto:
        raise ValueError("Produto não encontrado.")
    if produto["quantidade"] < quantidade:
        raise ValueError("Estoque insuficiente.")
    with get_connection() as conn:
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
            (quantidade, produto_id),
        )


def repor_estoque(produto_id, quantidade):
    with get_connection() as conn:
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?",
            (quantidade, produto_id),
        )


def produtos_estoque_baixo():
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM produtos WHERE quantidade <= estoque_minimo ORDER BY quantidade ASC"
        )
        return cursor.fetchall()
