"""
web_app.py - Interface web (Flask) do Sistema de Gestao de Loja
Dashboard moderno e minimalista para gerenciar estoque, vendas, clientes,
fornecedores e relatorios.
"""
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file

from database import inicializar_banco
import estoque
import clientes
import vendas
import fornecedores
import relatorios
import auth
from recibo import gerar_recibo_pdf

app = Flask(__name__)
app.secret_key = "troque-esta-chave-em-producao"


def login_necessario(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if auth.usuario_existe() and "usuario" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if not auth.usuario_existe():
        return redirect(url_for("registrar"))

    if request.method == "POST":
        usuario = auth.autenticar(request.form["username"], request.form["senha"])
        if usuario:
            session["usuario"] = usuario["username"]
            return redirect(url_for("dashboard"))
        flash("Usuario ou senha invalidos.", "erro")
    return render_template("login.html")


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if auth.usuario_existe():
        return redirect(url_for("login"))

    if request.method == "POST":
        auth.criar_usuario(
            request.form["username"], request.form["senha"], request.form.get("nome")
        )
        flash("Usuario criado! Faca login.", "sucesso")
        return redirect(url_for("login"))
    return render_template("registrar.html")


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))


@app.route("/")
@login_necessario
def dashboard():
    resumo = relatorios.resumo_dashboard()
    vendas_semana = relatorios.vendas_por_dia(7)
    estoque_critico = relatorios.relatorio_estoque_critico()
    return render_template(
        "dashboard.html",
        resumo=resumo,
        vendas_semana=vendas_semana,
        estoque_critico=estoque_critico,
    )


@app.route("/estoque")
@login_necessario
def pagina_estoque():
    produtos = estoque.listar_produtos()
    return render_template("estoque.html", produtos=produtos)


@app.route("/estoque/novo", methods=["POST"])
@login_necessario
def novo_produto():
    estoque.cadastrar_produto(
        nome=request.form["nome"],
        categoria=request.form.get("categoria"),
        preco_custo=float(request.form.get("preco_custo") or 0),
        preco_venda=float(request.form["preco_venda"]),
        quantidade=int(request.form.get("quantidade") or 0),
        estoque_minimo=int(request.form.get("estoque_minimo") or 5),
    )
    flash("Produto cadastrado com sucesso.", "sucesso")
    return redirect(url_for("pagina_estoque"))


@app.route("/estoque/<int:produto_id>/repor", methods=["POST"])
@login_necessario
def repor_produto(produto_id):
    estoque.repor_estoque(produto_id, int(request.form["quantidade"]))
    flash("Estoque reposto.", "sucesso")
    return redirect(url_for("pagina_estoque"))


@app.route("/estoque/<int:produto_id>/remover", methods=["POST"])
@login_necessario
def remover_produto(produto_id):
    estoque.remover_produto(produto_id)
    flash("Produto removido.", "sucesso")
    return redirect(url_for("pagina_estoque"))


@app.route("/clientes")
@login_necessario
def pagina_clientes():
    lista = clientes.listar_clientes()
    return render_template("clientes.html", clientes=lista)


@app.route("/clientes/novo", methods=["POST"])
@login_necessario
def novo_cliente():
    clientes.cadastrar_cliente(
        nome=request.form["nome"],
        telefone=request.form.get("telefone"),
        email=request.form.get("email"),
    )
    flash("Cliente cadastrado com sucesso.", "sucesso")
    return redirect(url_for("pagina_clientes"))


@app.route("/clientes/<int:cliente_id>")
@login_necessario
def detalhe_cliente(cliente_id):
    cliente = clientes.buscar_cliente(cliente_id)
    historico = clientes.historico_compras(cliente_id)
    return render_template("cliente_detalhe.html", cliente=cliente, historico=historico)


@app.route("/clientes/<int:cliente_id>/remover", methods=["POST"])
@login_necessario
def remover_cliente(cliente_id):
    clientes.remover_cliente(cliente_id)
    flash("Cliente removido.", "sucesso")
    return redirect(url_for("pagina_clientes"))


