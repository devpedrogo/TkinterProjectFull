# forms/produto_form.py (NOVO)
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from db import executar_comando


class ProdutoForm(tk.Toplevel):
    def __init__(self, parent, produto_id=None, recarregar_callback=None):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.parent = parent
        self.produto_id = produto_id
        self.recarregar_callback = recarregar_callback

        self.title("Novo Produto" if produto_id is None else "Editar Produto")
        self.protocol("WM_DELETE_WINDOW", self._on_fechar)

        self.dados_salvos = True
        self.setup_ui()

        if self.produto_id is not None:
            self._carregar_dados_produto()

    def setup_ui(self):
        # Usando Frame estilizado pelo ttkthemes
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill="both", expand=True)

        # Variáveis de controle
        self.var_nome = tk.StringVar()
        self.var_preco = tk.StringVar()
        self.var_estoque = tk.StringVar(value="0")

        # Monitora alterações
        self.var_nome.trace_add("write", lambda *args: self._marcar_alteracao())
        self.var_preco.trace_add("write", lambda *args: self._marcar_alteracao())
        self.var_estoque.trace_add("write", lambda *args: self._marcar_alteracao())

        # Campos
        ttk.Label(frame, text="Nome*:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(frame, textvariable=self.var_nome, width=40).grid(row=0, column=1, sticky="we", pady=5, padx=5)

        ttk.Label(frame, text="Preço Unit.* (R$):").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(frame, textvariable=self.var_preco, width=40).grid(row=1, column=1, sticky="we", pady=5, padx=5)

        ttk.Label(frame, text="Estoque Inicial/Atual*:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(frame, textvariable=self.var_estoque, width=40).grid(row=2, column=1, sticky="we", pady=5, padx=5)

        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)

        # Usando style='Accent.TButton' para dar destaque ao botão Salvar (UX)
        ttk.Button(button_frame, text="Salvar", command=self._salvar_produto, style='Accent.TButton').pack(side="left",
                                                                                                           padx=10)
        ttk.Button(button_frame, text="Cancelar", command=self._on_fechar).pack(side="left", padx=10)

        self.grab_set()  # Garante modalidade
        self.entry_nome.focus_set()

    def _marcar_alteracao(self):
        self.dados_salvos = False

    def _carregar_dados_produto(self):
        """Carrega os dados do produto para edição."""
        sql = "SELECT nome, preco, estoque FROM produtos WHERE id = ?"
        produto = executar_comando(sql, (self.produto_id,), fetchone=True)
        if produto:
            self.var_nome.set(produto[0])
            self.var_preco.set(f"{produto[1]:.2f}")
            self.var_estoque.set(produto[2])
            self.dados_salvos = True
        else:
            messagebox.showerror("Erro", "Produto não encontrado.")
            self.destroy()

    def _validar_campos(self, nome, preco_str, estoque_str):
        """Realiza validações do produto."""
        if not nome.strip():
            return False, "O Nome do produto é obrigatório."

        try:
            preco = float(preco_str.replace(',', '.'))
            if preco <= 0:
                return False, "O Preço deve ser um valor positivo."
        except ValueError:
            return False, "O Preço deve ser um número decimal válido."

        try:
            estoque = int(estoque_str)
            if estoque < 0:
                return False, "O Estoque não pode ser negativo."
        except ValueError:
            return False, "O Estoque deve ser um número inteiro válido."

        return True, (nome.strip(), preco, estoque)

    def _salvar_produto(self):
        """Salva o produto no DB."""
        nome = self.var_nome.get()
        preco_str = self.var_preco.get()
        estoque_str = self.var_estoque.get()

        valido, resultado = self._validar_campos(nome, preco_str, estoque_str)

        if not valido:
            messagebox.showwarning("Validação", resultado)
            return

        nome, preco, estoque = resultado

        try:
            if self.produto_id is None:
                # INSERT
                sql = "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)"
                resultado_db = executar_comando(sql, (nome, preco, estoque))
                if resultado_db == "IntegrityError":
                    messagebox.showerror("Erro de Salvar", "Produto com este nome já cadastrado.")
                    return
                elif resultado_db is not None:
                    messagebox.showinfo("Sucesso", "Produto cadastrado!")
            else:
                # UPDATE
                sql = "UPDATE produtos SET nome = ?, preco = ?, estoque = ? WHERE id = ?"
                resultado_db = executar_comando(sql, (nome, preco, estoque, self.produto_id))
                if resultado_db == "IntegrityError":
                    messagebox.showerror("Erro de Salvar", "Produto com este nome já cadastrado para outro ID.")
                    return
                elif resultado_db is not None:
                    messagebox.showinfo("Sucesso", "Produto atualizado!")

            self.dados_salvos = True
            if self.recarregar_callback:
                self.recarregar_callback()
            self.destroy()

        except Exception as e:
            logging.error(f"Erro ao salvar produto: {e}")
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o produto: {e}")

    def _on_fechar(self):
        """Prevenção de fechar janela com dados não salvos."""
        if not self.dados_salvos:
            if messagebox.askyesno("Confirmar", "Há dados não salvos. Deseja realmente fechar?"):
                self.destroy()
        else:
            self.destroy()