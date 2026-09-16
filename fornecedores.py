"""
fornecedores.py - Modulo de gestao de fornecedores e compras
"""
from database import get_connection
from estoque import repor_estoque
from validators import validar_texto_obrigatorio, validar_email, validar_inteiro_positivo, validar_numero_positivo, ValidationError


def cadastrar_fornecedor(nome, telefone=None, email=None, cnpj=None):
    nome = validar_texto_obrigatorio(nome, "nome")
    email = validar_email(email, obrigatorio=False)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fornecedores (nome, telefone, email, cnpj) VALUES (?, ?, ?, ?)",
            (nome, (telefone or "").strip() or None, email, (cnpj or "").strip() or None),
        )
        return cursor.lastrowid


def listar_fornecedores(busca=None):
    query = "SELECT * FROM fornecedores"
    params = []
    if busca:
        query += " WHERE nome LIKE ? OR cnpj LIKE ?"
        termo = f"%{busca}%"
        params.extend([termo, termo])
    query += " ORDER BY nome"
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def remover_fornecedor(fornecedor_id):
    with get_connection() as conn:
        conn.execute("UPDATE compras SET fornecedor_id = NULL WHERE fornecedor_id = ?", (fornecedor_id,))
        conn.execute("DELETE FROM fornecedores WHERE id = ?", (fornecedor_id,))


def registrar_compra(produto_id, quantidade, preco_unitario, fornecedor_id=None):
    quantidade = validar_inteiro_positivo(quantidade, "quantidade", permitir_zero=False)
    preco_unitario = validar_numero_positivo(preco_unitario, "preco unitario", permitir_zero=False)

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


def listar_compras(limite=200):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT c.id, c.quantidade, c.preco_unitario, c.data,
                   p.nome AS produto_nome, f.nome AS fornecedor_nome
            FROM compras c
            JOIN produtos p ON p.id = c.produto_id
            LEFT JOIN fornecedores f ON f.id = c.fornecedor_id
            ORDER BY c.data DESC
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()
