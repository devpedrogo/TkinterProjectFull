import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime
import os
import csv
# A biblioteca 'reportlab' deve ser instalada: pip install reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from db import executar_comando, buscar_pedidos_relatorio

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RelatoriosForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gerador de Relatórios de Pedidos")
        self.geometry("1000x700")
        self.parent = parent
        self.grab_set()  # Torna a janela modal

        # Armazena os dados brutos para exportação CSV/PDF
        self.pedidos_detalhados = {}

        self._setup_ui()
        self.carregar_clientes()
        self.recarregar_pedidos()  # Carrega dados iniciais

    def _setup_ui(self):
        # --- Frame Principal de Filtros ---
        frame_filtros = ttk.LabelFrame(self, text="Filtros de Relatório", padding="10")
        frame_filtros.pack(fill="x", padx=10, pady=10)

        # Labels e Entradas
        ttk.Label(frame_filtros, text="Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame_filtros, text="Data Inicial (AAAA-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Label(frame_filtros, text="Data Final (AAAA-MM-DD):").grid(row=0, column=4, padx=5, pady=5, sticky="w")

        # Cliente ComboBox
        self.clientes_map = {"Todos": None}
        self.var_cliente = tk.StringVar(value="Todos")
        self.combo_cliente = ttk.Combobox(frame_filtros, textvariable=self.var_cliente, state="readonly", width=30)
        self.combo_cliente.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        # Datas
        self.var_data_inicio = tk.StringVar()
        self.entry_data_inicio = ttk.Entry(frame_filtros, textvariable=self.var_data_inicio, width=15)
        self.entry_data_inicio.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        self.var_data_fim = tk.StringVar()
        self.entry_data_fim = ttk.Entry(frame_filtros, textvariable=self.var_data_fim, width=15)
        self.entry_data_fim.grid(row=1, column=4, padx=5, pady=5, sticky="w")

        # Botão de Busca
        ttk.Button(frame_filtros, text="Buscar Pedidos", command=self.recarregar_pedidos, style='Accent.TButton').grid(
            row=1, column=5, padx=10, pady=5, sticky="e")

        # Configurar expansão de colunas
        frame_filtros.grid_columnconfigure(5, weight=1)

        # --- Treeview de Pedidos ---
        list_frame = ttk.Frame(self, padding="10")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        colunas = ("ID", "Cliente", "Data", "Itens", "Total")
        self.tree_pedidos = ttk.Treeview(list_frame, columns=colunas, show="headings")
        self.tree_pedidos.heading("ID", text="ID");
        self.tree_pedidos.column("ID", width=60, anchor="center")
        self.tree_pedidos.heading("Cliente", text="Cliente");
        self.tree_pedidos.column("Cliente", width=200)
        self.tree_pedidos.heading("Data", text="Data");
        self.tree_pedidos.column("Data", width=100, anchor="center")
        self.tree_pedidos.heading("Itens", text="Itens");
        self.tree_pedidos.column("Itens", width=350)
        self.tree_pedidos.heading("Total", text="Total R$");
        self.tree_pedidos.column("Total", width=120, anchor="e")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_pedidos.yview)
        self.tree_pedidos.configure(yscrollcommand=scrollbar.set)

        self.tree_pedidos.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Frame de Exportação ---
        frame_exportacao = ttk.Frame(self, padding="10")
        frame_exportacao.pack(fill="x", padx=10, pady=10)

        ttk.Button(frame_exportacao, text="Exportar para CSV", command=self.exportar_csv).pack(side="left", padx=5)
        ttk.Button(frame_exportacao, text="Exportar para PDF", command=self.exportar_pdf).pack(side="left", padx=5)

    def carregar_clientes(self):
        """Busca clientes no DB e popula o ComboBox."""
        sql = "SELECT id, nome FROM clientes ORDER BY nome"
        try:
            clientes = executar_comando(sql, fetchall=True)
            self.clientes_map = {"Todos": None}
            if clientes:
                for id, nome in clientes:
                    self.clientes_map[nome] = id

            self.combo_cliente['values'] = list(self.clientes_map.keys())
            self.combo_cliente.current(0)
        except Exception as e:
            logging.error(f"Erro ao carregar clientes para o relatório: {e}")
            messagebox.showerror("Erro de DB", "Não foi possível carregar a lista de clientes.")

    def recarregar_pedidos(self):
        """Busca pedidos no DB com base nos filtros e atualiza a Treeview."""
        for item in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(item)

        cliente_selecionado = self.var_cliente.get()
        cliente_id = self.clientes_map.get(cliente_selecionado)
        data_inicio = self.var_data_inicio.get()
        data_fim = self.var_data_fim.get()

        # Validação de data (formato AAAA-MM-DD)
        try:
            if data_inicio: datetime.strptime(data_inicio, "%Y-%m-%d")
            if data_fim: datetime.strptime(data_fim, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Filtro Inválido", "As datas devem estar no formato AAAA-MM-DD.")
            return

        # Busca dados detalhados (função implementada em db.py)
        pedidos = buscar_pedidos_relatorio(data_inicio, data_fim, cliente_id)
        self.pedidos_detalhados = pedidos

        if not pedidos:
            self.tree_pedidos.insert("", "end", values=("", "Nenhum pedido encontrado.", "", "", ""), tags=('empty',))
            return

        for pedido_id, dados in pedidos.items():
            cliente = dados['cliente']
            data = dados['data']
            total = f"{dados['total']:.2f}".replace('.', ',')

            # Formata a string de itens para exibição
            itens_str = ", ".join([f"{item['quantidade']}x {item['nome']}" for item in dados['itens']])

            self.tree_pedidos.insert(
                "",
                "end",
                iid=pedido_id,
                values=(pedido_id, cliente, data, itens_str, total)
            )

    def exportar_csv(self):
        """Exporta os dados atualmente carregados para um arquivo CSV."""
        if not self.pedidos_detalhados:
            messagebox.showinfo("Exportar", "Nenhum dado para exportar. Busque pedidos primeiro.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Salvar Relatório CSV"
        )

        if not filepath: return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')  # Usando ';' como delimitador
                # Cabeçalho Detalhado do CSV
                writer.writerow(["ID Pedido", "Cliente", "Data Pedido", "Total Pedido (R$)",
                                 "ID Item", "Nome Produto", "Quantidade", "Preço Unitário (R$)"])

                # Escreve os dados linha por linha (um item por linha)
                for pedido_id, dados in self.pedidos_detalhados.items():
                    cliente = dados['cliente']
                    data = dados['data']
                    total = f"{dados['total']:.2f}".replace('.', ',')

                    for item in dados['itens']:
                        item_id = item['id']
                        nome = item['nome']
                        qtd = item['quantidade']
                        preco_unit = f"{item['preco_unit']:.2f}".replace('.', ',')

                        writer.writerow([pedido_id, cliente, data, total, item_id, nome, qtd, preco_unit])

            messagebox.showinfo("Sucesso", f"Relatório CSV exportado com sucesso para:\n{filepath}")
            self._abrir_arquivo(filepath)

        except Exception as e:
            logging.error(f"Erro ao exportar CSV: {e}")
            messagebox.showerror("Erro de Exportação", f"Ocorreu um erro ao salvar o arquivo CSV: {e}")

    def exportar_pdf(self):
        """Exporta os dados atualmente carregados para um arquivo PDF usando reportlab."""
        if not self.pedidos_detalhados:
            messagebox.showinfo("Exportar", "Nenhum dado para exportar. Busque pedidos primeiro.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Salvar Relatório PDF"
        )

        if not filepath: return

        try:
            pdf = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter

            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(inch, height - inch, "Relatório de Pedidos Detalhados")
            pdf.setFont("Helvetica", 10)
            pdf.drawString(inch, height - inch - 0.3 * inch, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

            y_pos = height - inch - 0.7 * inch
            x_pos = inch
            line_height = 0.25 * inch

            for pedido_id, dados in self.pedidos_detalhados.items():
                cliente = dados['cliente']
                data = dados['data']
                total = f"R$ {dados['total']:.2f}".replace('.', ',')

                # Nova página se necessário
                if y_pos < 1.5 * inch:
                    pdf.showPage()
                    y_pos = height - inch
                    pdf.setFont("Helvetica-Bold", 12)
                    pdf.drawString(inch, y_pos, "Relatório de Pedidos (Continuação)")
                    y_pos -= line_height

                # Informações do Pedido
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(x_pos, y_pos,
                               f"Pedido ID: {pedido_id} | Cliente: {cliente} | Data: {data} | TOTAL: {total}")
                y_pos -= line_height

                # Cabeçalho dos Itens
                pdf.setFont("Helvetica-Oblique", 9)
                pdf.drawString(x_pos + 0.5 * inch, y_pos, "Produto")
                pdf.drawString(x_pos + 4.5 * inch, y_pos, "Qtd.")
                pdf.drawString(x_pos + 5.5 * inch, y_pos, "Preço Unit.")
                pdf.drawString(x_pos + 7.0 * inch, y_pos, "Subtotal")
                y_pos -= line_height * 0.8

                # Loop pelos Itens
                for item in dados['itens']:
                    nome = item['nome']
                    qtd = item['quantidade']
                    preco_unit = item['preco_unit']
                    subtotal = qtd * preco_unit

                    pdf.setFont("Helvetica", 9)
                    pdf.drawString(x_pos + 0.5 * inch, y_pos, nome)
                    pdf.drawString(x_pos + 4.5 * inch, y_pos, str(qtd))
                    pdf.drawString(x_pos + 5.5 * inch, y_pos, f"R$ {preco_unit:.2f}".replace('.', ','))
                    pdf.drawString(x_pos + 7.0 * inch, y_pos, f"R$ {subtotal:.2f}".replace('.', ','))

                    y_pos -= line_height

                    if y_pos < 1.5 * inch:
                        pdf.showPage()
                        y_pos = height - inch
                        pdf.setFont("Helvetica", 9)

                y_pos -= line_height * 0.5

            pdf.save()
            messagebox.showinfo("Sucesso", f"Relatório PDF exportado com sucesso para:\n{filepath}")
            self._abrir_arquivo(filepath)

        except ImportError:
            messagebox.showerror("Erro de Dependência",
                                 "A biblioteca 'reportlab' não está instalada. Instale com 'pip install reportlab'.")
        except Exception as e:
            logging.error(f"Erro ao exportar PDF: {e}")
            messagebox.showerror("Erro de Exportação", f"Ocorreu um erro ao salvar o arquivo PDF: {e}")

    def _abrir_arquivo(self, filepath):
        """Tenta abrir o arquivo gerado usando o programa padrão do sistema."""
        if not filepath: return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.uname()[0] == 'Darwin':  # macOS
                os.system(f'open "{filepath}"')
            else:  # Linux
                os.system(f'xdg-open "{filepath}"')
        except Exception as e:
            logging.warning(f"Não foi possível abrir o arquivo automaticamente: {e}")