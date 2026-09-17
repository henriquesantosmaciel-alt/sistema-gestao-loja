"""
web_app.py - Interface web (Flask) do LojaOS
Dashboard moderno e minimalista, com autenticacao, controle de papeis
(admin/vendedor), protecao CSRF, cabecalhos de seguranca, limite de
tentativas de login, caixa, financeiro, pedidos/orcamentos e area
fiscal em homologacao (sem emissao real de notas).
"""
from datetime import date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, jsonify
)
from flask_wtf import CSRFProtect

import config
from database import inicializar_banco, DatabaseError
import estoque
import clientes
import vendas
import fornecedores
import relatorios
import auth
import loja_avancada as loja
import seguranca
from validators import ValidationError
from recibo import gerar_recibo_pdf

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE

csrf = CSRFProtect(app)


@app.after_request
def add_security_headers(response):
    return seguranca.aplicar_cabecalhos_seguranca(response)


@app.errorhandler(ValidationError)
def handle_validation_error(erro):
    flash(str(erro), "erro")
    return redirect(request.referrer or url_for("dashboard"))


@app.errorhandler(DatabaseError)
def handle_database_error(erro):
    flash("Ocorreu um erro ao acessar o banco de dados. Tente novamente.", "erro")
    return redirect(request.referrer or url_for("dashboard"))


@app.errorhandler(404)
def handle_404(erro):
    return render_template("erro.html", codigo=404, mensagem="Pagina nao encontrada."), 404


@app.errorhandler(500)
def handle_500(erro):
    return render_template("erro.html", codigo=500, mensagem="Erro interno do servidor."), 500


def login_necessario(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if auth.usuario_existe() and "usuario" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def permissao_necessaria(area):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            papel = session.get("papel", "admin")
            if not auth.tem_permissao(papel, area):
                flash("Voce nao tem permissao para acessar esta area.", "erro")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)
        return wrapper
    return decorador


@app.context_processor
def inject_globals():
    return {"papel_usuario": session.get("papel", "admin"), "caixa_atual": loja.caixa_aberto() if session.get("usuario") else None}


