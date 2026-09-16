"""
app.py - Interface de linha de comando (CLI) do Sistema de Gestao de Loja
Complementa a versao web (web_app.py) para uso rapido via terminal.
"""
from database import inicializar_banco
import estoque
import clientes
import vendas
import fornecedores
import relatorios
from validators import ValidationError


def menu_principal():
    print("\n===== SISTEMA DE GESTAO DE LOJA (CLI) =====")
    print("1. Estoque")
    print("2. Clientes")
    print("3. Vendas")
    print("4. Fornecedores e compras")
    print("5. Relatorios")
    print("0. Sair")
    return input("Escolha uma opcao: ")


def menu_estoque():
    while True:
        print("\n--- ESTOQUE ---")
        print("1. Cadastrar produto")
        print("2. Listar produtos")
        print("3. Repor estoque")
        print("4. Produtos com estoque baixo")
        print("5. Remover produto")
        print("0. Voltar")
        opcao = input("Opcao: ")
        try:
            if opcao == "1":
                nome = input("Nome do produto: ")
                categoria = input("Categoria: ")
                preco_custo = input("Preco de custo: ") or 0
                preco_venda = input("Preco de venda: ")
                quantidade = input("Quantidade inicial: ") or 0
                estoque_minimo = input("Estoque minimo (padrao 5): ") or 5
                produto_id = estoque.cadastrar_produto(
                    nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo
                )
                print(f"Produto cadastrado com ID {produto_id}.")

            elif opcao == "2":
                for p in estoque.listar_produtos():
                    print(f"[{p['id']}] {p['nome']} | Qtd: {p['quantidade']} | "
                          f"Preco: R$ {p['preco_venda']:.2f}")

            elif opcao == "3":
                produto_id = int(input("ID do produto: "))
                quantidade = input("Quantidade a repor: ")
                estoque.repor_estoque(produto_id, quantidade)
                print("Estoque atualizado.")

            elif opcao == "4":
                for p in estoque.produtos_estoque_baixo():
                    print(f"[{p['id']}] {p['nome']} | Qtd atual: {p['quantidade']} "
                          f"| Minimo: {p['estoque_minimo']}")

            elif opcao == "5":
                produto_id = int(input("ID do produto a remover: "))
                estoque.remover_produto(produto_id)
                print("Produto removido.")

            elif opcao == "0":
                break
        except ValidationError as e:
            print(f"Erro: {e}")
        except ValueError:
            print("Entrada invalida. Tente novamente.")


def menu_clientes():
    while True:
        print("\n--- CLIENTES ---")
        print("1. Cadastrar cliente")
        print("2. Listar clientes")
        print("3. Historico de compras")
        print("0. Voltar")
        opcao = input("Opcao: ")
        try:
            if opcao == "1":
                nome = input("Nome: ")
                telefone = input("Telefone: ")
                email = input("Email: ")
                cliente_id = clientes.cadastrar_cliente(nome, telefone, email)
                print(f"Cliente cadastrado com ID {cliente_id}.")

            elif opcao == "2":
                for c in clientes.listar_clientes():
                    print(f"[{c['id']}] {c['nome']} | Tel: {c['telefone']}")

            elif opcao == "3":
                cliente_id = int(input("ID do cliente: "))
                for compra in clientes.historico_compras(cliente_id):
                    print(f"Venda #{compra['id']} | {compra['data']} | R$ {compra['total']:.2f} | {compra['status']}")

            elif opcao == "0":
                break
        except ValidationError as e:
            print(f"Erro: {e}")
        except ValueError:
            print("Entrada invalida. Tente novamente.")


def menu_vendas():
    while True:
        print("\n--- VENDAS ---")
        print("1. Registrar venda")
        print("2. Listar vendas")
        print("3. Detalhes de uma venda")
        print("4. Cancelar venda")
        print("0. Voltar")
        opcao = input("Opcao: ")
        try:
            if opcao == "1":
                itens = []
                while True:
                    produto_id = input("ID do produto (ou Enter para finalizar): ")
                    if not produto_id:
                        break
                    quantidade = input("Quantidade: ")
                    itens.append({"produto_id": produto_id, "quantidade": quantidade})
                cliente_id_input = input("ID do cliente (opcional): ")
                cliente_id = int(cliente_id_input) if cliente_id_input else None
                forma_pagamento = input("Forma de pagamento (dinheiro/cartao/pix/fiado): ") or "dinheiro"
                venda_id, total = vendas.registrar_venda(itens, cliente_id, forma_pagamento, vendedor="cli")
                print(f"Venda #{venda_id} registrada. Total: R$ {total:.2f}")

            elif opcao == "2":
                for v in vendas.listar_vendas():
                    print(f"[{v['id']}] {v['data']} | Total: R$ {v['total']:.2f} | "
                          f"{v['forma_pagamento']} | {v['status']}")

            elif opcao == "3":
                venda_id = int(input("ID da venda: "))
                venda, itens = vendas.detalhes_venda(venda_id)
                if venda:
                    print(f"Venda #{venda['id']} | Total: R$ {venda['total']:.2f}")
                    for item in itens:
                        print(f"  - {item['produto_nome']} x{item['quantidade']} = R$ {item['subtotal']:.2f}")
                else:
                    print("Venda nao encontrada.")

            elif opcao == "4":
                venda_id = int(input("ID da venda a cancelar: "))
                vendas.cancelar_venda(venda_id)
                print("Venda cancelada e estoque restaurado.")

            elif opcao == "0":
                break
        except ValidationError as e:
            print(f"Erro: {e}")
        except ValueError:
            print("Entrada invalida. Tente novamente.")


