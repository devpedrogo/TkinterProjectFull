# utils/analise_ia.py (VERSÃO FINAL COMPLETA COM SUPORTE A .ENV)
from google import genai
from google.genai.errors import APIError
import logging
import os
# NOVO: Importa a biblioteca para carregar o arquivo .env
from dotenv import load_dotenv

# ----------------------------------------------------
# CARREGAMENTO DO .ENV: Esta linha deve ser a primeira a executar
# para que o genai.Client() possa encontrar a chave na variável de ambiente.
load_dotenv()
# ----------------------------------------------------

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# A biblioteca 'google-genai' buscará automaticamente a chave da variável de ambiente GEMINI_API_KEY.
MODELO_IA = "gemini-2.5-flash"

PROMPT_SISTEMA = """
Você é um analista de negócios. Sua tarefa é analisar os dados de pedidos brutos fornecidos 
abaixo e gerar insights acionáveis, concisos e fáceis de ler. 
Foque em:
1. Top 3 Produtos mais vendidos (por quantidade).
2. O Ticket Médio dos pedidos (Total / Número de pedidos).
3. A data do pedido mais recente.
4. Qualquer observação notável (ex: grande volume de pedidos em uma data).

Formate sua resposta como um resumo textual em blocos, usando emojis, e não ultrapasse 20 linhas.
"""


def analisar_pedidos_ia(dados_pedidos_brutos):
    """
    Formata os dados brutos dos pedidos e envia para a API do Gemini para análise.
    """
    if not dados_pedidos_brutos:
        return "❌ Não há pedidos suficientes para gerar uma análise."

    # --- 1. Formatação dos Dados para o Prompt ---

    contexto_dados = "## Dados Brutos dos Últimos Pedidos\n\n"

    for pedido in dados_pedidos_brutos:
        itens_str = ", ".join([
            f"{item['quantidade']}x {item['produto_nome']} (R$ {item['preco_unit']:.2f})"
            for item in pedido['itens']
        ])

        contexto_dados += (
            f"Pedido ID: {pedido['id']}, Cliente: {pedido['cliente']}, Data: {pedido['data']}, "
            f"Total: R$ {pedido['total']:.2f}\n"
            f"Itens: {itens_str}\n---\n"
        )

    contexto_dados += "\nPor favor, gere a análise com base nestes dados."

    # --- 2. Comunicação com a API do Gemini ---
    try:
        # A chave já está carregada no ambiente pela chamada load_dotenv()
        client = genai.Client()

        response = client.models.generate_content(
            model=MODELO_IA,
            contents=[
                {"role": "user", "parts": [
                    {"text": PROMPT_SISTEMA},
                    {"text": contexto_dados}
                ]}
            ],
            config={"temperature": 0.3}
        )

        return response.text

    except APIError as e:
        logging.error(f"Erro na API do Gemini: {e}")
        return (f"🛑 Erro de API (Gemini): Falha na comunicação ou cota excedida. "
                f"Verifique sua chave de API e o saldo. Detalhe: {e}")
    except Exception as e:
        logging.error(f"Erro desconhecido ao analisar pedidos com Gemini: {e}")
        return f"🚨 Erro Desconhecido: {e}"