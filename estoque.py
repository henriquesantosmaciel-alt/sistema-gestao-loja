"""
estoque.py - Modulo de controle de estoque
"""
from database import get_connection
from validators import validar_texto_obrigatorio, validar_numero_positivo, validar_inteiro_positivo, ValidationError


def cadastrar_produto(nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo=5):
    nome = validar_texto_obrigatorio(nome, "nome")
    preco_custo = validar_numero_positivo(preco_custo or 0, "preco de custo")
    preco_venda = validar_numero_positivo(preco_venda, "preco de venda")
    if preco_venda <= 0:
        raise ValidationError("O preco de venda deve ser maior que zero.")
    quantidade = validar_inteiro_positivo(quantidade or 0, "quantidade")
    estoque_minimo = validar_inteiro_positivo(estoque_minimo or 5, "estoque minimo")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO produtos (nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, (categoria or "").strip() or None, preco_custo, preco_venda, quantidade, estoque_minimo))
        return cursor.lastrowid


def atualizar_produto(produto_id, **campos):
    if not campos:
        return
    permitidos = {"nome", "categoria", "preco_custo", "preco_venda", "quantidade", "estoque_minimo", "ativo"}
    campos = {k: v for k, v in campos.items() if k in permitidos}
    if not campos:
        return
    colunas = ", ".join(f"{chave} = ?" for chave in campos)
    valores = list(campos.values()) + [produto_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE produtos SET {colunas} WHERE id = ?", valores)


def remover_produto(produto_id):
    with get_connection() as conn:
        em_uso = conn.execute(
            "SELECT COUNT(*) AS n FROM itens_venda WHERE produto_id = ?", (produto_id,)
        ).fetchone()["n"]
        if em_uso > 0:
            conn.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,))
        else:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def listar_produtos(apenas_ativos=True, busca=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if apenas_ativos:
        query += " AND ativo = 1"
    if busca:
        query += " AND (nome LIKE ? OR categoria LIKE ?)"
        termo = f"%{busca}%"
        params.extend([termo, termo])
    query += " ORDER BY nome"
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def buscar_produto(produto_id):
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        return cursor.fetchone()


def dar_baixa_estoque(produto_id, quantidade):
    produto = buscar_produto(produto_id)
    if not produto:
        raise ValidationError("Produto nao encontrado.")
    if produto["quantidade"] < quantidade:
        raise ValidationError(f"Estoque insuficiente para '{produto['nome']}' (disponivel: {produto['quantidade']}).")
    with get_connection() as conn:
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
            (quantidade, produto_id),
        )


def repor_estoque(produto_id, quantidade):
    quantidade = validar_inteiro_positivo(quantidade, "quantidade", permitir_zero=False)
    with get_connection() as conn:
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?",
            (quantidade, produto_id),
        )


def produtos_estoque_baixo():
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM produtos WHERE ativo = 1 AND quantidade <= estoque_minimo ORDER BY quantidade ASC"
        )
        return cursor.fetchall()


def valor_total_estoque():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantidade * preco_custo), 0) AS valor FROM produtos WHERE ativo = 1"
        ).fetchone()
        return row["valor"]
