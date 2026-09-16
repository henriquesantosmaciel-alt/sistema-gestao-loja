"""
loja_avancada.py - Caixa, financeiro, pedidos/orcamentos, fiscal (homologacao)
e utilidades de empresa/backup para o LojaOS.
"""
from datetime import datetime
from pathlib import Path
import shutil

from database import get_connection
from validators import ValidationError, validar_texto_obrigatorio, validar_numero_positivo, validar_inteiro_positivo


def caixa_aberto():
    with get_connection() as c:
        return c.execute("SELECT * FROM caixas WHERE status = 'aberto' ORDER BY id DESC LIMIT 1").fetchone()


def abrir_caixa(usuario, saldo_inicial):
    if caixa_aberto():
        raise ValidationError("Ja existe um caixa aberto.")
    saldo_inicial = validar_numero_positivo(saldo_inicial or 0, "saldo inicial")
    with get_connection() as c:
        return c.execute(
            "INSERT INTO caixas (usuario, saldo_inicial) VALUES (?, ?)", (usuario, saldo_inicial)
        ).lastrowid


def movimentar_caixa(caixa_id, tipo, valor, descricao, usuario):
    if tipo not in {"entrada", "saida", "sangria", "suprimento"}:
        raise ValidationError("Tipo de movimentacao invalido.")
    if not caixa_id:
        raise ValidationError("Abra o caixa antes de registrar movimentacoes.")
    valor = validar_numero_positivo(valor, "valor", permitir_zero=False)
    descricao = validar_texto_obrigatorio(descricao, "descricao", tamanho_maximo=200)
    with get_connection() as c:
        c.execute(
            "INSERT INTO movimentacoes_caixa (caixa_id, tipo, descricao, valor, usuario) VALUES (?, ?, ?, ?, ?)",
            (caixa_id, tipo, descricao, valor, usuario),
        )


def resumo_caixa(caixa_id):
    with get_connection() as c:
        caixa = c.execute("SELECT * FROM caixas WHERE id = ?", (caixa_id,)).fetchone()
        mov = c.execute(
            "SELECT * FROM movimentacoes_caixa WHERE caixa_id = ? ORDER BY data DESC", (caixa_id,)
        ).fetchall()
    if not caixa:
        return None, [], 0
    entradas = sum(m["valor"] for m in mov if m["tipo"] in ("entrada", "suprimento"))
    saidas = sum(m["valor"] for m in mov if m["tipo"] in ("saida", "sangria"))
    esperado = caixa["saldo_inicial"] + entradas - saidas
    return caixa, mov, esperado


def fechar_caixa(caixa_id, saldo_final, observacao=None):
    caixa, _, esperado = resumo_caixa(caixa_id)
    if not caixa:
        raise ValidationError("Caixa nao encontrado.")
    saldo_final = validar_numero_positivo(saldo_final, "saldo final")
    with get_connection() as c:
        c.execute(
            """UPDATE caixas SET fechamento = CURRENT_TIMESTAMP, saldo_final_informado = ?,
               saldo_esperado = ?, diferenca = ?, status = 'fechado', observacao = ? WHERE id = ?""",
            (saldo_final, esperado, saldo_final - esperado, observacao, caixa_id),
        )


def historico_caixas(limite=30):
    with get_connection() as c:
        return c.execute("SELECT * FROM caixas ORDER BY abertura DESC LIMIT ?", (limite,)).fetchall()


