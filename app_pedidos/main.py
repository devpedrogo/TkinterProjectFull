# main.py (VERSÃO FINAL DE ESTABILIDADE E CORREÇÃO DE NAMES)
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from ttkthemes import ThemedTk
from db import inicializar_db, executar_comando, get_dashboard_metrics, get_ultimos_pedidos_detalhados
from forms.cliente_form import ClienteForm
from forms.produto_form import ProdutoForm
from forms.pedido_form import PedidoForm
from forms.detalhes_pedido_form import DetalhesPedidoForm
from forms.relatorios_form import RelatoriosForm
from forms.historico_form import HistoricoForm
from utils.analise_ia import analisar_pedidos_ia
from utils.log_manager import registrar_acao

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- DEFINIÇÕES DE CONSTANTES GLOBAIS ---
TEMA_ESCURO = "equilux"
TEMA_CLARO = "clam"
MODERN_FONT_FAMILY = 'Inter'
MODERN_FONT = ('Inter', 10)

# Cores de Estilo
ACCENT_COLOR = '#4A90E2'  # Azul Neutro para destaques/botões
CUSTOM_DARK_BG = '#2B2B2B'

# Cores do Tema Básico
DARK_BG_PRIMARY = '#2B2B2B'
DARK_BG_SECONDARY = '#3C3C3C'
DARK_TEXT_COLOR = '#E0E0E0'
DARK_ACCENT_COLOR = '#5A9BD6'

LIGHT_BG_PRIMARY = '#F0F0F0'
LIGHT_BG_SECONDARY = '#E8E8E8'
LIGHT_TEXT_COLOR = '#333333'
LIGHT_ACCENT_COLOR = '#5A9BD6'


