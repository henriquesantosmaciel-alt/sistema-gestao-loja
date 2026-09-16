"""
fornecedores.py - Modulo de gestao de fornecedores e compras
"""
from database import get_connection
from estoque import repor_estoque


def cadastrar_fornecedor(nome, telefone=None, email=None, cnpj=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fornecedores (nome, telefone, email, cnpj) VALUES (?, ?, ?, ?)",
            (nome, telefone, email, cnpj),
        )
        return cursor.lastrowid


def listar_fornecedores():
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM fornecedores ORDER BY nome")
        return cursor.fetchall()


def remover_fornecedor(fornecedor_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM fornecedores WHERE id = ?", (fornecedor_id,))


def registrar_compra(produto_id, quantidade, preco_unitario, fornecedor_id=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO compras (fornecedor_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
        """, (fornecedor_id, produto_id, quantidade, preco_unitario))
        compra_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO movimentacoes_caixa (tipo, descricao, valor) VALUES (?, ?, ?)",
            ("saida", f"Compra #{compra_id}", quantidade * preco_unitario),
        )
    repor_estoque(produto_id, quantidade)
    return compra_id


def listar_compras():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT c.id, c.quantidade, c.preco_unitario, c.data,
                   p.nome AS produto_nome, f.nome AS fornecedor_nome
            FROM compras c
            JOIN produtos p ON p.id = c.produto_id
            LEFT JOIN fornecedores f ON f.id = c.fornecedor_id
            ORDER BY c.data DESC
        """)
        return cursor.fetchall()
