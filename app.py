"""
app.py - Interface de linha de comando (CLI) do Sistema de Gestão de Loja
"""
from datetime import date

from database import inicializar_banco
import estoque
import clientes
import vendas
import relatorios


def menu_principal():
    print("\n===== SISTEMA DE GESTÃO DE LOJA =====")
    print("1. Estoque")
    print("2. Clientes")
    print("3. Vendas")
    print("4. Relatórios")
    print("0. Sair")
    return input("Escolha uma opção: ")


def menu_estoque():
    while True:
        print("\n--- ESTOQUE ---")
        print("1. Cadastrar produto")
        print("2. Listar produtos")
        print("3. Repor estoque")
        print("4. Produtos com estoque baixo")
        print("0. Voltar")
        opcao = input("Opção: ")

        if opcao == "1":
            nome = input("Nome do produto: ")
            categoria = input("Categoria: ")
            preco_custo = float(input("Preço de custo: "))
            preco_venda = float(input("Preço de venda: "))
            quantidade = int(input("Quantidade inicial: "))
            estoque_minimo = int(input("Estoque mínimo (padrão 5): ") or 5)
            produto_id = estoque.cadastrar_produto(
                nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo
            )
            print(f"Produto cadastrado com ID {produto_id}.")

        elif opcao == "2":
            for p in estoque.listar_produtos():
                print(f"[{p['id']}] {p['nome']} | Qtd: {p['quantidade']} | "
                      f"Preço: R$ {p['preco_venda']:.2f}")

        elif opcao == "3":
            produto_id = int(input("ID do produto: "))
            quantidade = int(input("Quantidade a repor: "))
            estoque.repor_estoque(produto_id, quantidade)
            print("Estoque atualizado.")

        elif opcao == "4":
            for p in estoque.produtos_estoque_baixo():
                print(f"[{p['id']}] {p['nome']} | Qtd atual: {p['quantidade']} "
                      f"| Mínimo: {p['estoque_minimo']}")

        elif opcao == "0":
            break


def menu_clientes():
    while True:
        print("\n--- CLIENTES ---")
        print("1. Cadastrar cliente")
        print("2. Listar clientes")
        print("3. Histórico de compras")
        print("0. Voltar")
        opcao = input("Opção: ")

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
                print(f"Venda #{compra['id']} | {compra['data']} | R$ {compra['total']:.2f}")

        elif opcao == "0":
            break


def menu_vendas():
    while True:
        print("\n--- VENDAS ---")
        print("1. Registrar venda")
        print("2. Listar vendas")
        print("3. Detalhes de uma venda")
        print("4. Cancelar venda")
        print("0. Voltar")
        opcao = input("Opção: ")

        if opcao == "1":
            itens = []
            while True:
                produto_id = input("ID do produto (ou Enter para finalizar): ")
                if not produto_id:
                    break
                quantidade = int(input("Quantidade: "))
                itens.append({"produto_id": int(produto_id), "quantidade": quantidade})
            cliente_id_input = input("ID do cliente (opcional): ")
            cliente_id = int(cliente_id_input) if cliente_id_input else None
            forma_pagamento = input("Forma de pagamento: ") or "dinheiro"
            try:
                venda_id, total = vendas.registrar_venda(itens, cliente_id, forma_pagamento)
                print(f"Venda #{venda_id} registrada. Total: R$ {total:.2f}")
            except ValueError as e:
                print(f"Erro: {e}")

        elif opcao == "2":
            for v in vendas.listar_vendas():
                print(f"[{v['id']}] {v['data']} | Total: R$ {v['total']:.2f} | {v['forma_pagamento']}")

        elif opcao == "3":
            venda_id = int(input("ID da venda: "))
            venda, itens = vendas.detalhes_venda(venda_id)
            if venda:
                print(f"Venda #{venda['id']} | Total: R$ {venda['total']:.2f}")
                for item in itens:
                    print(f"  - {item['produto_nome']} x{item['quantidade']} = R$ {item['subtotal']:.2f}")

        elif opcao == "4":
            venda_id = int(input("ID da venda a cancelar: "))
            vendas.cancelar_venda(venda_id)
            print("Venda cancelada e estoque restaurado.")

        elif opcao == "0":
            break


def menu_relatorios():
    while True:
        print("\n--- RELATÓRIOS ---")
        print("1. Faturamento por período")
        print("2. Produtos mais vendidos")
        print("3. Estoque crítico")
        print("4. Lucro por período")
        print("5. Melhores clientes")
        print("0. Voltar")
        opcao = input("Opção: ")

        if opcao == "1":
            inicio = input("Data início (AAAA-MM-DD): ")
            fim = input("Data fim (AAAA-MM-DD): ")
            resultado = relatorios.faturamento_periodo(inicio, fim)
            print(f"Faturamento: R$ {resultado['faturamento']:.2f} em {resultado['qtd_vendas']} vendas.")

        elif opcao == "2":
            for p in relatorios.produtos_mais_vendidos():
                print(f"{p['nome']} | Vendidos: {p['total_vendido']} | Receita: R$ {p['receita']:.2f}")

        elif opcao == "3":
            for p in relatorios.relatorio_estoque_critico():
                print(f"{p['nome']} | Qtd: {p['quantidade']} | Mínimo: {p['estoque_minimo']}")

        elif opcao == "4":
            inicio = input("Data início (AAAA-MM-DD): ")
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
            menu_relatorios()
        elif opcao == "0":
            print("Até logo!")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