@app.route("/login", methods=["GET", "POST"])
def login():
    if not auth.usuario_existe():
        return redirect(url_for("registrar"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()

        if seguranca.login_bloqueado(username):
            restante = seguranca.segundos_restantes_bloqueio(username)
            flash(f"Muitas tentativas de login. Tente novamente em {restante} segundos.", "erro")
            return render_template("login.html")

        usuario = auth.autenticar(request.form.get("username", ""), request.form.get("senha", ""))
        if usuario:
            seguranca.limpar_tentativas(username)
            session["usuario"] = usuario["username"]
            session["papel"] = usuario["papel"]
            return redirect(url_for("dashboard"))

        seguranca.registrar_falha_login(username)
        flash("Usuario ou senha invalidos.", "erro")
    return render_template("login.html")


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if auth.usuario_existe():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            if request.form.get("senha") != request.form.get("confirmar_senha"):
                raise ValidationError("As senhas informadas nao sao iguais.")
            auth.criar_usuario(request.form["username"], request.form["senha"], request.form.get("nome"), papel="admin")
            flash("Usuario administrador criado! Faca login.", "sucesso")
            return redirect(url_for("login"))
        except ValidationError as e:
            flash(str(e), "erro")
    return render_template("registrar.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_necessario
def dashboard():
    resumo = relatorios.resumo_dashboard()
    vendas_semana = relatorios.vendas_por_dia(7)
    estoque_critico = relatorios.relatorio_estoque_critico()
    valor_estoque = estoque.valor_total_estoque()
    financeiro = loja.resumo_financeiro()
    caixa = loja.caixa_aberto()
    return render_template(
        "dashboard.html", resumo=resumo, vendas_semana=vendas_semana,
        estoque_critico=estoque_critico, valor_estoque=valor_estoque,
        financeiro=financeiro, caixa=caixa,
    )


@app.route("/estoque")
@login_necessario
@permissao_necessaria("estoque")
def pagina_estoque():
    busca = request.args.get("q", "").strip()
    produtos = estoque.listar_produtos(busca=busca or None)
    return render_template("estoque.html", produtos=produtos, busca=busca)


@app.route("/estoque/novo", methods=["POST"])
@login_necessario
@permissao_necessaria("estoque")
def novo_produto():
    estoque.cadastrar_produto(
        nome=request.form.get("nome"), categoria=request.form.get("categoria"),
        preco_custo=request.form.get("preco_custo") or 0, preco_venda=request.form.get("preco_venda"),
        quantidade=request.form.get("quantidade") or 0, estoque_minimo=request.form.get("estoque_minimo") or 5,
    )
    flash("Produto cadastrado com sucesso.", "sucesso")
    return redirect(url_for("pagina_estoque"))


@app.route("/estoque/<int:produto_id>/repor", methods=["POST"])
@login_necessario
@permissao_necessaria("estoque")
def repor_produto(produto_id):
    estoque.repor_estoque(produto_id, request.form.get("quantidade"))
    flash("Estoque reposto.", "sucesso")
    return redirect(url_for("pagina_estoque"))


@app.route("/estoque/<int:produto_id>/remover", methods=["POST"])
@login_necessario
@permissao_necessaria("estoque")
def remover_produto(produto_id):
    estoque.remover_produto(produto_id)
    flash("Produto removido.", "sucesso")
    return redirect(url_for("pagina_estoque"))


@app.route("/clientes")
@login_necessario
@permissao_necessaria("clientes")
def pagina_clientes():
    busca = request.args.get("q", "").strip()
    lista = clientes.listar_clientes(busca or None)
    return render_template("clientes.html", clientes=lista, busca=busca)


@app.route("/clientes/novo", methods=["POST"])
@login_necessario
@permissao_necessaria("clientes")
def novo_cliente():
    clientes.cadastrar_cliente(
        nome=request.form.get("nome"), telefone=request.form.get("telefone"), email=request.form.get("email"),
    )
    flash("Cliente cadastrado com sucesso.", "sucesso")
    return redirect(url_for("pagina_clientes"))


@app.route("/clientes/<int:cliente_id>")
@login_necessario
@permissao_necessaria("clientes")
def detalhe_cliente(cliente_id):
    cliente = clientes.buscar_cliente(cliente_id)
    if not cliente:
        flash("Cliente nao encontrado.", "erro")
        return redirect(url_for("pagina_clientes"))
    historico = clientes.historico_compras(cliente_id)
    stats = clientes.estatisticas_cliente(cliente_id)
    return render_template("cliente_detalhe.html", cliente=cliente, historico=historico, stats=stats)


@app.route("/clientes/<int:cliente_id>/remover", methods=["POST"])
@login_necessario
@permissao_necessaria("clientes")
def remover_cliente(cliente_id):
    clientes.remover_cliente(cliente_id)
    flash("Cliente removido.", "sucesso")
    return redirect(url_for("pagina_clientes"))


@app.route("/vendas")
@login_necessario
@permissao_necessaria("vendas")
def pagina_vendas():
    busca = request.args.get("cliente", "").strip()
    lista = vendas.listar_vendas(busca_cliente=busca or None)
    produtos = estoque.listar_produtos()
    lista_clientes = clientes.listar_clientes()
    return render_template("vendas.html", vendas=lista, produtos=produtos, clientes=lista_clientes, busca=busca)


@app.route("/vendas/nova", methods=["POST"])
@login_necessario
@permissao_necessaria("vendas")
def nova_venda():
    produto_ids = request.form.getlist("produto_id")
    quantidades = request.form.getlist("quantidade")
    itens = [{"produto_id": pid, "quantidade": qtd} for pid, qtd in zip(produto_ids, quantidades) if pid and qtd]
    cliente_id = request.form.get("cliente_id") or None
    forma_pagamento = request.form.get("forma_pagamento") or "dinheiro"
    venda_id, total = vendas.registrar_venda(itens, int(cliente_id) if cliente_id else None, forma_pagamento, vendedor=session.get("usuario"))
    caixa = loja.caixa_aberto()
    if caixa:
        from database import get_connection as _gc
        with _gc() as c:
            c.execute("UPDATE vendas SET caixa_id = ? WHERE id = ?", (caixa["id"], venda_id))
        loja.movimentar_caixa(caixa["id"], "entrada", total, f"Venda #{venda_id}", session.get("usuario"))
    flash(f"Venda #{venda_id} registrada. Total: R$ {total:.2f}", "sucesso")
    return redirect(url_for("pagina_vendas"))


@app.route("/vendas/<int:venda_id>")
@login_necessario
@permissao_necessaria("vendas")
def detalhe_venda(venda_id):
    venda, itens = vendas.detalhes_venda(venda_id)
    if not venda:
        flash("Venda nao encontrada.", "erro")
        return redirect(url_for("pagina_vendas"))
    return render_template("venda_detalhe.html", venda=venda, itens=itens)


@app.route("/vendas/<int:venda_id>/cancelar", methods=["POST"])
@login_necessario
@permissao_necessaria("vendas")
def cancelar_venda(venda_id):
    vendas.cancelar_venda(venda_id)
    flash("Venda cancelada e estoque restaurado.", "sucesso")
    return redirect(url_for("pagina_vendas"))


@app.route("/vendas/<int:venda_id>/recibo")
@login_necessario
@permissao_necessaria("vendas")
def recibo_venda(venda_id):
    import tempfile, os
    caminho = os.path.join(tempfile.gettempdir(), f"recibo_{venda_id}.pdf")
    gerar_recibo_pdf(venda_id, caminho)
    return send_file(caminho, as_attachment=True, download_name=f"recibo_venda_{venda_id}.pdf")


@app.route("/fornecedores")
@login_necessario
@permissao_necessaria("fornecedores")
def pagina_fornecedores():
    lista = fornecedores.listar_fornecedores()
    compras = fornecedores.listar_compras()
    produtos = estoque.listar_produtos()
    return render_template("fornecedores.html", fornecedores=lista, compras=compras, produtos=produtos)


@app.route("/fornecedores/novo", methods=["POST"])
@login_necessario
@permissao_necessaria("fornecedores")
def novo_fornecedor():
    fornecedores.cadastrar_fornecedor(
        nome=request.form.get("nome"), telefone=request.form.get("telefone"),
        email=request.form.get("email"), cnpj=request.form.get("cnpj"),
    )
    flash("Fornecedor cadastrado.", "sucesso")
    return redirect(url_for("pagina_fornecedores"))


@app.route("/fornecedores/compra", methods=["POST"])
@login_necessario
@permissao_necessaria("fornecedores")
def nova_compra():
    fornecedores.registrar_compra(
        produto_id=int(request.form["produto_id"]), quantidade=request.form.get("quantidade"),
        preco_unitario=request.form.get("preco_unitario"),
        fornecedor_id=int(request.form["fornecedor_id"]) if request.form.get("fornecedor_id") else None,
    )
    flash("Compra registrada e estoque atualizado.", "sucesso")
    return redirect(url_for("pagina_fornecedores"))


@app.route("/relatorios")
@login_necessario
@permissao_necessaria("relatorios")
def pagina_relatorios():
    hoje = date.today().isoformat()
    inicio_mes = date.today().replace(day=1).isoformat()
    mais_vendidos = relatorios.produtos_mais_vendidos()
    top_clientes = relatorios.clientes_top()
    lucro = relatorios.lucro_periodo(inicio_mes, hoje)
    estoque_critico = relatorios.relatorio_estoque_critico()
    vendas_semana = relatorios.vendas_por_dia(7)
    formas_pagamento = relatorios.vendas_por_forma_pagamento()
    return render_template(
        "relatorios.html", mais_vendidos=mais_vendidos, top_clientes=top_clientes, lucro=lucro,
        estoque_critico=estoque_critico, vendas_semana=vendas_semana, formas_pagamento=formas_pagamento,
        inicio_mes=inicio_mes, hoje=hoje,
    )


@app.route("/relatorios/exportar")
@login_necessario
@permissao_necessaria("relatorios")
def exportar_relatorio():
    inicio = request.args.get("inicio") or date.today().replace(day=1).isoformat()
    fim = request.args.get("fim") or date.today().isoformat()
    buffer = relatorios.exportar_vendas_csv(inicio, fim)
    return app.response_class(buffer.getvalue(), mimetype="text/csv",
                               headers={"Content-Disposition": f"attachment;filename=vendas_{inicio}_a_{fim}.csv"})


@app.route("/usuarios")
@login_necessario
@permissao_necessaria("usuarios")
def pagina_usuarios():
    return render_template("usuarios.html", usuarios=auth.listar_usuarios())


@app.route("/usuarios/novo", methods=["POST"])
@login_necessario
@permissao_necessaria("usuarios")
def novo_usuario():
    auth.criar_usuario(request.form.get("username"), request.form.get("senha"), request.form.get("nome"), request.form.get("papel", "vendedor"))
    flash("Usuario criado com sucesso.", "sucesso")
    return redirect(url_for("pagina_usuarios"))


@app.route("/usuarios/<int:usuario_id>/desativar", methods=["POST"])
@login_necessario
@permissao_necessaria("usuarios")
def desativar_usuario(usuario_id):
    auth.desativar_usuario(usuario_id)
    flash("Usuario desativado.", "sucesso")
    return redirect(url_for("pagina_usuarios"))


@app.route("/caixa", methods=["GET", "POST"])
@login_necessario
@permissao_necessaria("vendas")
def pagina_caixa():
    caixa = loja.caixa_aberto()
    if request.method == "POST":
        acao = request.form.get("acao")
        if acao == "abrir":
            loja.abrir_caixa(session.get("usuario"), request.form.get("saldo_inicial"))
            flash("Caixa aberto com sucesso.", "sucesso")
        elif acao == "movimentar" and caixa:
            loja.movimentar_caixa(caixa["id"], request.form.get("tipo"), request.form.get("valor"), request.form.get("descricao"), session.get("usuario"))
            flash("Movimentacao registrada.", "sucesso")
        elif acao == "fechar" and caixa:
            loja.fechar_caixa(caixa["id"], request.form.get("saldo_final"), request.form.get("observacao"))
            flash("Caixa fechado.", "sucesso")
        return redirect(url_for("pagina_caixa"))

    caixa, movimentos, esperado = loja.resumo_caixa(caixa["id"]) if caixa else (None, [], 0)
    historico = loja.historico_caixas()
    return render_template("caixa.html", caixa=caixa, movimentos=movimentos, esperado=esperado, historico=historico)


@app.route("/financeiro", methods=["GET", "POST"])
@login_necessario
@permissao_necessaria("relatorios")
def pagina_financeiro():
    if request.method == "POST":
        loja.criar_conta(
            tipo=request.form.get("tipo"), descricao=request.form.get("descricao"),
            valor=request.form.get("valor"), vencimento=request.form.get("vencimento") or None,
            categoria=request.form.get("categoria"), entidade=request.form.get("entidade"),
        )
        flash("Conta registrada.", "sucesso")
        return redirect(url_for("pagina_financeiro"))
    filtro = request.args.get("status", "aberta")
    return render_template("financeiro.html", contas=loja.listar_contas(status=filtro if filtro != "todas" else None),
                            resumo=loja.resumo_financeiro(), filtro=filtro)


@app.route("/financeiro/<int:conta_id>/baixar", methods=["POST"])
@login_necessario
@permissao_necessaria("relatorios")
def baixar_conta(conta_id):
    loja.baixar_conta(conta_id)
    flash("Conta baixada com sucesso.", "sucesso")
    return redirect(url_for("pagina_financeiro"))


@app.route("/pedidos", methods=["GET", "POST"])
@login_necessario
@permissao_necessaria("vendas")
def pagina_pedidos():
    if request.method == "POST":
        ids = request.form.getlist("produto_id")
        qtds = request.form.getlist("quantidade")
        itens = [{"produto_id": pid, "quantidade": q} for pid, q in zip(ids, qtds) if pid and q]
        cliente_id = request.form.get("cliente_id") or None
        loja.criar_pedido(int(cliente_id) if cliente_id else None, request.form.get("tipo", "orcamento"),
                           request.form.get("validade"), request.form.get("observacao"), itens)
        flash("Pedido/orcamento criado com sucesso.", "sucesso")
        return redirect(url_for("pagina_pedidos"))
    return render_template("pedidos.html", pedidos=loja.listar_pedidos(), produtos=estoque.listar_produtos(), clientes=clientes.listar_clientes())


@app.route("/pedidos/<int:pedido_id>")
@login_necessario
@permissao_necessaria("vendas")
def detalhe_pedido(pedido_id):
    pedido, itens = loja.detalhes_pedido(pedido_id)
    if not pedido:
        flash("Pedido nao encontrado.", "erro")
        return redirect(url_for("pagina_pedidos"))
    return render_template("pedido_detalhe.html", pedido=pedido, itens=itens)


@app.route("/pedidos/<int:pedido_id>/converter", methods=["POST"])
@login_necessario
@permissao_necessaria("vendas")
def converter_pedido(pedido_id):
    pedido, itens = loja.detalhes_pedido(pedido_id)
    if not pedido:
        flash("Pedido nao encontrado.", "erro")
        return redirect(url_for("pagina_pedidos"))
    itens_venda = [{"produto_id": i["produto_id"], "quantidade": i["quantidade"]} for i in itens]
    venda_id, total = vendas.registrar_venda(itens_venda, pedido["cliente_id"], "dinheiro", vendedor=session.get("usuario"))
    loja.atualizar_status_pedido(pedido_id, "convertido")
    flash(f"Pedido convertido na venda #{venda_id}.", "sucesso")
    return redirect(url_for("detalhe_venda", venda_id=venda_id))


@app.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@login_necessario
@permissao_necessaria("vendas")
def cancelar_pedido(pedido_id):
    loja.atualizar_status_pedido(pedido_id, "cancelado")
    flash("Pedido cancelado.", "sucesso")
    return redirect(url_for("pagina_pedidos"))


@app.route("/fiscal", methods=["GET", "POST"])
@login_necessario
@permissao_necessaria("relatorios")
def pagina_fiscal():
    if request.method == "POST":
        loja.salvar_empresa(request.form)
        flash("Dados fiscais da empresa atualizados.", "sucesso")
        return redirect(url_for("pagina_fiscal"))
    return render_template("fiscal.html", empresa=loja.obter_empresa(), notas=loja.listar_notas(), vendas_recentes=vendas.listar_vendas(limite=20))


@app.route("/fiscal/nota/<int:venda_id>", methods=["POST"])
@login_necessario
@permissao_necessaria("relatorios")
def gerar_nota_homologacao(venda_id):
    loja.criar_nota_homologacao(venda_id, request.form.get("tipo", "NFC-e"))
    flash("Documento de homologacao gerado (sem valor fiscal). Configure uma API fiscal para emissao real.", "sucesso")
    return redirect(url_for("pagina_fiscal"))


@app.route("/auditoria")
@login_necessario
@permissao_necessaria("usuarios")
def pagina_auditoria():
    return render_template("auditoria.html", registros=loja.listar_auditoria())


@app.route("/backup", methods=["POST"])
@login_necessario
@permissao_necessaria("usuarios")
def gerar_backup():
    nome = loja.criar_backup()
    flash(f"Backup criado com sucesso: {nome}", "sucesso")
    return redirect(url_for("dashboard"))


@app.route("/api/produto/<int:produto_id>")
@login_necessario
def api_produto(produto_id):
    produto = estoque.buscar_produto(produto_id)
    if not produto:
        return jsonify({"erro": "nao encontrado"}), 404
    return jsonify(dict(produto))


if __name__ == "__main__":
    inicializar_banco()
    if not auth.usuario_existe():
        print("Nenhum usuario encontrado. Acesse /registrar para criar o administrador.")
    app.run(debug=config.DEBUG)
