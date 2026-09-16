"""
relatorios.py - Módulo de relatórios gerenciais
"""
from database import get_connection


def faturamento_periodo(data_inicio, data_fim):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT COALESCE(SUM(total), 0) as faturamento, COUNT(*) as qtd_vendas
            FROM vendas
            WHERE date(data) BETWEEN date(?) AND date(?)
        """, (data_inicio, data_fim))
        return cursor.fetchone()


def produtos_mais_vendidos(limite=10):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT p.nome, SUM(iv.quantidade) AS total_vendido, SUM(iv.subtotal) AS receita
            FROM itens_venda iv
            JOIN produtos p ON p.id = iv.produto_id
            GROUP BY p.id
            ORDER BY total_vendido DESC
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()


def relatorio_estoque_critico():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT nome, quantidade, estoque_minimo
            FROM produtos
            WHERE quantidade <= estoque_minimo
            ORDER BY quantidade ASC
        """)
        return cursor.fetchall()


def lucro_periodo(data_inicio, data_fim):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                SUM(iv.subtotal) AS receita,
                SUM(iv.quantidade * p.preco_custo) AS custo
            FROM itens_venda iv
            JOIN produtos p ON p.id = iv.produto_id
            JOIN vendas v ON v.id = iv.venda_id
            WHERE date(v.data) BETWEEN date(?) AND date(?)
        """, (data_inicio, data_fim))
        row = cursor.fetchone()
        receita = row["receita"] or 0
        custo = row["custo"] or 0
        return {"receita": receita, "custo": custo, "lucro": receita - custo}


def clientes_top(limite=5):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT c.nome, COUNT(v.id) AS qtd_compras, SUM(v.total) AS total_gasto
            FROM vendas v
            JOIN clientes c ON c.id = v.cliente_id
            GROUP BY c.id
            ORDER BY total_gasto DESC
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()
