"""
recibo.py - Geracao de recibos em PDF para vendas
Usa apenas reportlab.
"""
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from vendas import detalhes_venda


def gerar_recibo_pdf(venda_id, caminho_saida=None):
    venda, itens = detalhes_venda(venda_id)
    if not venda:
        raise ValueError("Venda nao encontrada.")

    caminho_saida = caminho_saida or f"recibo_venda_{venda_id}.pdf"
    largura, altura = A5

    c = canvas.Canvas(caminho_saida, pagesize=A5)
    y = altura - 20 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(largura / 2, y, "RECIBO DE VENDA")
    y -= 10 * mm

    c.setFont("Helvetica", 10)
    c.drawString(15 * mm, y, f"Venda #{venda['id']}")
    y -= 6 * mm
    c.drawString(15 * mm, y, f"Data: {venda['data']}")
    y -= 6 * mm
    c.drawString(15 * mm, y, f"Forma de pagamento: {venda['forma_pagamento']}")
    y -= 10 * mm

    c.line(15 * mm, y, largura - 15 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(15 * mm, y, "Produto")
    c.drawString(85 * mm, y, "Qtd")
    c.drawString(100 * mm, y, "Unit.")
    c.drawString(120 * mm, y, "Subtotal")
    y -= 6 * mm
    c.setFont("Helvetica", 9)

    for item in itens:
        c.drawString(15 * mm, y, str(item["produto_nome"])[:35])
        c.drawString(85 * mm, y, str(item["quantidade"]))
        c.drawString(100 * mm, y, f"R$ {item['preco_unitario']:.2f}")
        c.drawString(120 * mm, y, f"R$ {item['subtotal']:.2f}")
        y -= 6 * mm
        if y < 20 * mm:
            c.showPage()
            y = altura - 20 * mm

    y -= 4 * mm
    c.line(15 * mm, y, largura - 15 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(15 * mm, y, f"TOTAL: R$ {venda['total']:.2f}")
    y -= 12 * mm

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(largura / 2, y, "Obrigado pela preferencia!")

    c.save()
    return caminho_saida
