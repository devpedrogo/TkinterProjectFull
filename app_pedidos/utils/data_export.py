# utils/data_export.py
import csv
import logging
from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def exportar_pedido_csv(pedido_id, dados_pedido, itens_pedido):
    """Exporta um pedido para CSV."""

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile=f"pedido_{pedido_id}.csv"
    )

    if not file_path:
        return

    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Cabeçalho do Pedido
            writer.writerow(["Pedido ID:", pedido_id])
            writer.writerow(["Cliente:", dados_pedido['nome_cliente']])
            writer.writerow(["Data:", dados_pedido['data']])
            writer.writerow(["Total:", f"R$ {dados_pedido['total']:.2f}"])
            writer.writerow([])

            # Cabeçalho dos Itens
            writer.writerow(["Produto", "Quantidade", "Preco Unitario", "Subtotal"])

            # Itens
            for produto, qtd, preco in itens_pedido:
                subtotal = qtd * preco
                writer.writerow([produto, qtd, f"{preco:.2f}", f"{subtotal:.2f}"])

        messagebox.showinfo("Sucesso", f"Pedido exportado para CSV em:\n{file_path}")
    except Exception as e:
        logging.error(f"Erro ao exportar CSV: {e}")
        messagebox.showerror("Erro", f"Falha ao exportar para CSV: {e}")


def exportar_pedido_pdf(pedido_id, dados_pedido, itens_pedido):
    """Exporta um pedido para PDF simples (Requer reportlab)."""
    # Instalação: pip install reportlab

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile=f"pedido_{pedido_id}.pdf"
    )

    if not file_path:
        return

    try:
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter  # 612x792

        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"Detalhes do Pedido #{pedido_id}")

        # Dados do Pedido
        c.setFont("Helvetica", 12)
        y = height - 80
        c.drawString(50, y, f"Cliente: {dados_pedido['nome_cliente']}")
        c.drawString(50, y - 20, f"Data: {dados_pedido['data']}")

        # Tabela de Itens (simplificada)
        c.setFont("Helvetica-Bold", 10)
        y -= 50
        c.drawString(50, y, "Produto")
        c.drawString(250, y, "Qtd")
        c.drawString(350, y, "Preço Unit.")
        c.drawString(500, y, "Subtotal")

        c.setFont("Helvetica", 10)
        y -= 15
        for produto, qtd, preco in itens_pedido:
            subtotal = qtd * preco
            c.drawString(50, y, produto)
            c.drawString(250, y, str(qtd))
            c.drawString(350, y, f"R$ {preco:.2f}")
            c.drawString(500, y, f"R$ {subtotal:.2f}")
            y -= 15

        # Total
        y -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"TOTAL DO PEDIDO: R$ {dados_pedido['total']:.2f}")

        c.save()

        messagebox.showinfo("Sucesso", f"Pedido exportado para PDF em:\n{file_path}")

    except ImportError:
        messagebox.showerror("Erro", "A biblioteca 'reportlab' não está instalada. Execute 'pip install reportlab'.")
    except Exception as e:
        logging.error(f"Erro ao exportar PDF: {e}")
        messagebox.showerror("Erro", f"Falha ao exportar para PDF: {e}")

# --- FILTRO POR INTERVALO DE DATAS (Implementação no main.py ou em uma nova view) ---
# O filtro por intervalo de datas deve ser implementado na view (main.py ou nova)
# que lista os pedidos (você ainda não criou uma view de lista de pedidos, mas a lógica SQL seria:
#
# def buscar_pedidos_por_data(data_inicio, data_fim):
#     sql = "SELECT * FROM pedidos WHERE data BETWEEN ? AND ?"
#     return executar_comando(sql, (data_inicio, data_fim), fetchall=True)
#
# Isso envolveria adicionar campos de data_inicio e data_fim e um botão de filtro
# na sua lista de pedidos.