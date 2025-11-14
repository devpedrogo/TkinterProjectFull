# forms/pedido_form.py (ATUALIZADO com Log de Ações)
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
from db import criar_conexao, Error, executar_comando  # Importação de Error para tratamento de exceções
# NOVO:
from utils.log_manager import registrar_acao

# Configuração de logging, se não for centralizada no db.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PedidoForm(tk.Toplevel):
    def __init__(self, parent, recarregar_callback=None):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.parent = parent
        self.recarregar_callback = recarregar_callback
        self.title("Novo Pedido")
        self.protocol("WM_DELETE_WINDOW", self._on_fechar)

        # Dados: (produto_id, produto_nome, qtd, preco_unit)
        self.itens_pedido = []
        self.clientes_map = {}  # {nome: id}
        self.produtos_map = {}  # {nome: (id, preco)}
        self.dados_salvos = True

        self.setup_ui()
        self._carregar_dados_iniciais()

    def _carregar_dados_iniciais(self):
        self._carregar_clientes_combobox()
        self._carregar_produtos_combobox()

    def setup_ui(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill="both", expand=True)

        # Seção de Cabeçalho do Pedido (Cliente, Data)
        header_frame = ttk.LabelFrame(frame, text="Dados do Pedido", padding="10")
        header_frame.pack(fill="x", pady=5)

        ttk.Label(header_frame, text="Cliente:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.var_cliente = tk.StringVar()
        self.cb_cliente = ttk.Combobox(header_frame, textvariable=self.var_cliente, state="readonly", width=35)
        self.cb_cliente.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        ttk.Label(header_frame, text="Data:").grid(row=0, column=2, sticky="w", padx=15, pady=5)
        self.var_data = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(header_frame, textvariable=self.var_data, width=15).grid(row=0, column=3, sticky="w", padx=5, pady=5)

        # Seção de Itens do Pedido (Formulário para adicionar)
        item_input_frame = ttk.LabelFrame(frame, text="Adicionar Item", padding="10")
        item_input_frame.pack(fill="x", pady=10)

        ttk.Label(item_input_frame, text="Produto:").grid(row=0, column=0, padx=5)
        self.var_produto_selecionado = tk.StringVar()
        self.cb_produto = ttk.Combobox(item_input_frame, textvariable=self.var_produto_selecionado, state="readonly",
                                       width=30)
        self.cb_produto.grid(row=0, column=1, padx=5)

        ttk.Label(item_input_frame, text="Qtd:").grid(row=0, column=2, padx=5)
        self.var_quantidade = tk.StringVar()
        ttk.Entry(item_input_frame, textvariable=self.var_quantidade, width=8).grid(row=0, column=3, padx=5)

        ttk.Label(item_input_frame, text="Preço Unit.:").grid(row=0, column=4, padx=5)
        self.var_preco_unit = tk.StringVar(value="0.00")
        ttk.Entry(item_input_frame, textvariable=self.var_preco_unit, width=12).grid(row=0, column=5, padx=5)

        ttk.Button(item_input_frame, text="Adicionar Item", command=self._adicionar_item, style='Accent.TButton').grid(
            row=0, column=6, padx=10)

        # Seção de Lista de Itens
        list_frame = ttk.Frame(frame, padding="5")
        list_frame.pack(fill="both", expand=True)

        self.tree_itens = ttk.Treeview(list_frame,
                                       columns=("Produto ID", "Produto", "Quantidade", "Preço Unit.", "Subtotal"),
                                       show="headings")
        self.tree_itens.heading("Produto ID", text="ID", anchor="center")
        self.tree_itens.heading("Produto", text="Produto")
        self.tree_itens.heading("Quantidade", text="Qtd", anchor="center")
        self.tree_itens.heading("Preço Unit.", text="Preço R$", anchor="e")
        self.tree_itens.heading("Subtotal", text="Subtotal R$", anchor="e")

        self.tree_itens.column("Produto ID", width=50, anchor="center")
        self.tree_itens.column("Produto", width=250, anchor="w")
        self.tree_itens.column("Quantidade", width=60, anchor="center")
        self.tree_itens.column("Preço Unit.", width=100, anchor="e")
        self.tree_itens.column("Subtotal", width=120, anchor="e")
        self.tree_itens.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_itens.yview)
        self.tree_itens.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Botões de Itens
        item_buttons_frame = ttk.Frame(list_frame)
        item_buttons_frame.pack(side="right", fill="y", padx=5)
        ttk.Button(item_buttons_frame, text="Remover Item", command=self._remover_item).pack(fill="x", pady=5)

        # Seção de Total
        total_frame = ttk.Frame(frame, padding="10")
        total_frame.pack(fill="x")

        ttk.Label(total_frame, text="TOTAL DO PEDIDO:", font=('Arial', 12, 'bold')).pack(side="left", padx=5)
        self.var_total = tk.StringVar(value="0.00")
        ttk.Label(total_frame, textvariable=self.var_total, font=('Arial', 14, 'bold'), foreground='green').pack(
            side="right", padx=5)

        # Botões Principais (Salvar/Cancelar)
        button_frame = ttk.Frame(frame, padding="10")
        button_frame.pack(fill="x")

        ttk.Button(button_frame, text="Salvar Pedido", command=self._salvar_pedido, style='Accent.TButton').pack(
            side="left", padx=10)
        ttk.Button(button_frame, text="Cancelar", command=self._on_fechar).pack(side="left", padx=10)

    def _carregar_clientes_combobox(self):
        """Carrega clientes no Combobox."""
        sql = "SELECT id, nome FROM clientes ORDER BY nome"
        clientes = executar_comando(sql, fetchall=True)
        nomes_clientes = []
        if clientes:
            for id_c, nome in clientes:
                self.clientes_map[nome] = id_c
                nomes_clientes.append(nome)

        self.cb_cliente['values'] = nomes_clientes
        if nomes_clientes:
            self.cb_cliente.set(nomes_clientes[0])
        else:
            # Não fecha, mas impede a criação do pedido se não houver cliente
            messagebox.showwarning("Aviso", "Nenhum cliente cadastrado. Cadastre um cliente primeiro.")

    def _carregar_produtos_combobox(self):
        """Carrega produtos no Combobox e mapeia ID/Preço."""
        sql = "SELECT id, nome, preco FROM produtos ORDER BY nome"
        produtos = executar_comando(sql, fetchall=True)
        nomes_produtos = []
        self.produtos_map = {}
        if produtos:
            for id_p, nome, preco in produtos:
                self.produtos_map[nome] = (id_p, preco)
                nomes_produtos.append(nome)

        self.cb_produto['values'] = nomes_produtos
        self.cb_produto.bind("<<ComboboxSelected>>", self._selecionar_produto)

    def _selecionar_produto(self, event=None):
        """Preenche o campo de preço ao selecionar um produto."""
        produto_nome = self.var_produto_selecionado.get()
        if produto_nome in self.produtos_map:
            _, preco = self.produtos_map[produto_nome]
            self.var_preco_unit.set(f"{preco:.2f}")
        else:
            self.var_preco_unit.set("0.00")

    def _validar_item(self, produto_nome, quantidade_str, preco_str):
        """Valida os campos de um item antes de adicionar."""
        produto_data = self.produtos_map.get(produto_nome)  # (id, preco) ou None

        if not produto_nome.strip():
            # Permite item customizado se o campo de preço for preenchido manualmente
            if not preco_str.strip():
                return False, "Selecione um produto ou preencha o preço para item customizado."
            produto_id = None
        else:
            # Produto Selecionado
            produto_id = produto_data[0] if produto_data else None

        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0: return False, "Quantidade deve ser um número inteiro positivo."
        except ValueError:
            return False, "Quantidade deve ser um número inteiro válido."

        try:
            # O preço é lido do campo Entry, que pode ter sido preenchido automaticamente ou editado
            preco_unit = float(preco_str.replace(',', '.'))
            if preco_unit <= 0: return False, "Preço unitário deve ser um número positivo."
        except ValueError:
            return False, "Preço unitário deve ser um número decimal válido."

        return True, (produto_id, produto_nome.strip(), quantidade, preco_unit)

    def _adicionar_item(self):
        """Adiciona um item à lista e atualiza a Treeview."""
        produto_nome = self.var_produto_selecionado.get()
        quantidade_str = self.var_quantidade.get()
        preco_str = self.var_preco_unit.get()

        valido, resultado = self._validar_item(produto_nome, quantidade_str, preco_str)

        if not valido:
            messagebox.showwarning("Erro de Item", resultado)
            return

        produto_id, produto_nome_final, quantidade, preco_unit = resultado

        self.itens_pedido.append((produto_id, produto_nome_final, quantidade, preco_unit))
        self._atualizar_lista_e_total()
        self.dados_salvos = False

        # Limpar campos de adição
        self.var_produto_selecionado.set("")
        self.var_quantidade.set("")
        self.var_preco_unit.set("0.00")

    def _remover_item(self):
        """Remove o item selecionado da lista e Treeview."""
        selecionado = self.tree_itens.selection()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um item para remover.")
            return

        try:
            # O iid é o índice na lista itens_pedido
            item_index = int(selecionado[0])
            self.itens_pedido.pop(item_index)
            self._atualizar_lista_e_total()
            self.dados_salvos = False
        except (IndexError, ValueError) as e:
            logging.error(f"Erro ao remover item: {e}")
            messagebox.showerror("Erro", "Falha ao remover item.")

    def _calcular_total(self):
        """Calcula o total do pedido."""
        # item: (produto_id, produto_nome, qtd, preco_unit)
        total = sum(qtd * preco for _, _, qtd, preco in self.itens_pedido)
        return total

    def _atualizar_lista_e_total(self):
        """Recarrega a Treeview de itens e atualiza o total."""
        for item in self.tree_itens.get_children():
            self.tree_itens.delete(item)

        total = 0.0
        # item: (produto_id, produto_nome, qtd, preco_unit)
        for i, (p_id, p_nome, quantidade, preco_unit) in enumerate(self.itens_pedido):
            subtotal = quantidade * preco_unit
            total += subtotal

            # Use o índice 'i' como iid para facilitar a remoção
            self.tree_itens.insert("", "end", iid=i,
                                   values=(
                                   p_id if p_id is not None else "CUST", p_nome, quantidade, f"{preco_unit:.2f}",
                                   f"{subtotal:.2f}"),
                                   tags=('data',))

        self.var_total.set(f"{total:.2f}")

    def _salvar_pedido(self):
        """Salva o Pedido e seus Itens de forma transacional (Lógica Corrigida)."""
        nome_cliente = self.var_cliente.get()
        cliente_id = self.clientes_map.get(nome_cliente)
        data = self.var_data.get()
        total = self._calcular_total()

        if not cliente_id or not self.itens_pedido or not total > 0:
            messagebox.showwarning("Erro", "Cliente, itens e total do pedido são obrigatórios.")
            return

        conn = criar_conexao()
        if conn is None:
            messagebox.showerror("Erro de DB", "Não foi possível conectar ao banco de dados.")
            return

        try:
            # Inicia a Transação
            cursor = conn.cursor()

            # 1. Salvar na tabela PEDIDOS (e capturar o ID)
            sql_pedido = "INSERT INTO pedidos (cliente_id, data, total) VALUES (?, ?, ?)"
            cursor.execute(sql_pedido, (cliente_id, data, total))
            pedido_id = cursor.lastrowid  # CRÍTICO: Capturar o ID

            # 2. Salvar na tabela ITENS_PEDIDO e preparar atualização de estoque
            sql_item = "INSERT INTO itens_pedido (pedido_id, produto_id, produto_nome, quantidade, preco_unit) VALUES (?, ?, ?, ?, ?)"
            sql_estoque = "UPDATE produtos SET estoque = estoque - ? WHERE id = ?"

            updates_estoque = []
            itens_dados_para_db = []

            # item: (produto_id, produto_nome, qtd, preco_unit)
            for item in self.itens_pedido:
                produto_id, produto_nome, quantidade, preco_unit = item

                # Dados para inserção na tabela itens_pedido
                itens_dados_para_db.append((pedido_id, produto_id, produto_nome, quantidade, preco_unit))

                # Dados para atualização de estoque (apenas se houver ID de produto)
                if produto_id is not None:
                    # Verifica se o estoque não ficará negativo (UX/Validação)
                    produto_atual = executar_comando("SELECT estoque FROM produtos WHERE id = ?", (produto_id,),
                                                     fetchone=True)
                    if produto_atual and produto_atual[0] < quantidade:
                        raise ValueError(f"Estoque insuficiente para {produto_nome}. Disponível: {produto_atual[0]}.")

                    updates_estoque.append((quantidade, produto_id))

            # Executa inserção de todos os itens
            cursor.executemany(sql_item, itens_dados_para_db)

            # Executa atualização de estoque
            if updates_estoque:
                cursor.executemany(sql_estoque, updates_estoque)

            # 3. Finaliza a Transação
            conn.commit()
            self.dados_salvos = True
            messagebox.showinfo("Sucesso", f"Pedido #{pedido_id} salvo com sucesso! Estoque atualizado.")
            if self.recarregar_callback:
                self.recarregar_callback()
            self.destroy()

        except ValueError as ve:
            # Erro de validação de estoque, usa o rollback implícito no finally/except
            conn.rollback()
            logging.warning(f"Erro de Validação (Estoque): {ve}")
            messagebox.showwarning("Aviso de Estoque", str(ve))

        except Error as e:
            # Outros erros de DB, garante rollback
            conn.rollback()
            logging.error(f"Erro transacional ao salvar pedido: {e}")
            messagebox.showerror("Erro de Transação", f"Falha ao salvar o pedido: {e}")

        finally:
            if conn:
                conn.close()

    def _on_fechar(self):
        """Prevenção de fechar janela com dados não salvos."""
        if not self.dados_salvos:
            if messagebox.askyesno("Confirmar", "Há itens de pedido não salvos. Deseja realmente fechar?"):
                self.destroy()
        else:
            self.destroy()