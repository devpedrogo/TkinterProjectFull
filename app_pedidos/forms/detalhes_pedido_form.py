# forms/detalhes_pedido_form.py
import tkinter as tk
from tkinter import ttk, messagebox
from db import executar_comando
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DetalhesPedidoForm(tk.Toplevel):
    def __init__(self, parent, pedido_id):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.parent = parent
        self.pedido_id = pedido_id
        self.title(f"Detalhes do Pedido #{pedido_id}")
        self.geometry("600x450")

        # Dados do pedido principal (para título)
        self.dados_pedido = self._carregar_dados_principais()

        if not self.dados_pedido:
            messagebox.showerror("Erro", "Pedido não encontrado.")
            self.destroy()
            return

        self.setup_ui()
        self._carregar_itens_pedido()

    def _carregar_dados_principais(self):
        """Busca ID, Cliente e Total para exibir no cabeçalho."""
        sql = """
            SELECT p.id, c.nome, p.data, p.total
            FROM pedidos p
            INNER JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = ?
        """
        return executar_comando(sql, (self.pedido_id,), fetchone=True)

    def setup_ui(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill="both", expand=True)

        # Cabeçalho
        pedido_id, nome_cliente, data, total = self.dados_pedido

        ttk.Label(frame, text=f"Pedido: #{pedido_id}", font=('Arial', 14, 'bold')).pack(anchor='w', pady=(0, 5))
        ttk.Label(frame, text=f"Cliente: {nome_cliente}").pack(anchor='w')
        ttk.Label(frame, text=f"Data: {data}").pack(anchor='w')
        ttk.Label(frame, text=f"TOTAL: R$ {total:.2f}", font=('Arial', 12, 'bold'), foreground='green').pack(anchor='e',
                                                                                                             pady=(
                                                                                                             5, 15))

        ttk.Label(frame, text="ITENS DO PEDIDO:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(5, 0))

        # Lista de Itens (Treeview)
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True)

        self.tree_itens = ttk.Treeview(list_frame, columns=("Produto", "Qtd", "Preço Unit.", "Subtotal"),
                                       show="headings")
        self.tree_itens.heading("Produto", text="Produto")
        self.tree_itens.heading("Qtd", text="Qtd", anchor="center")
        self.tree_itens.heading("Preço Unit.", text="Preço Unit. R$", anchor="e")
        self.tree_itens.heading("Subtotal", text="Subtotal R$", anchor="e")

        self.tree_itens.column("Produto", width=250, anchor="w")
        self.tree_itens.column("Qtd", width=60, anchor="center")
        self.tree_itens.column("Preço Unit.", width=100, anchor="e")
        self.tree_itens.column("Subtotal", width=120, anchor="e")
        self.tree_itens.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_itens.yview)
        self.tree_itens.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(frame, text="Fechar", command=self.destroy).pack(pady=10)

    def _carregar_itens_pedido(self):
        """Busca e exibe os itens associados ao ID do pedido."""
        sql = """
            SELECT 
                produto_nome, 
                quantidade, 
                preco_unit 
            FROM itens_pedido 
            WHERE pedido_id = ?
        """

        try:
            itens = executar_comando(sql, (self.pedido_id,), fetchall=True)
            if itens:
                for nome, qtd, preco_unit in itens:
                    subtotal = qtd * preco_unit

                    self.tree_itens.insert("", "end",
                                           values=(nome, qtd, f"{preco_unit:.2f}", f"{subtotal:.2f}"))
            else:
                self.tree_itens.insert("", "end", values=("Nenhum item encontrado", "", "", ""), tags=('empty',))

        except Exception as e:
            logging.error(f"Erro ao carregar itens do pedido {self.pedido_id}: {e}")
            messagebox.showerror("Erro de DB", f"Falha ao carregar itens: {e}")