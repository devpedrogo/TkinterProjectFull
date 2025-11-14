# 🚀 Sistema de Gestão de Pedidos & Análise de IA (Python Desktop App)

Este projeto é uma aplicação de desktop completa desenvolvida em Python para gerenciamento de clientes, produtos, pedidos e auditoria de ações. O sistema utiliza **Tkinter/TTK** para uma interface estável e profissional, com temas de alto contraste.

## ✨ Destaques do Projeto

| Funcionalidade | Detalhe Principal |
| :--- | :--- |
| **Análise de IA (Gemini)** | Gera insights de negócios (Top Produtos, Ticket Médio) a partir dos dados do SQLite. |
| **UX/UI Estável** | Interface de alto contraste (Dark/Light) com navegação unificada e funcionalidade de troca de tema garantida. |
| **Transações Seguras** | Criação de pedidos transacionais que atualizam o estoque em tempo real. |
| **Auditoria de Logs** | Registro automático de todas as ações de CRUD e visualização em uma tela de Histórico. |
| **Dashboard** | Visão geral em tempo real com métricas financeiras essenciais. |

---

## 🛠️ Tecnologias Utilizadas

| Componente | Tecnologia |
| :---: | :---: |
| Linguagem | Python 3 |
| Interface | Tkinter / TTK (ttkthemes) |
| Banco de Dados | SQLite3 |
| Inteligência Artificial| Google Gemini 2.5 Flash API |
| Segurança | python-dotenv |

---

## ⚙️ Instalação e Execução

### 1. Pré-requisitos

Instale as bibliotecas necessárias:

```bash
pip install ttkthemes google-genai python-dotenv reportlab
```
### 2. Configurar a Chave de API (Segurança)
ATENÇÃO: Para segurança, o arquivo .env é ignorado pelo Git.

Crie um arquivo chamado .env na raiz do projeto (fora da pasta app_pedidos) e adicione sua chave Gemini API:
```bash
Snippet de código

# .env
GEMINI_API_KEY="SUA_CHAVE_COMPLETA_OBTIDA_NO_GOOGLE_AI_STUDIO"
```
3. Inicialização
Navegue até a pasta app_pedidos e execute o script principal para iniciar o aplicativo:

```Bash

cd app_pedidos
python main.py
```
Desenvolvido por @devpedrogo.