def criar_conta(tipo, descricao, valor, vencimento=None, categoria=None, entidade=None, observacao=None):
    if tipo not in {"pagar", "receber"}:
        raise ValidationError("Tipo de conta invalido.")
    descricao = validar_texto_obrigatorio(descricao, "descricao")
    valor = validar_numero_positivo(valor, "valor", permitir_zero=False)
    with get_connection() as c:
        return c.execute(
            """INSERT INTO contas_financeiras (tipo, descricao, categoria, valor, vencimento, entidade, observacao)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tipo, descricao, categoria or None, valor, vencimento or None, entidade or None, observacao or None),
        ).lastrowid


def listar_contas(status=None, tipo=None):
    query = """SELECT *, CASE WHEN status = 'aberta' AND vencimento IS NOT NULL AND vencimento < date('now')
               THEN 'vencida' ELSE status END AS situacao FROM contas_financeiras WHERE 1=1"""
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if tipo:
        query += " AND tipo = ?"
        params.append(tipo)
    query += " ORDER BY vencimento IS NULL, vencimento"
    with get_connection() as c:
        return c.execute(query, params).fetchall()


def baixar_conta(conta_id):
    with get_connection() as c:
        c.execute("UPDATE contas_financeiras SET status = 'paga', pagamento = date('now') WHERE id = ?", (conta_id,))


def resumo_financeiro():
    with get_connection() as c:
        pagar = c.execute(
            "SELECT COALESCE(SUM(valor),0) t FROM contas_financeiras WHERE tipo='pagar' AND status='aberta'"
        ).fetchone()["t"]
        receber = c.execute(
            "SELECT COALESCE(SUM(valor),0) t FROM contas_financeiras WHERE tipo='receber' AND status='aberta'"
        ).fetchone()["t"]
        vencidas = c.execute(
            "SELECT COUNT(*) n FROM contas_financeiras WHERE status='aberta' AND vencimento < date('now')"
        ).fetchone()["n"]
    return {"a_pagar": pagar, "a_receber": receber, "vencidas": vencidas}


def criar_pedido(cliente_id, tipo, validade, observacao, itens):
    if tipo not in {"orcamento", "pedido"}:
        raise ValidationError("Tipo de pedido invalido.")
    if not itens:
        raise ValidationError("Adicione ao menos um item ao pedido.")

    processados = []
    total = 0
    with get_connection() as c:
        for item in itens:
            produto_id = int(item["produto_id"])
            quantidade = validar_inteiro_positivo(item["quantidade"], "quantidade", permitir_zero=False)
            produto = c.execute("SELECT * FROM produtos WHERE id = ? AND ativo = 1", (produto_id,)).fetchone()
            if not produto:
                raise ValidationError("Produto invalido no pedido.")
            preco = produto["preco_promocional"] or produto["preco_venda"]
            subtotal = round(preco * quantidade, 2)
            total += subtotal
            processados.append((produto_id, quantidade, preco, subtotal))

        pedido_id = c.execute(
            """INSERT INTO pedidos (cliente_id, tipo, status, validade, total, observacao)
               VALUES (?, ?, 'aberto', ?, ?, ?)""",
            (cliente_id or None, tipo, validade or None, round(total, 2), observacao or None),
        ).lastrowid

        c.executemany(
            """INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal)
               VALUES (?, ?, ?, ?, ?)""",
            [(pedido_id, *p) for p in processados],
        )
    return pedido_id


def listar_pedidos():
    with get_connection() as c:
        return c.execute(
            """SELECT p.*, COALESCE(cl.nome, 'Consumidor final') AS cliente_nome
               FROM pedidos p LEFT JOIN clientes cl ON cl.id = p.cliente_id
               ORDER BY p.criado_em DESC"""
        ).fetchall()


def detalhes_pedido(pedido_id):
    with get_connection() as c:
        pedido = c.execute(
            """SELECT p.*, COALESCE(cl.nome, 'Consumidor final') AS cliente_nome
               FROM pedidos p LEFT JOIN clientes cl ON cl.id = p.cliente_id WHERE p.id = ?""",
            (pedido_id,),
        ).fetchone()
        itens = c.execute(
            """SELECT ip.*, pr.nome AS produto_nome FROM itens_pedido ip
               JOIN produtos pr ON pr.id = ip.produto_id WHERE ip.pedido_id = ?""",
            (pedido_id,),
        ).fetchall()
    return pedido, itens


def atualizar_status_pedido(pedido_id, status):
    if status not in {"aberto", "convertido", "cancelado"}:
        raise ValidationError("Status invalido.")
    with get_connection() as c:
        c.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def obter_empresa():
    with get_connection() as c:
        return c.execute("SELECT * FROM empresa WHERE id = 1").fetchone()


def salvar_empresa(dados):
    campos = ["razao_social", "nome_fantasia", "cnpj", "inscricao_estadual", "endereco",
              "cidade", "uf", "cep", "regime_tributario", "ambiente_fiscal"]
    valores = [dados.get(c) or None for c in campos]
    with get_connection() as c:
        c.execute("INSERT OR IGNORE INTO empresa (id) VALUES (1)")
        c.execute(f"UPDATE empresa SET {', '.join(f'{x} = ?' for x in campos)} WHERE id = 1", valores)


def criar_nota_homologacao(venda_id, tipo="NFC-e"):
    if tipo not in {"NFC-e", "NF-e"}:
        raise ValidationError("Tipo fiscal invalido.")
    with get_connection() as c:
        venda = c.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,)).fetchone()
        if not venda:
            raise ValidationError("Venda nao encontrada.")
        xml = (
            f'<nota ambiente="homologacao" semValorFiscal="true">'
            f'<venda>{venda_id}</venda><total>{venda["total"]:.2f}</total>'
            f'<emitido_em>{datetime.now().isoformat()}</emitido_em></nota>'
        )
        return c.execute(
            "INSERT INTO notas_fiscais (venda_id, tipo, status, xml) VALUES (?, ?, 'rascunho_homologacao', ?)",
            (venda_id, tipo, xml),
        ).lastrowid


def listar_notas():
    with get_connection() as c:
        return c.execute(
            """SELECT nf.*, v.total AS venda_total FROM notas_fiscais nf
               LEFT JOIN vendas v ON v.id = nf.venda_id ORDER BY nf.criado_em DESC"""
        ).fetchall()


def registrar_auditoria(usuario, acao, entidade, entidade_id=None, detalhes=None):
    with get_connection() as c:
        c.execute(
            "INSERT INTO auditoria (usuario, acao, entidade, entidade_id, detalhes) VALUES (?, ?, ?, ?, ?)",
            (usuario, acao, entidade, entidade_id, detalhes),
        )


def listar_auditoria(limite=100):
    with get_connection() as c:
        return c.execute("SELECT * FROM auditoria ORDER BY criado_em DESC LIMIT ?", (limite,)).fetchall()


def criar_backup():
    from config import DB_NAME
    origem = Path(DB_NAME)
    if not origem.exists():
        raise ValidationError("Banco de dados ainda nao foi criado.")
    pasta = Path("backups")
    pasta.mkdir(exist_ok=True)
    destino = pasta / f"lojaos_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(origem, destino)
    return destino.name
