"""
vendas.py - Módulo de registro e processamento de vendas
"""
from database import get_connection
from estoque import buscar_produto, dar_baixa_estoque


def registrar_venda(itens, cliente_id=None, forma_pagamento="dinheiro"):
    """
    itens: lista de dicionários no formato:
        [{"produto_id": 1, "quantidade": 2}, ...]
    """
    if not itens:
        raise ValueError("A venda precisa ter ao menos um item.")

    total = 0
    itens_processados = []

    for item in itens:
        produto = buscar_produto(item["produto_id"])
        if not produto:
            raise ValueError(f"Produto {item['produto_id']} não encontrado.")
        quantidade = item["quantidade"]
        if produto["quantidade"] < quantidade:
            raise ValueError(f"Estoque insuficiente para o produto {produto['nome']}.")

        preco_unitario = produto["preco_venda"]
        subtotal = preco_unitario * quantidade
        total += subtotal
        itens_processados.append({
            "produto_id": produto["id"],
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "subtotal": subtotal,
        })

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vendas (cliente_id, total, forma_pagamento) VALUES (?, ?, ?)",
            (cliente_id, total, forma_pagamento),
        )
        venda_id = cursor.lastrowid

        for item in itens_processados:
            cursor.execute("""
                INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (venda_id, item["produto_id"], item["quantidade"], item["preco_unitario"], item["subtotal"]))

        cursor.execute(
            "INSERT INTO movimentacoes_caixa (tipo, descricao, valor) VALUES (?, ?, ?)",
            ("entrada", f"Venda #{venda_id}", total),
        )

    for item in itens_processados:
        dar_baixa_estoque(item["produto_id"], item["quantidade"])

    return venda_id, total


def listar_vendas():
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM vendas ORDER BY data DESC")
        return cursor.fetchall()


def detalhes_venda(venda_id):
    with get_connection() as conn:
        venda = conn.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,)).fetchone()
        itens = conn.execute("""
            SELECT iv.*, p.nome AS produto_nome
            FROM itens_venda iv
            JOIN produtos p ON p.id = iv.produto_id
            WHERE iv.venda_id = ?
        """, (venda_id,)).fetchall()
        return venda, itens


def cancelar_venda(venda_id):
    with get_connection() as conn:
        itens = conn.execute(
            "SELECT * FROM itens_venda WHERE venda_id = ?", (venda_id,)
        ).fetchall()
        for item in itens:
            conn.execute(
                "UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        venda = conn.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,)).fetchone()
        if venda:
            conn.execute(
                "INSERT INTO movimentacoes_caixa (tipo, descricao, valor) VALUES (?, ?, ?)",
                ("estorno", f"Cancelamento da venda #{venda_id}", -venda["total"]),
            )
        conn.execute("DELETE FROM itens_venda WHERE venda_id = ?", (venda_id,))
        conn.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
