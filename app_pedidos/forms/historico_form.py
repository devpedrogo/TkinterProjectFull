# forms/historico_form.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from utils.log_manager import ler_historico, limpar_arquivo_log


class HistoricoForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Histórico de Ações do Sistema")
        self.geometry("800x600")
        self.parent = parent
        self.grab_set()

        self.setup_ui()
        self.carregar_historico()

    def setup_ui(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Eventos Registrados (Mais Recentes Primeiro):", font=('Arial', 12, 'bold')).pack(
            anchor='w', pady=(0, 5))

        # Widget de Texto com Rolagem
        self.text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=100, height=30, font=('Courier', 10))
        self.text_widget.pack(fill="both", expand=True)
        self.text_widget.config(state=tk.DISABLED)

        # Frame de Botões
        button_frame = ttk.Frame(frame, padding="5")
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Limpar Histórico", command=self.limpar_historico_ui, style='TButton').pack(
            side="left", padx=5)
        ttk.Button(button_frame, text="Atualizar", command=self.carregar_historico, style='Accent.TButton').pack(
            side="right", padx=5)
        ttk.Button(button_frame, text="Fechar", command=self.destroy).pack(side="right", padx=5)

    def carregar_historico(self):
        """Lê o arquivo de log e exibe no widget de texto."""
        historico = ler_historico()

        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)

        # Insere todas as linhas do log
        self.text_widget.insert(tk.END, "".join(historico))

        self.text_widget.config(state=tk.DISABLED)

    def limpar_historico_ui(self):
        """Pede confirmação e limpa o arquivo de log."""
        if messagebox.askyesno("Confirmar Limpeza",
                               "Tem certeza que deseja apagar TODO o histórico de ações? Esta ação é irreversível."):
            if limpar_arquivo_log():
                messagebox.showinfo("Sucesso", "Histórico de ações limpo.")
                self.carregar_historico()
            else:
                messagebox.showerror("Erro", "Não foi possível limpar o arquivo de log.")