class App(ThemedTk):
    def __init__(self):
        super().__init__(theme=TEMA_CLARO)  # Inicia no tema claro
        self.title("Sistema de Gestão de Clientes e Pedidos")
        self.geometry("1200x800")

        self._current_theme_name = TEMA_CLARO

        inicializar_db()
        self.setup_custom_styles()
        self.setup_app_theme(self._current_theme_name)

        self.var_busca_cliente = tk.StringVar()
        self.var_busca_produto = tk.StringVar()
        self.var_clientes = tk.StringVar(value="--")
        self.var_pedidos = tk.StringVar(value="--")
        self.var_ticket = tk.StringVar(value="R$ --")

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        self.setup_top_menu_actions(main_frame)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.setup_dashboard_tab()
        self.setup_cliente_tab()
        self.setup_produto_tab()
        self.setup_pedido_tab()

        self.recarregar_clientes()
        self.recarregar_produtos()
        self.recarregar_pedidos()
        self.recarregar_dashboard()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self.protocol("WM_DELETE_WINDOW", self._on_app_fechar)

    def _on_app_fechar(self):
        if messagebox.askyesno("Sair do Sistema", "Tem certeza que deseja sair do aplicativo?"):
            self.destroy()

    def setup_custom_styles(self):
        """Configura estilos customizados no TTK padrão."""

        self.style = ttk.Style(self)
        self.style.configure('.', font=MODERN_FONT)
        self.style.configure('TLabel', font=MODERN_FONT)
        self.style.configure('TButton', padding=[10, 5])

        # Configuração inicial do Treeview (foreground será ajustado dinamicamente)
        self.style.configure(
            "Treeview.Heading",
            foreground=ACCENT_COLOR,
            font=(MODERN_FONT_FAMILY, 10, 'bold')
        )

        # Estilos do Dashboard (usados dinamicamente)
        self.style.configure("DashboardValue.TLabel", foreground=ACCENT_COLOR, font=(MODERN_FONT_FAMILY, 16, 'bold'))
        self.style.configure("DashboardTitle.TLabel", font=MODERN_FONT)

        # Estilo para Botões Principais (Azul discreto)
        self.style.configure("Primary.TButton", foreground='white', background=ACCENT_COLOR)
        self.style.map("Primary.TButton", background=[('active', ACCENT_COLOR)])

        # Estilo para Entradas (Ajustaremos dinamicamente)
        self.style.configure("Search.TEntry", relief="flat", padding=5)

    def setup_app_theme(self, theme_name):
        """Aplica o tema e configura as cores dinamicamente."""

        try:
            self.set_theme(theme_name)
            self._current_theme_name = theme_name
        except Exception as e:
            messagebox.showerror("Erro de Tema", f"O tema '{theme_name}' não pôde ser aplicado. Erro: {e}")
            self.set_theme(TEMA_CLARO)
            self._current_theme_name = TEMA_CLARO

        # 1. Definição das Cores Dinâmicas
        is_dark = (self._current_theme_name == TEMA_ESCURO)

        # Cores gerais da aplicação
        app_bg_color = DARK_BG_PRIMARY if is_dark else LIGHT_BG_PRIMARY
        main_text_color = DARK_TEXT_COLOR if is_dark else LIGHT_TEXT_COLOR
        accent_color = DARK_ACCENT_COLOR if is_dark else LIGHT_ACCENT_COLOR

        # Cores para elementos secundários (cartões, entradas)
        secondary_bg_color = DARK_FRAME_COLOR if is_dark else LIGHT_BG_SECONDARY
        secondary_text_color = DARK_TEXT_COLOR if is_dark else LIGHT_TEXT_COLOR

        # 2. Aplicação Geral (Fundo e Texto)
        self.configure(bg=app_bg_color)
        self.style.configure('TFrame', background=app_bg_color)
        self.style.configure('TNotebook', background=app_bg_color)

        # Cores Dinâmicas para Labels, Tabs e Entradas (Garantindo Visibilidade)
        self.style.configure('TLabel', foreground=main_text_color, background=app_bg_color)
        self.style.configure('TNotebook.Tab', background=app_bg_color, foreground=main_text_color)
        self.style.map('TNotebook.Tab',
                       background=[('selected', secondary_bg_color if is_dark else accent_color)],
                       foreground=[('selected', DARK_TEXT_COLOR if is_dark else 'white')])

        # 3. Aplicação Específica (Bordas, Cartões, Entradas, Botões)

        # Dashboard Frames (Bordas Visíveis)
        self.style.configure("Dashboard.TFrame",
                             background=secondary_bg_color,
                             relief="solid",
                             borderwidth=1,
                             bordercolor=accent_color  # Borda com a cor de destaque
                             )
        self.style.configure("DashboardTitle.TLabel", foreground=secondary_text_color,
                             background=secondary_bg_color)  # Título do cartão
        self.style.configure("DashboardValue.TLabel", foreground=accent_color,
                             background=secondary_bg_color)  # Valor do cartão

        # Entradas de Texto (Search.TEntry e TEntry)
        self.style.configure("TEntry",
                             fieldbackground=secondary_bg_color,
                             foreground=secondary_text_color,
                             insertcolor=accent_color,  # Cor do cursor
                             )

        # Treeview (Fundo claro no modo claro)
        self.style.configure("Treeview",
                             background=secondary_bg_color,
                             fieldbackground=secondary_bg_color,
                             foreground=secondary_text_color
                             )
        self.style.configure("Treeview.Heading",
                             foreground=accent_color,
                             background=DARK_BG_SECONDARY if is_dark else LIGHT_BG_SECONDARY
                             )

        # ScrolledText (Insights de IA)
        if hasattr(self, 'ia_text_widget'):
            self.ia_text_widget.config(
                background=secondary_bg_color,
                foreground=secondary_text_color,
                font=MODERN_FONT,
                insertbackground=accent_color
            )

    def alternar_tema(self):
        """Alterna entre o tema Escuro e o tema Claro."""
        new_theme = TEMA_ESCURO if self._current_theme_name == TEMA_CLARO else TEMA_CLARO

        self.setup_app_theme(new_theme)
        messagebox.showinfo("Tema",
                            f"Tema alterado para: {'Escuro' if self._current_theme_name == TEMA_ESCURO else 'Claro'}.")

    # --- SETUP DA BARRA DE AÇÕES SUPERIOR ---

    def setup_top_menu_actions(self, parent_frame):
        """Cria a barra de botões de ações (Relatórios, Histórico, Tema) no topo."""
        menu_frame = ttk.Frame(parent_frame, padding="5")
        menu_frame.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Button(menu_frame, text="❌ Sair", command=self._on_app_fechar, style='Primary.TButton').pack(side="right",
                                                                                                         padx=5)

        ttk.Button(menu_frame, text="📊 Relatórios", command=self.abrir_relatorios, style='Primary.TButton').pack(
            side="right", padx=5)

        ttk.Button(menu_frame, text="📜 Histórico", command=self.abrir_historico, style='Primary.TButton').pack(
            side="right", padx=5)

        ttk.Button(menu_frame, text="🌓 Tema", command=self.alternar_tema, style='Primary.TButton').pack(side="right",
                                                                                                        padx=15)

        ttk.Frame(menu_frame, width=1).pack(side="right", fill='y', padx=10)

    def _on_tab_change(self, event):
        tab_index = self.notebook.index("current")
        tab_name = self.notebook.tab(tab_index, "text")
        if tab_name == "Pedidos":
            self.recarregar_pedidos()
        elif tab_name == "Dashboard":
            self.recarregar_dashboard(display_message=False)

    # --- SETUP DASHBOARD ---

    def setup_dashboard_tab(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="Dashboard")

        ttk.Label(frame, text="Visão Geral do Negócio", font=('Arial', 18, 'bold')).pack(pady=(0, 20), anchor='w')

        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill="x", pady=10)

        self._criar_cartao_dashboard(metrics_frame, "Total de Clientes", self.var_clientes, 0)
        self._criar_cartao_dashboard(metrics_frame, "Pedidos no Mês", self.var_pedidos, 1)
        self._criar_cartao_dashboard(metrics_frame, "Ticket Médio", self.var_ticket, 2)

        control_frame = ttk.Frame(frame)
        control_frame.pack(pady=20, anchor='w', fill="x")

        ttk.Button(control_frame, text="🔄 Atualizar Dados", command=self.recarregar_dashboard,
                   style='Primary.TButton').pack(side="left", padx=10)
        ttk.Button(control_frame, text="🤖 Analisar Últimos 5 Pedidos (IA)", command=self.analisar_pedidos_ia_ui,
                   style='Primary.TButton').pack(side="left", padx=10)

        ttk.Button(control_frame, text="ℹ️ Sobre", command=lambda: messagebox.showinfo("Sobre",
                                                                                       "Sistema de Gestão de Pedidos.\nDesenvolvido com Python/TTK."),
                   style='Primary.TButton').pack(side="right", padx=10)

        # Área de insights
        ttk.Label(frame, text="Insights de IA:", font=('Arial', 12, 'bold')).pack(pady=(10, 5), anchor='w')
        self.ia_text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=15, font=MODERN_FONT,
                                                        relief="flat")
        self.ia_text_widget.pack(fill="both", expand=True)
        self.ia_text_widget.insert(tk.END, "Clique no botão 'Analisar Últimos 5 Pedidos (IA)' para gerar insights.")
        self.ia_text_widget.config(state=tk.DISABLED)

        self.setup_app_theme(self._current_theme_name)

    def _criar_cartao_dashboard(self, parent, titulo, var_valor, coluna):
        cartao = ttk.Frame(parent, style="Dashboard.TFrame", padding="15")
        cartao.grid(row=0, column=coluna, padx=15, pady=5, sticky="nsew")

        ttk.Label(cartao, text=titulo, style="DashboardTitle.TLabel").pack(padx=10, pady=5, anchor="w")
        ttk.Label(cartao, textvariable=var_valor, style="DashboardValue.TLabel").pack(padx=10, pady=5, anchor="w")

        parent.grid_columnconfigure(coluna, weight=1)

    def recarregar_dashboard(self, display_message=True):
        metrics = get_dashboard_metrics()
        if metrics is not None:
            self.var_clientes.set(f"{metrics['total_clientes']}")
            self.var_pedidos.set(f"{metrics['total_pedidos_mes']}")
            self.var_ticket.set(f"R$ {metrics['ticket_medio']:.2f}".replace('.', ','))
            if display_message:
                messagebox.showinfo("Atualização", "Dados do Dashboard atualizados com sucesso!")
        else:
            if display_message:
                messagebox.showerror("Erro", "Falha ao carregar métricas do Dashboard.")

    def analisar_pedidos_ia_ui(self):
        self.ia_text_widget.config(state=tk.NORMAL)
        self.ia_text_widget.delete(1.0, tk.END)
        self.ia_text_widget.insert(tk.END,
                                   "Aguarde... Buscando dados e solicitando análise à IA (pode levar alguns segundos).\n\n")
        self.ia_text_widget.config(state=tk.DISABLED)
        self.update_idletasks()

        logging.info("Iniciando análise de pedidos via API de IA (Gemini).")
        dados_brutos = get_ultimos_pedidos_detalhados(limite=5)
        resultado_analise = analisar_pedidos_ia(dados_brutos)

        self.ia_text_widget.config(state=tk.NORMAL)
        self.ia_text_widget.delete(1.0, tk.END)
        self.ia_text_widget.insert(tk.END, resultado_analise)
        self.ia_text_widget.config(state=tk.DISABLED)
        logging.info("Análise de IA concluída.")

    # --- SETUP CLIENTES ---

    def setup_cliente_tab(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Clientes")

        frame_busca = ttk.Frame(frame)
        frame_busca.pack(fill="x", pady=(0, 10))
        ttk.Label(frame_busca, text="Buscar Cliente (Nome/Email):", style='DashboardTitle.TLabel').pack(side="left",
                                                                                                        padx=5, pady=5)
        ttk.Entry(frame_busca, textvariable=self.var_busca_cliente, width=50, style='TEntry').pack(side="left",
                                                                                                   fill="x",
                                                                                                   expand=True, padx=5)
        self.var_busca_cliente.trace_add("write", lambda *args: self.recarregar_clientes())

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        self.tree_clientes = self._criar_treeview(list_frame, ("ID", "Nome", "Email", "Telefone"))
        self.tree_clientes.column("ID", width=50, anchor="center");
        self.tree_clientes.heading("ID", text="ID")
        self.tree_clientes.column("Nome", width=250);
        self.tree_clientes.heading("Nome", text="Nome")
        self.tree_clientes.column("Email", width=250);
        self.tree_clientes.heading("Email", text="Email")
        self.tree_clientes.column("Telefone", width=150);
        self.tree_clientes.heading("Telefone", text="Telefone")

        frame_botoes = ttk.Frame(frame, padding="5")
        frame_botoes.pack(fill="x")
        ttk.Button(frame_botoes, text="Novo Cliente", command=self.abrir_novo_cliente, style='Primary.TButton').pack(
            side="left", padx=5)
        ttk.Button(frame_botoes, text="Editar Cliente", command=self.abrir_editar_cliente,
                   style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(frame_botoes, text="Excluir Cliente", command=self.excluir_cliente, style='Primary.TButton').pack(
            side="left", padx=5)
        self.tree_clientes.bind('<Double-1>', lambda e: self.abrir_editar_cliente())

    # --- SETUP PRODUTOS ---

    def setup_produto_tab(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Produtos")

        frame_busca = ttk.Frame(frame)
        frame_busca.pack(fill="x", pady=(0, 10))
        ttk.Label(frame_busca, text="Buscar Produto (Nome):", style='DashboardTitle.TLabel').pack(side="left", padx=5,
                                                                                                  pady=5)
        ttk.Entry(frame_busca, textvariable=self.var_busca_produto, width=50, style='TEntry').pack(side="left",
                                                                                                   fill="x",
                                                                                                   expand=True, padx=5)
        self.var_busca_produto.trace_add("write", lambda *args: self.recarregar_produtos())

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        self.tree_produtos = self._criar_treeview(list_frame, ("ID", "Nome", "Preço", "Estoque"))
        self.tree_produtos.column("ID", width=50, anchor="center");
        self.tree_produtos.heading("ID", text="ID")
        self.tree_produtos.column("Nome", width=300);
        self.tree_produtos.heading("Nome", text="Nome")
        self.tree_produtos.column("Preço", width=150, anchor="e");
        self.tree_produtos.heading("Preço", text="Preço Unit. R$")
        self.tree_produtos.column("Estoque", width=100, anchor="center");
        self.tree_produtos.heading("Estoque", text="Estoque")

        frame_botoes = ttk.Frame(frame, padding="5")
        frame_botoes.pack(fill="x")
        ttk.Button(frame_botoes, text="Novo Produto", command=self.abrir_novo_produto, style='Primary.TButton').pack(
            side="left", padx=5)
        ttk.Button(frame_botoes, text="Editar Produto", command=self.abrir_editar_produto,
                   style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(frame_botoes, text="Excluir Produto", command=self.excluir_produto, style='Primary.TButton').pack(
            side="left", padx=5)
        self.tree_produtos.bind('<Double-1>', lambda e: self.abrir_editar_produto())

    # --- SETUP PEDIDOS ---

    def setup_pedido_tab(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Pedidos")

        frame_busca = ttk.Frame(frame)
        frame_busca.pack(fill="x")
        ttk.Label(frame_busca, text="Lista de Pedidos (mais recentes primeiro)", style='DashboardTitle.TLabel').pack(
            side="left", padx=5, pady=5)
        ttk.Button(frame_busca, text="Atualizar Lista", command=self.recarregar_pedidos).pack(side="right", padx=5)

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.tree_pedidos = self._criar_treeview(list_frame, ("ID", "Cliente", "Data", "Total"))
        self.tree_pedidos.column("ID", width=70, anchor="center");
        self.tree_pedidos.heading("ID", text="ID")
        self.tree_pedidos.column("Cliente", width=300);
        self.tree_pedidos.heading("Cliente", text="Cliente")
        self.tree_pedidos.column("Data", width=150, anchor="center");
        self.tree_pedidos.heading("Data", text="Data")
        self.tree_pedidos.column("Total", width=150, anchor="e");
        self.tree_pedidos.heading("Total", text="Total R$")

        self.tree_pedidos.bind('<Double-1>', lambda e: self.abrir_detalhes_pedido())

        frame_botoes = ttk.Frame(frame, padding="5")
        frame_botoes.pack(fill="x")

        ttk.Button(frame_botoes, text="Novo Pedido", command=self.abrir_novo_pedido, style='Primary.TButton').pack(
            side="left", padx=5)
        ttk.Button(frame_botoes, text="Ver Detalhes", command=self.abrir_detalhes_pedido, style='Primary.TButton').pack(
            side="left", padx=5)

    # --- SETUP RELATÓRIOS E HISTÓRICO (Rodapé Unificado) ---

    def setup_footer_buttons(self, parent_frame):
        """Este método está obsoleto, o menu foi movido para o topo."""
        pass

    def abrir_relatorios(self):
        RelatoriosForm(self)

    def abrir_historico(self):
        HistoricoForm(self)

        # --- AUXILIARES E RECARREGAMENTO ---

    def _criar_treeview(self, parent_frame, colunas):
        tree = ttk.Treeview(parent_frame, columns=colunas, show="headings")
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=tree.yview)  # Scrollbar TTK padrão

        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    def recarregar_clientes(self):
        self._recarregar_dados(self.tree_clientes, "clientes", self.var_busca_cliente.get().strip(),
                               "nome LIKE ? OR email LIKE ?",
                               "id, nome, email, telefone")

    def recarregar_produtos(self):
        self._recarregar_dados(self.tree_produtos, "produtos", self.var_busca_produto.get().strip(),
                               "nome LIKE ?",
                               "id, nome, preco, estoque")

    def recarregar_pedidos(self):
        """Busca pedidos no DB e recarrega a Treeview de pedidos."""
        for item in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(item)

        sql = """
            SELECT 
                p.id, 
                c.nome, 
                p.data, 
                p.total 
            FROM pedidos p
            INNER JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.data DESC, p.id DESC
        """
        try:
            pedidos = executar_comando(sql, fetchall=True)
            if pedidos:
                for pedido in pedidos:
                    pedido_id = pedido[0]
                    nome_cliente = pedido[1]
                    data = pedido[2]
                    total_formatado = f"{pedido[3]:.2f}"

                    self.tree_pedidos.insert(
                        "",
                        "end",
                        iid=pedido_id,
                        values=(pedido_id, nome_cliente, data, total_formatado)
                    )
            else:
                self.tree_pedidos.insert("", "end", values=("", "Nenhum pedido encontrado.", "", ""), tags=('empty',))
        except Exception as e:
            logging.error(f"Erro ao carregar pedidos: {e}")
            messagebox.showerror("Erro de DB", f"Não foi possível carregar a lista de pedidos: {e}")

    def _recarregar_dados(self, treeview, tabela, termo, where_clause, colunas_sql):
        # Limpa o Treeview
        for item in treeview.get_children():
            treeview.delete(item)

        sql = f"SELECT {colunas_sql} FROM {tabela}"
        parametros = ()

        if termo:
            sql += f" WHERE {where_clause}"
            if tabela == "clientes":
                parametros = (f'%{termo}%', f'%{termo}%')
            elif tabela == "produtos":
                parametros = (f'%{termo}%',)

        try:
            dados = executar_comando(sql, parametros, fetchall=True)
            if dados:
                for dado in dados:
                    if tabela == "produtos":
                        dado_list = list(dado)
                        dado_list[2] = f"{dado_list[2]:.2f}"
                        treeview.insert("", "end", iid=dado_list[0], values=dado_list)
                    else:
                        treeview.insert("", "end", iid=dado[0], values=dado)

        except Exception as e:
            logging.error(f"Erro ao carregar dados de {tabela}: {e}")
            messagebox.showerror("Erro de DB", f"Não foi possível carregar a lista de {tabela}: {e}")

    # --- MÉTODOS CRUD E ABERTURA DE FORMS ---

    def _get_selected_id(self, treeview):
        selecionado = treeview.selection()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um item na lista.")
            return None
        return selecionado[0]

    def abrir_novo_cliente(self):
        ClienteForm(self, recarregar_callback=self.recarregar_clientes)

    def abrir_editar_cliente(self):
        cliente_id = self._get_selected_id(self.tree_clientes)
        if cliente_id:
            ClienteForm(self, cliente_id=int(cliente_id), recarregar_callback=self.recarregar_clientes)

    def excluir_cliente(self):
        cliente_id = self._get_selected_id(self.tree_clientes)
        if cliente_id:
            if messagebox.askyesno("Confirmar Exclusão",
                                   "Tem certeza que deseja excluir o cliente selecionado? "
                                   "Todos os pedidos associados serão EXCLUÍDOS (CASCADE)."):
                try:
                    nome_cliente_excluido = self.tree_clientes.item(cliente_id, 'values')[1]

                    executar_comando("DELETE FROM clientes WHERE id = ?", (cliente_id,))

                    registrar_acao("CLIENTE", "EXCLUIR",
                                   f"ID {cliente_id}: {nome_cliente_excluido} (Pedidos associados excluídos)")

                    messagebox.showinfo("Sucesso", "Cliente e pedidos associados excluídos!")
                    self.recarregar_clientes()
                    self.recarregar_dashboard()
                except Exception as e:
                    logging.error(f"Erro ao excluir cliente: {e}")
                    messagebox.showerror("Erro de DB", f"Não foi possível excluir o cliente: {e}")

    def abrir_novo_produto(self):
        ProdutoForm(self, recarregar_callback=self.recarregar_produtos)

    def abrir_editar_produto(self):
        produto_id = self._get_selected_id(self.tree_produtos)
        if produto_id:
            ProdutoForm(self, produto_id=int(produto_id), recarregar_callback=self.recarregar_produtos)

    def excluir_produto(self):
        produto_id = self._get_selected_id(self.tree_produtos)
        if produto_id:
            if messagebox.askyesno("Confirmar Exclusão",
                                   "Tem certeza que deseja excluir o produto selecionado? "
                                   "Pedidos que o contêm serão afetados (o item permanecerá com o nome, mas sem link)."):
                try:
                    executar_comando("DELETE FROM produtos WHERE id = ?", (produto_id,))

                    registrar_acao("PRODUTO", "EXCLUIR", f"ID {produto_id} (Verifique pedidos afetados)")

                    messagebox.showinfo("Sucesso", "Produto excluído!")
                    self.recarregar_produtos()
                except Exception as e:
                    logging.error(f"Erro ao excluir produto: {e}")
                    messagebox.showerror("Erro de DB", f"Não foi possível excluir o produto: {e}")

    def abrir_novo_pedido(self):
        def callback_completo():
            self.recarregar_pedidos()
            self.recarregar_produtos()
            self.recarregar_dashboard()

        PedidoForm(self, recarregar_callback=callback_completo)

    def abrir_detalhes_pedido(self):
        """Abre a janela de detalhes para o pedido selecionado."""
        pedido_id = self._get_selected_id(self.tree_pedidos)
        if pedido_id:
            try:
                DetalhesPedidoForm(self, pedido_id=int(pedido_id))
            except ValueError:
                messagebox.showerror("Erro", "ID de pedido inválido.")


if __name__ == "__main__":
    app = App()
    app.mainloop()