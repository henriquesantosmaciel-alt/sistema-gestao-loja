"""
relatorios.py - Modulo de relatorios gerenciais
"""
import csv
import io
from datetime import date, timedelta
from database import get_connection


def faturamento_periodo(data_inicio, data_fim):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT COALESCE(SUM(total), 0) as faturamento, COUNT(*) as qtd_vendas
            FROM vendas
            WHERE date(data) BETWEEN date(?) AND date(?) AND status = 'concluida'
        """, (data_inicio, data_fim))
        return cursor.fetchone()


def produtos_mais_vendidos(limite=10):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT p.nome, SUM(iv.quantidade) AS total_vendido, SUM(iv.subtotal) AS receita
            FROM itens_venda iv
            JOIN produtos p ON p.id = iv.produto_id
            JOIN vendas v ON v.id = iv.venda_id
            WHERE v.status = 'concluida'
            GROUP BY p.id
            ORDER BY total_vendido DESC
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()


def relatorio_estoque_critico():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, nome, quantidade, estoque_minimo
            FROM produtos
            WHERE ativo = 1 AND quantidade <= estoque_minimo
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
            WHERE date(v.data) BETWEEN date(?) AND date(?) AND v.status = 'concluida'
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
            WHERE v.status = 'concluida'
            GROUP BY c.id
            ORDER BY total_gasto DESC
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()


def vendas_por_dia(dias=7):
    hoje = date.today()
    inicio = hoje - timedelta(days=dias - 1)
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT date(data) AS dia, COALESCE(SUM(total), 0) AS total
            FROM vendas
            WHERE date(data) BETWEEN date(?) AND date(?) AND status = 'concluida'
            GROUP BY date(data)
        """, (inicio.isoformat(), hoje.isoformat()))
        mapa = {row["dia"]: row["total"] for row in cursor.fetchall()}

    resultado = []
    for i in range(dias):
        dia = (inicio + timedelta(days=i)).isoformat()
        resultado.append({"dia": dia, "total": mapa.get(dia, 0)})
    return resultado


def vendas_por_forma_pagamento():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT forma_pagamento, COUNT(*) AS qtd, COALESCE(SUM(total), 0) AS total
            FROM vendas
            WHERE status = 'concluida'
            GROUP BY forma_pagamento
        """)
        return cursor.fetchall()


def resumo_dashboard():
    hoje = date.today().isoformat()
    inicio_mes = date.today().replace(day=1).isoformat()

    fat_hoje = faturamento_periodo(hoje, hoje)
    fat_mes = faturamento_periodo(inicio_mes, hoje)
    estoque_critico = relatorio_estoque_critico()

    with get_connection() as conn:
        total_clientes = conn.execute("SELECT COUNT(*) AS n FROM clientes").fetchone()["n"]
        total_produtos = conn.execute("SELECT COUNT(*) AS n FROM produtos WHERE ativo = 1").fetchone()["n"]
        total_vendas = conn.execute("SELECT COUNT(*) AS n FROM vendas WHERE status = 'concluida'").fetchone()["n"]

    return {
        "faturamento_hoje": fat_hoje["faturamento"],
        "vendas_hoje": fat_hoje["qtd_vendas"],
        "faturamento_mes": fat_mes["faturamento"],
        "vendas_mes": fat_mes["qtd_vendas"],
        "produtos_estoque_baixo": len(estoque_critico),
        "total_clientes": total_clientes,
        "total_produtos": total_produtos,
        "total_vendas": total_vendas,
    }


def exportar_vendas_csv(data_inicio, data_fim):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT v.id, v.data, v.total, v.forma_pagamento, v.status,
                   COALESCE(c.nome, 'Consumidor final') AS cliente
            FROM vendas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            WHERE date(v.data) BETWEEN date(?) AND date(?)
            ORDER BY v.data
        """, (data_inicio, data_fim)).fetchall()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ID", "Data", "Cliente", "Total", "Forma de Pagamento", "Status"])
    for row in rows:
        writer.writerow([row["id"], row["data"], row["cliente"], f"{row['total']:.2f}",
                          row["forma_pagamento"], row["status"]])
    buffer.seek(0)
    return buffer
