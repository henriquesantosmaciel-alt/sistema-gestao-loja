"""
vendas.py - Modulo de registro e processamento de vendas
"""
from database import get_connection
from estoque import buscar_produto, dar_baixa_estoque
from validators import ValidationError

FORMAS_PAGAMENTO_VALIDAS = {"dinheiro", "cartao", "pix", "fiado"}


def registrar_venda(itens, cliente_id=None, forma_pagamento="dinheiro", vendedor=None):
    if not itens:
        raise ValidationError("A venda precisa ter ao menos um item.")
    if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
        forma_pagamento = "dinheiro"

    total = 0
    itens_processados = []
    produtos_vistos = set()

    for item in itens:
        try:
            produto_id = int(item["produto_id"])
            quantidade = int(item["quantidade"])
        except (TypeError, ValueError, KeyError):
            raise ValidationError("Item de venda invalido.")

        if quantidade <= 0:
            raise ValidationError("A quantidade de cada item deve ser maior que zero.")
        if produto_id in produtos_vistos:
            raise ValidationError("Um mesmo produto foi informado mais de uma vez na venda.")
        produtos_vistos.add(produto_id)

        produto = buscar_produto(produto_id)
        if not produto:
            raise ValidationError(f"Produto de ID {produto_id} nao encontrado.")
        if produto["quantidade"] < quantidade:
            raise ValidationError(
                f"Estoque insuficiente para '{produto['nome']}' (disponivel: {produto['quantidade']})."
            )

        preco_unitario = produto["preco_venda"]
        subtotal = round(preco_unitario * quantidade, 2)
        total += subtotal
        itens_processados.append({
            "produto_id": produto["id"],
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "subtotal": subtotal,
        })

    total = round(total, 2)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vendas (cliente_id, total, forma_pagamento, vendedor) VALUES (?, ?, ?, ?)",
            (cliente_id, total, forma_pagamento, vendedor),
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


def listar_vendas(limite=200, busca_cliente=None):
    query = """
        SELECT v.*, c.nome AS cliente_nome
        FROM vendas v
        LEFT JOIN clientes c ON c.id = v.cliente_id
        WHERE 1=1
    """
    params = []
    if busca_cliente:
        query += " AND c.nome LIKE ?"
        params.append(f"%{busca_cliente}%")
    query += " ORDER BY v.data DESC LIMIT ?"
    params.append(limite)
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def detalhes_venda(venda_id):
    with get_connection() as conn:
        venda = conn.execute("""
            SELECT v.*, c.nome AS cliente_nome
            FROM vendas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            WHERE v.id = ?
        """, (venda_id,)).fetchone()
        itens = conn.execute("""
            SELECT iv.*, p.nome AS produto_nome
            FROM itens_venda iv
            JOIN produtos p ON p.id = iv.produto_id
            WHERE iv.venda_id = ?
        """, (venda_id,)).fetchall()
        return venda, itens


def cancelar_venda(venda_id):
    with get_connection() as conn:
        venda = conn.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,)).fetchone()
        if not venda:
            raise ValidationError("Venda nao encontrada.")
        if venda["status"] == "cancelada":
            raise ValidationError("Esta venda ja foi cancelada.")

        itens = conn.execute(
            "SELECT * FROM itens_venda WHERE venda_id = ?", (venda_id,)
        ).fetchall()
        for item in itens:
            conn.execute(
                "UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        conn.execute(
            "INSERT INTO movimentacoes_caixa (tipo, descricao, valor) VALUES (?, ?, ?)",
            ("estorno", f"Cancelamento da venda #{venda_id}", -venda["total"]),
        )
        conn.execute("UPDATE vendas SET status = 'cancelada' WHERE id = ?", (venda_id,))
