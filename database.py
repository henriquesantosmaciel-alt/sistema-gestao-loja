"""
database.py - Configuracao e modelagem do banco de dados SQLite
Sistema de Gestao de Loja
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
        CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            data TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            cnpj TEXT,
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

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas (data)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos (nome)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_venda_venda ON itens_venda (venda_id)")

    logger.info("Banco de dados inicializado com sucesso em %s", DB_NAME)


if __name__ == "__main__":
    inicializar_banco()
