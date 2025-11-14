# forms/cliente_form.py (ATUALIZADO com Log de Ações)
import tkinter as tk
from tkinter import ttk, messagebox
from db import executar_comando
from utils.validations import validar_nome, validar_email, validar_telefone
# NOVO:
from utils.log_manager import registrar_acao


class ClienteForm(tk.Toplevel):
    def __init__(self, parent, cliente_id=None, recarregar_callback=None):
        super().__init__(parent)
        self.transient(parent)  # Faz a janela ser dependente da principal
        self.grab_set()  # Torna a janela modal
        self.parent = parent
        self.cliente_id = cliente_id
        self.recarregar_callback = recarregar_callback

        self.title("Novo Cliente" if cliente_id is None else "Editar Cliente")
        self.protocol("WM_DELETE_WINDOW", self._on_fechar)  # Previne fechar com dados não salvos

        self.dados_salvos = True  # Flag para controle de fechamento

        self.setup_ui()

        if self.cliente_id is not None:
            self._carregar_dados_cliente()

    def setup_ui(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)

        # Variáveis de controle
        self.var_nome = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_telefone = tk.StringVar()

        # Monitora alterações para controle de fechamento
        self.var_nome.trace_add("write", lambda *args: self._marcar_alteracao())
        self.var_email.trace_add("write", lambda *args: self._marcar_alteracao())
        self.var_telefone.trace_add("write", lambda *args: self._marcar_alteracao())

        # Campos
        ttk.Label(frame, text="Nome*:", anchor="w").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.entry_nome = ttk.Entry(frame, textvariable=self.var_nome, width=40)
        self.entry_nome.grid(row=0, column=1, sticky="we", pady=5, padx=5)
        self.label_nome_erro = ttk.Label(frame, text="", foreground="red")
        self.label_nome_erro.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(frame, text="E-mail:", anchor="w").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.entry_email = ttk.Entry(frame, textvariable=self.var_email, width=40)
        self.entry_email.grid(row=2, column=1, sticky="we", pady=5, padx=5)
        self.label_email_erro = ttk.Label(frame, text="", foreground="red")
        self.label_email_erro.grid(row=3, column=1, sticky="w", padx=5)

        ttk.Label(frame, text="Telefone:", anchor="w").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.entry_telefone = ttk.Entry(frame, textvariable=self.var_telefone, width=40)
        self.entry_telefone.grid(row=4, column=1, sticky="we", pady=5, padx=5)
        self.label_telefone_erro = ttk.Label(frame, text="", foreground="red")
        self.label_telefone_erro.grid(row=5, column=1, sticky="w", padx=5)

        # Botões (callback separado)
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Salvar", command=self._salvar_cliente).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Cancelar", command=self._cancelar).pack(side="left", padx=10)

        self.entry_nome.focus_set()

    def _marcar_alteracao(self):
        """Marca que houve alteração nos dados."""
        self.dados_salvos = False

    def _carregar_dados_cliente(self):
        """Carrega os dados do cliente para edição."""
        sql = "SELECT nome, email, telefone FROM clientes WHERE id = ?"
        cliente = executar_comando(sql, (self.cliente_id,), fetchone=True)
        if cliente:
            self.var_nome.set(cliente[0])
            self.var_email.set(cliente[1] or "")
            self.var_telefone.set(cliente[2] or "")
            self.dados_salvos = True  # Dados carregados, não alterados ainda
        else:
            messagebox.showerror("Erro", "Cliente não encontrado.")
            self.destroy()

    def _validar_e_exibir_erros(self, nome, email, telefone):
        """Realiza todas as validações e retorna True se OK."""
        erros = False

        # Limpa mensagens de erro
        self.label_nome_erro.config(text="")
        self.label_email_erro.config(text="")
        self.label_telefone_erro.config(text="")

        # 1. Validação do Nome (Obrigatório)
        if not validar_nome(nome):
            self.label_nome_erro.config(text="Nome é obrigatório.")
            erros = True

        # 2. Validação do E-mail (Formato simples)
        if email and not validar_email(email):
            self.label_email_erro.config(text="E-mail inválido (formato simples).")
            erros = True

        # 3. Validação do Telefone (8-15 dígitos)
        if telefone and not validar_telefone(telefone):
            self.label_telefone_erro.config(text="Telefone deve ter entre 8 e 15 dígitos.")
            erros = True

        return not erros

    def _salvar_cliente(self):
        """Callback para o botão Salvar. Insere ou atualiza o cliente."""
        nome = self.var_nome.get().strip()
        email = self.var_email.get().strip()
        telefone = self.var_telefone.get().strip()

        if not self._validar_e_exibir_erros(nome, email, telefone):
            messagebox.showwarning("Validação", "Por favor, corrija os erros no formulário.")
            return

        try:
            if self.cliente_id is None:
                # INSERT
                sql = "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)"
                resultado = executar_comando(sql, (nome, email or None, telefone or None))

                if resultado == "IntegrityError":
                    messagebox.showerror("Erro de Salvar", "E-mail já cadastrado para outro cliente.")
                    return
                elif resultado is not None:
                    # LOG DE CRIAÇÃO
                    registrar_acao("CLIENTE", "CRIAR", f"ID {resultado}: {nome}")
                    messagebox.showinfo("Sucesso", "Cliente cadastrado!")
            else:
                # UPDATE
                sql = "UPDATE clientes SET nome = ?, email = ?, telefone = ? WHERE id = ?"
                resultado = executar_comando(sql, (nome, email or None, telefone or None, self.cliente_id))

                if resultado == "IntegrityError":
                    messagebox.showerror("Erro de Salvar", "E-mail já cadastrado para outro cliente.")
                    return
                elif resultado is not None:
                    # LOG DE EDIÇÃO
                    registrar_acao("CLIENTE", "EDITAR", f"ID {self.cliente_id}: {nome}")
                    messagebox.showinfo("Sucesso", "Cliente atualizado!")

            self.dados_salvos = True
            if self.recarregar_callback:
                self.recarregar_callback()
            self.destroy()

        except Exception as e:
            logging.error(f"Erro ao salvar cliente: {e}")
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o cliente: {e}")

    def _cancelar(self):
        """Callback para o botão Cancelar."""
        self._on_fechar()

    def _on_fechar(self):
        """Prevenção de fechar janela com dados não salvos."""
        if not self.dados_salvos:
            if messagebox.askyesno("Confirmar", "Há dados não salvos. Deseja realmente fechar?"):
                self.destroy()
        else:
            self.destroy()