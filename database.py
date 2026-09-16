"""
database.py - Configuracao e modelagem do banco de dados SQLite
Sistema de Gestao de Loja (LojaOS) - inclui modulos avancados:
caixa, financeiro, pedidos/orcamentos, fiscal (homologacao) e auditoria.
"""
import sqlite3
import logging
from contextlib import contextmanager

from config import DB_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lojaos.database")


class DatabaseError(Exception):
    """Erro de acesso ao banco de dados."""


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        logger.error("Erro no banco de dados: %s", exc)
        raise DatabaseError(str(exc)) from exc
    finally:
        conn.close()


def _add_column(conn, table, column, definition):
    cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def inicializar_banco():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            preco_custo REAL NOT NULL DEFAULT 0 CHECK (preco_custo >= 0),
            preco_venda REAL NOT NULL CHECK (preco_venda >= 0),
            quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
            estoque_minimo INTEGER NOT NULL DEFAULT 5 CHECK (estoque_minimo >= 0),
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            documento TEXT,
            endereco TEXT,
            limite_credito REAL DEFAULT 0,
            observacoes TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL DEFAULT 0,
            forma_pagamento TEXT,
            status TEXT NOT NULL DEFAULT 'concluida',
            vendedor TEXT,
            caixa_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (venda_id) REFERENCES vendas (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            abertura TEXT DEFAULT CURRENT_TIMESTAMP,
            fechamento TEXT,
            saldo_inicial REAL NOT NULL DEFAULT 0,
            saldo_final_informado REAL,
            saldo_esperado REAL,
            diferenca REAL,
            status TEXT NOT NULL DEFAULT 'aberto',
            observacao TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caixa_id INTEGER,
            tipo TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            data TEXT DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT,
            FOREIGN KEY (caixa_id) REFERENCES caixas (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            cnpj TEXT,
            endereco TEXT,
            prazo_pagamento INTEGER DEFAULT 0,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor_id INTEGER,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            data TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT,
            papel TEXT NOT NULL DEFAULT 'admin',
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas_financeiras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT,
            valor REAL NOT NULL,
            vencimento TEXT,
            pagamento TEXT,
            status TEXT NOT NULL DEFAULT 'aberta',
            entidade TEXT,
            observacao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            tipo TEXT NOT NULL DEFAULT 'orcamento',
            status TEXT NOT NULL DEFAULT 'aberto',
            validade TEXT,
            total REAL NOT NULL DEFAULT 0,
            observacao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            razao_social TEXT,
            nome_fantasia TEXT,
            cnpj TEXT,
            inscricao_estadual TEXT,
            endereco TEXT,
            cidade TEXT,
            uf TEXT,
            cep TEXT,
            regime_tributario TEXT DEFAULT 'Simples Nacional',
            ambiente_fiscal TEXT DEFAULT 'homologacao'
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            tipo TEXT NOT NULL DEFAULT 'NFC-e',
            numero TEXT,
            status TEXT NOT NULL DEFAULT 'rascunho',
            chave_acesso TEXT,
            xml TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venda_id) REFERENCES vendas (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            acao TEXT NOT NULL,
            entidade TEXT,
            entidade_id INTEGER,
            detalhes TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # IMPORTANTE: migracoes de colunas ANTES de criar indices que as usam,
        # pois tabelas antigas (criadas em versoes anteriores) podem nao ter
        # essas colunas ainda quando "CREATE TABLE IF NOT EXISTS" e ignorado.
        _add_column(conn, "produtos", "sku", "TEXT")
        _add_column(conn, "produtos", "codigo_barras", "TEXT")
        _add_column(conn, "produtos", "marca", "TEXT")
        _add_column(conn, "produtos", "unidade", "TEXT DEFAULT 'UN'")
        _add_column(conn, "produtos", "preco_promocional", "REAL")
        _add_column(conn, "produtos", "ncm", "TEXT")
        _add_column(conn, "produtos", "cest", "TEXT")
        _add_column(conn, "produtos", "cfop", "TEXT")
        _add_column(conn, "produtos", "csosn", "TEXT")
        _add_column(conn, "produtos", "origem", "TEXT DEFAULT '0'")
        _add_column(conn, "clientes", "documento", "TEXT")
        _add_column(conn, "clientes", "endereco", "TEXT")
        _add_column(conn, "clientes", "limite_credito", "REAL DEFAULT 0")
        _add_column(conn, "clientes", "observacoes", "TEXT")
        _add_column(conn, "vendas", "status", "TEXT DEFAULT 'concluida'")
        _add_column(conn, "vendas", "vendedor", "TEXT")
        _add_column(conn, "vendas", "caixa_id", "INTEGER")
        _add_column(conn, "fornecedores", "endereco", "TEXT")
        _add_column(conn, "fornecedores", "prazo_pagamento", "INTEGER DEFAULT 0")
        _add_column(conn, "movimentacoes_caixa", "caixa_id", "INTEGER")
        _add_column(conn, "movimentacoes_caixa", "usuario", "TEXT")
        _add_column(conn, "usuarios", "papel", "TEXT DEFAULT 'admin'")
        _add_column(conn, "usuarios", "ativo", "INTEGER DEFAULT 1")

        # Indices - criados DEPOIS das migracoes de coluna
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas (data)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos (nome)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_venda_venda ON itens_venda (venda_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mov_caixa ON movimentacoes_caixa (caixa_id, data)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contas_status ON contas_financeiras (status, vencimento)")

        cursor.execute("INSERT OR IGNORE INTO empresa (id) VALUES (1)")

    logger.info("Banco de dados inicializado com sucesso em %s", DB_NAME)


if __name__ == "__main__":
    inicializar_banco()