@app.route("/vendas")
@login_necessario
def pagina_vendas():
    lista = vendas.listar_vendas()
    produtos = estoque.listar_produtos()
    lista_clientes = clientes.listar_clientes()
    return render_template("vendas.html", vendas=lista, produtos=produtos, clientes=lista_clientes)


@app.route("/vendas/nova", methods=["POST"])
@login_necessario
def nova_venda():
    produto_ids = request.form.getlist("produto_id")
    quantidades = request.form.getlist("quantidade")
    itens = [
        {"produto_id": int(pid), "quantidade": int(qtd)}
        for pid, qtd in zip(produto_ids, quantidades) if pid and qtd
    ]
    cliente_id = request.form.get("cliente_id") or None
    forma_pagamento = request.form.get("forma_pagamento") or "dinheiro"

    try:
        venda_id, total = vendas.registrar_venda(
            itens, int(cliente_id) if cliente_id else None, forma_pagamento
        )
        flash(f"Venda #{venda_id} registrada. Total: R$ {total:.2f}", "sucesso")
    except ValueError as e:
        flash(str(e), "erro")
    return redirect(url_for("pagina_vendas"))


@app.route("/vendas/<int:venda_id>")
@login_necessario
def detalhe_venda(venda_id):
    venda, itens = vendas.detalhes_venda(venda_id)
    return render_template("venda_detalhe.html", venda=venda, itens=itens)


@app.route("/vendas/<int:venda_id>/cancelar", methods=["POST"])
@login_necessario
def cancelar_venda(venda_id):
    vendas.cancelar_venda(venda_id)
    flash("Venda cancelada e estoque restaurado.", "sucesso")
    return redirect(url_for("pagina_vendas"))


@app.route("/vendas/<int:venda_id>/recibo")
@login_necessario
def recibo_venda(venda_id):
    caminho = gerar_recibo_pdf(venda_id, f"/tmp/recibo_{venda_id}.pdf")
    return send_file(caminho, as_attachment=True, download_name=f"recibo_venda_{venda_id}.pdf")


@app.route("/fornecedores")
@login_necessario
def pagina_fornecedores():
    lista = fornecedores.listar_fornecedores()
    compras = fornecedores.listar_compras()
    produtos = estoque.listar_produtos()
    return render_template("fornecedores.html", fornecedores=lista, compras=compras, produtos=produtos)


@app.route("/fornecedores/novo", methods=["POST"])
@login_necessario
def novo_fornecedor():
    fornecedores.cadastrar_fornecedor(
        nome=request.form["nome"],
        telefone=request.form.get("telefone"),
        email=request.form.get("email"),
        cnpj=request.form.get("cnpj"),
    )
    flash("Fornecedor cadastrado.", "sucesso")
    return redirect(url_for("pagina_fornecedores"))


@app.route("/fornecedores/compra", methods=["POST"])
@login_necessario
def nova_compra():
    fornecedores.registrar_compra(
        produto_id=int(request.form["produto_id"]),
        quantidade=int(request.form["quantidade"]),
        preco_unitario=float(request.form["preco_unitario"]),
        fornecedor_id=int(request.form["fornecedor_id"]) if request.form.get("fornecedor_id") else None,
    )
    flash("Compra registrada e estoque atualizado.", "sucesso")
    return redirect(url_for("pagina_fornecedores"))


@app.route("/relatorios")
@login_necessario
def pagina_relatorios():
    hoje = date.today().isoformat()
    inicio_mes = date.today().replace(day=1).isoformat()
    mais_vendidos = relatorios.produtos_mais_vendidos()
    top_clientes = relatorios.clientes_top()
    lucro = relatorios.lucro_periodo(inicio_mes, hoje)
    estoque_critico = relatorios.relatorio_estoque_critico()
    vendas_semana = relatorios.vendas_por_dia(7)
    return render_template(
        "relatorios.html",
        mais_vendidos=mais_vendidos,
        top_clientes=top_clientes,
        lucro=lucro,
        estoque_critico=estoque_critico,
        vendas_semana=vendas_semana,
    )


if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True)
