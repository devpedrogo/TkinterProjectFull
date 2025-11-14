# db.py (VERSÃO FINAL COMPLETA E CONSOLIDADA)
import sqlite3
from sqlite3 import Error
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_NAME = "pedidos.db"


def criar_conexao(db_file=DATABASE_NAME):
    """Cria uma conexão com o banco de dados SQLite especificado."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except Error as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        if conn:
            conn.close()
        return None


def inicializar_db():
    """Cria as tabelas do esquema."""
    conn = criar_conexao()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            # Tabela CLIENTES
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE,
                    telefone TEXT
                );
            """)

            # Tabela PRODUTOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    preco REAL NOT NULL,
                    estoque INTEGER NOT NULL DEFAULT 0
                );
            """)

            # Tabela PEDIDOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    total REAL NOT NULL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
                );
            """)

            # Tabela ITENS_PEDIDO
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS itens_pedido (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER NOT NULL,
                    produto_id INTEGER,
                    produto_nome TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    preco_unit REAL NOT NULL,
                    FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE SET NULL
                );
            """)
            conn.commit()
            logging.info("Banco de dados inicializado com sucesso.")
        except Error as e:
            logging.error(f"Erro ao criar tabelas: {e}")
            print(f"ERRO CRÍTICO NA CRIAÇÃO DE TABELAS: {e}")
        finally:
            conn.close()
    else:
        logging.error("Não foi possível estabelecer a conexão para inicialização do DB.")


def get_dashboard_metrics():
    """
    Retorna métricas agregadas: Total de Clientes, Pedidos no Mês e Ticket Médio.
    """
    conn = criar_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        # 1. Total de Clientes
        cursor.execute("SELECT COUNT(id) FROM clientes")
        total_clientes = cursor.fetchone()[0]

        # Data de início do mês atual (formato YYYY-MM-01)
        hoje = datetime.now()
        primeiro_dia_mes = hoje.strftime("%Y-%m-01")

        # 2. Total de Pedidos e Ticket Médio no Mês
        sql_pedidos_mes = f"""
            SELECT 
                COUNT(id), 
                AVG(total) 
            FROM pedidos 
            WHERE data >= '{primeiro_dia_mes}'
        """
        cursor.execute(sql_pedidos_mes)
        pedidos_mes_data = cursor.fetchone()

        total_pedidos_mes = pedidos_mes_data[0]
        ticket_medio = pedidos_mes_data[1] if pedidos_mes_data[1] is not None else 0.0

        return {
            "total_clientes": total_clientes,
            "total_pedidos_mes": total_pedidos_mes,
            "ticket_medio": ticket_medio
        }

    except Exception as e:
        logging.error(f"Erro ao buscar métricas do Dashboard: {e}")
        return None

    finally:
        if conn:
            conn.close()


def get_ultimos_pedidos_detalhados(limite=5):
    """
    Busca os últimos 'limite' pedidos com seus itens detalhados para análise de IA.
    Retorna uma lista de dicionários detalhados.
    """
    conn = criar_conexao()
    if conn is None:
        return []

    sql_base = f"""
        SELECT 
            p.id, 
            c.nome AS cliente, 
            p.data, 
            p.total,
            i.id AS item_id,
            i.produto_nome,
            i.quantidade,
            i.preco_unit
        FROM pedidos p
        INNER JOIN clientes c ON p.cliente_id = c.id
        INNER JOIN itens_pedido i ON p.id = i.pedido_id
        ORDER BY p.id DESC
        LIMIT {limite}
    """

    pedidos_agrupados = []

    try:
        cursor = conn.cursor()
        cursor.execute(sql_base)

        for row in cursor.fetchall():
            (pedido_id, cliente, data, total, item_id, produto_nome, quantidade, preco_unit) = row

            # Encontrar o índice do pedido (agrupamento)
            try:
                pedido_idx = [i for i, p in enumerate(pedidos_agrupados) if p['id'] == pedido_id][0]
            except IndexError:
                # Pedido novo
                pedido_idx = len(pedidos_agrupados)
                pedidos_agrupados.append({
                    'id': pedido_id,
                    'cliente': cliente,
                    'data': data,
                    'total': total,
                    'itens': []
                })

            # Adicionar o item
            pedidos_agrupados[pedido_idx]['itens'].append({
                'id': item_id,
                'produto_nome': produto_nome,
                'quantidade': quantidade,
                'preco_unit': preco_unit
            })

        return pedidos_agrupados

    except Error as e:
        logging.error(f"Erro ao buscar últimos pedidos para análise de IA: {e}")
        return []
    finally:
        if conn:
            conn.close()


def buscar_pedidos_relatorio(data_inicio=None, data_fim=None, cliente_id=None):
    """
    Busca pedidos e seus itens detalhados com filtros de data e cliente (MÉTODO PARA RELATÓRIOS).
    Retorna um dicionário: {pedido_id: {cliente: '...', data: '...', total: 100.0, itens: [...]}}
    """
    conn = criar_conexao()
    if conn is None:
        return None

    sql = """
        SELECT 
            p.id AS pedido_id, 
            c.nome AS cliente_nome, 
            p.data AS data_pedido, 
            p.total AS total_pedido,
            i.id AS item_id,
            i.produto_nome AS item_nome,
            i.quantidade AS item_quantidade,
            i.preco_unit AS item_preco_unit
        FROM pedidos p
        INNER JOIN clientes c ON p.cliente_id = c.id
        INNER JOIN itens_pedido i ON p.id = i.pedido_id
    """

    # 1. Construir a cláusula WHERE
    condicoes = []
    parametros = []

    if cliente_id is not None and cliente_id != "Todos":
        condicoes.append("c.id = ?")
        parametros.append(cliente_id)

    if data_inicio:
        condicoes.append("p.data >= ?")
        parametros.append(data_inicio)

    if data_fim:
        condicoes.append("p.data <= ?")
        parametros.append(data_fim)

    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)

    sql += " ORDER BY p.data DESC, p.id DESC"

    pedidos_agrupados = {}

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(parametros))

        # Mapeamento para agrupar itens por pedido
        for row in cursor.fetchall():
            pedido_id = row[0]

            if pedido_id not in pedidos_agrupados:
                pedidos_agrupados[pedido_id] = {
                    'cliente': row[1],
                    'data': row[2],
                    'total': row[3],
                    'itens': []
                }

            # Adiciona o item ao pedido
            pedidos_agrupados[pedido_id]['itens'].append({
                'id': row[4],
                'nome': row[5],
                'quantidade': row[6],
                'preco_unit': row[7]
            })

        return pedidos_agrupados

    except Error as e:
        logging.error(f"Erro ao buscar pedidos detalhados para relatório: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def executar_comando(sql, parametros=(), fetchone=False, fetchall=False, commit=True):
    """
    Executa comandos SQL (SELECT, INSERT, UPDATE, DELETE) parametrizados.
    """
    conn = criar_conexao()
    resultado = None
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(sql, parametros)

        if fetchone:
            resultado = cursor.fetchone()
        elif fetchall:
            resultado = cursor.fetchall()
        elif commit:
            conn.commit()
            if sql.strip().upper().startswith("INSERT"):
                resultado = cursor.lastrowid

    except sqlite3.IntegrityError as e:
        logging.warning(f"Erro de Integridade no DB: {e}. SQL: {sql}")
        resultado = "IntegrityError"
        if commit: conn.rollback()
    except Error as e:
        logging.error(f"Erro ao executar comando SQL: {e}. SQL: {sql} - Params: {parametros}")
        if commit: conn.rollback()
    finally:
        if conn:
            conn.close()
    return resultado