def menu_fornecedores():
    while True:
        print("\n--- FORNECEDORES E COMPRAS ---")
        print("1. Cadastrar fornecedor")
        print("2. Listar fornecedores")
        print("3. Registrar compra")
        print("4. Listar compras")
        print("0. Voltar")
        opcao = input("Opcao: ")
        try:
            if opcao == "1":
                nome = input("Nome: ")
                telefone = input("Telefone: ")
                email = input("Email: ")
                cnpj = input("CNPJ: ")
                fornecedores.cadastrar_fornecedor(nome, telefone, email, cnpj)
                print("Fornecedor cadastrado.")

            elif opcao == "2":
                for f in fornecedores.listar_fornecedores():
                    print(f"[{f['id']}] {f['nome']} | Tel: {f['telefone']}")

            elif opcao == "3":
                produto_id = int(input("ID do produto: "))
                fornecedor_id_input = input("ID do fornecedor (opcional): ")
                fornecedor_id = int(fornecedor_id_input) if fornecedor_id_input else None
                quantidade = input("Quantidade: ")
                preco_unitario = input("Preco unitario: ")
                fornecedores.registrar_compra(produto_id, quantidade, preco_unitario, fornecedor_id)
                print("Compra registrada e estoque atualizado.")

            elif opcao == "4":
                for c in fornecedores.listar_compras():
                    print(f"{c['produto_nome']} | Qtd: {c['quantidade']} | "
                          f"Unit: R$ {c['preco_unitario']:.2f} | {c['data']}")

            elif opcao == "0":
                break
        except ValidationError as e:
            print(f"Erro: {e}")
        except ValueError:
            print("Entrada invalida. Tente novamente.")


def menu_relatorios():
    while True:
        print("\n--- RELATORIOS ---")
        print("1. Faturamento por periodo")
        print("2. Produtos mais vendidos")
        print("3. Estoque critico")
        print("4. Lucro por periodo")
        print("5. Melhores clientes")
        print("0. Voltar")
        opcao = input("Opcao: ")

        if opcao == "1":
            inicio = input("Data inicio (AAAA-MM-DD): ")
            fim = input("Data fim (AAAA-MM-DD): ")
            resultado = relatorios.faturamento_periodo(inicio, fim)
            print(f"Faturamento: R$ {resultado['faturamento']:.2f} em {resultado['qtd_vendas']} vendas.")

        elif opcao == "2":
            for p in relatorios.produtos_mais_vendidos():
                print(f"{p['nome']} | Vendidos: {p['total_vendido']} | Receita: R$ {p['receita']:.2f}")

        elif opcao == "3":
            for p in relatorios.relatorio_estoque_critico():
                print(f"{p['nome']} | Qtd: {p['quantidade']} | Minimo: {p['estoque_minimo']}")

        elif opcao == "4":
            inicio = input("Data inicio (AAAA-MM-DD): ")
            fim = input("Data fim (AAAA-MM-DD): ")
            resultado = relatorios.lucro_periodo(inicio, fim)
            print(f"Receita: R$ {resultado['receita']:.2f} | Custo: R$ {resultado['custo']:.2f} "
                  f"| Lucro: R$ {resultado['lucro']:.2f}")

        elif opcao == "5":
            for c in relatorios.clientes_top():
                print(f"{c['nome']} | Compras: {c['qtd_compras']} | Total gasto: R$ {c['total_gasto']:.2f}")

        elif opcao == "0":
            break


def main():
    inicializar_banco()
    while True:
        opcao = menu_principal()
        if opcao == "1":
            menu_estoque()
        elif opcao == "2":
            menu_clientes()
        elif opcao == "3":
            menu_vendas()
        elif opcao == "4":
            menu_fornecedores()
        elif opcao == "5":
            menu_relatorios()
        elif opcao == "0":
            print("Ate logo!")
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main()
