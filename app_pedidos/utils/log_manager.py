# utils/log_manager.py
import logging
from datetime import datetime
import os

# Define o nome do arquivo de log e o diretório
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configura o logger para o arquivo específico
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Cria um logger com um handler para o arquivo (separado do logging global)
logger = logging.getLogger('action_logger')
logger.setLevel(logging.INFO)

# Handler que escreve no arquivo app.log
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

# Garante que o logger só tenha este handler (para evitar duplicação)
if not logger.handlers:
    logger.addHandler(file_handler)


def registrar_acao(tipo_entidade, acao, detalhes=""):
    """
    Registra uma ação auditável no arquivo de log.
    Ex: registrar_acao("CLIENTE", "CRIAR", "ID 5: Maria Silva")
    """
    mensagem = f"[{tipo_entidade}] {acao}: {detalhes}"
    logger.info(mensagem)


def ler_historico():
    """Lê todas as linhas do arquivo de log."""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            # Lê as linhas e as reverte para mostrar o mais recente primeiro
            return f.readlines()[::-1]
    except FileNotFoundError:
        return ["Nenhum histórico de ações encontrado."]
    except Exception as e:
        return [f"Erro ao ler histórico: {e}"]


def limpar_arquivo_log():
    """Apaga o conteúdo do arquivo de log."""
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - [SISTEMA] LOG LIMPO\n")
        return True
    except Exception as e:
        logging.error(f"Erro ao limpar o arquivo de log: {e}")
        return False