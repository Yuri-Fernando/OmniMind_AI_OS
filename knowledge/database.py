"""
knowledge/database.py
Base de conhecimento local AIOS — SQLite
Armazena: resumos RAG, insights de transcricao, anotacoes de sessao
"""
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

# Caminho do banco
DB_PATH = os.getenv("AIOS_DB_PATH", str(Path(__file__).parent / "aios_knowledge.db"))


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria todas as tabelas se nao existirem."""
    conn = _get_conn()
    c = conn.cursor()

    # Tabela principal AIOS — resumos RAG
    c.execute("""
        CREATE TABLE IF NOT EXISTS rag_summaries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fonte       TEXT NOT NULL,
            titulo      TEXT NOT NULL,
            resumo      TEXT,
            chunks      INTEGER DEFAULT 0,
            embeddings  TEXT,
            tags        TEXT,
            criado_em   TEXT DEFAULT (datetime('now')),
            UNIQUE(fonte, titulo)
        )
    """)

    # Insights extraidos de transcricoes / videos
    c.execute("""
        CREATE TABLE IF NOT EXISTS insights (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            origem      TEXT,
            tipo        TEXT,
            conteudo    TEXT NOT NULL,
            fase        TEXT,
            criado_em   TEXT DEFAULT (datetime('now'))
        )
    """)

    # Anotacoes de sessao (memoria de longo prazo estruturada)
    c.execute("""
        CREATE TABLE IF NOT EXISTS anotacoes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sessao_id   TEXT,
            pergunta    TEXT,
            resposta    TEXT,
            provedor    TEXT,
            modelo      TEXT,
            latencia_ms INTEGER,
            criado_em   TEXT DEFAULT (datetime('now'))
        )
    """)

    # Arquivos processados (controle de ingestion)
    c.execute("""
        CREATE TABLE IF NOT EXISTS arquivos_processados (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            caminho      TEXT UNIQUE NOT NULL,
            tipo         TEXT,
            status       TEXT DEFAULT 'pendente',
            transcricao  TEXT,
            resumo       TEXT,
            processado_em TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"[AIOS DB] Banco iniciado em: {DB_PATH}")


# --- RAG Summaries -----------------------------------------------------------

def salvar_resumo_rag(fonte: str, titulo: str, resumo: str,
                       chunks: int = 0, tags: list = None) -> dict:
    """Salva ou atualiza resumo de documento RAG."""
    conn = _get_conn()
    c = conn.cursor()
    dados = {
        "fonte": fonte,
        "titulo": titulo[:300],
        "resumo": resumo[:2000],
        "chunks": chunks,
        "tags": json.dumps(tags or []),
        "criado_em": datetime.utcnow().isoformat()
    }
    c.execute("""
        INSERT INTO rag_summaries (fonte, titulo, resumo, chunks, tags, criado_em)
        VALUES (:fonte, :titulo, :resumo, :chunks, :tags, :criado_em)
        ON CONFLICT(fonte, titulo) DO UPDATE SET
            resumo=excluded.resumo,
            chunks=excluded.chunks,
            tags=excluded.tags,
            criado_em=excluded.criado_em
    """, dados)
    conn.commit()
    inserido = c.lastrowid or 0
    conn.close()
    return {"id": inserido, "fonte": fonte, "titulo": titulo}


def buscar_resumos(query: str = None, limite: int = 20) -> list:
    """Busca resumos RAG, com filtro opcional por texto."""
    conn = _get_conn()
    c = conn.cursor()
    if query:
        c.execute("""
            SELECT * FROM rag_summaries
            WHERE titulo LIKE ? OR resumo LIKE ? OR fonte LIKE ?
            ORDER BY criado_em DESC LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limite))
    else:
        c.execute("SELECT * FROM rag_summaries ORDER BY criado_em DESC LIMIT ?", (limite,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# --- Insights ----------------------------------------------------------------

def salvar_insight(conteudo: str, origem: str = "transcricao",
                   tipo: str = "insight", fase: str = None) -> int:
    """Salva insight extraido de transcricao/video."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO insights (origem, tipo, conteudo, fase)
        VALUES (?, ?, ?, ?)
    """, (origem, tipo, conteudo, fase))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def listar_insights(tipo: str = None, limite: int = 50) -> list:
    conn = _get_conn()
    c = conn.cursor()
    if tipo:
        c.execute("SELECT * FROM insights WHERE tipo=? ORDER BY criado_em DESC LIMIT ?", (tipo, limite))
    else:
        c.execute("SELECT * FROM insights ORDER BY criado_em DESC LIMIT ?", (limite,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# --- Anotacoes de Sessao -----------------------------------------------------

def salvar_anotacao(sessao_id: str, pergunta: str, resposta: str,
                     provedor: str = None, modelo: str = None,
                     latencia_ms: int = None) -> int:
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO anotacoes (sessao_id, pergunta, resposta, provedor, modelo, latencia_ms)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sessao_id, pergunta, resposta[:5000], provedor, modelo, latencia_ms))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


# --- Arquivos Processados ----------------------------------------------------

def registrar_arquivo(caminho: str, tipo: str = "audio") -> int:
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO arquivos_processados (caminho, tipo, status)
        VALUES (?, ?, 'pendente')
    """, (caminho, tipo))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def marcar_processado(caminho: str, transcricao: str = None, resumo: str = None):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE arquivos_processados
        SET status='concluido', transcricao=?, resumo=?, processado_em=?
        WHERE caminho=?
    """, (transcricao, resumo, datetime.utcnow().isoformat(), caminho))
    conn.commit()
    conn.close()


def listar_arquivos(status: str = None) -> list:
    conn = _get_conn()
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM arquivos_processados WHERE status=? ORDER BY id DESC", (status,))
    else:
        c.execute("SELECT * FROM arquivos_processados ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# --- Estatisticas ------------------------------------------------------------

def stats() -> dict:
    """Retorna estatisticas do banco."""
    conn = _get_conn()
    c = conn.cursor()
    resultado = {}
    for tabela in ["rag_summaries", "insights", "anotacoes", "arquivos_processados"]:
        c.execute(f"SELECT COUNT(*) FROM {tabela}")
        resultado[tabela] = c.fetchone()[0]
    conn.close()
    return resultado


# Inicializa automaticamente ao importar
if __name__ == "__main__":
    init_db()
    print("Stats:", stats())
