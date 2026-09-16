# Sistema de Gestão de Loja

Sistema completo em Python para organizar tudo o que uma loja precisa: controle de **estoque**, **vendas**, **clientes**, **caixa** e **relatórios gerenciais**. Funciona via linha de comando (CLI) e usa **SQLite** como banco de dados local — não requer servidor externo.

## Funcionalidades

### Estoque
- Cadastro, edição e remoção de produtos
- Controle de quantidade e preço de custo/venda
- Alerta automático de estoque baixo (abaixo do mínimo definido)
- Reposição de estoque

### Clientes
- Cadastro de clientes (nome, telefone, email)
- Histórico de compras por cliente

### Vendas
- Registro de vendas com múltiplos itens
- Baixa automática de estoque ao vender
- Cancelamento de venda com restauração de estoque
- Registro de forma de pagamento
- Lançamento automático no caixa

### Relatórios
- Faturamento por período
- Produtos mais vendidos
- Estoque crítico (produtos que precisam de reposição)
- Lucro por período (receita - custo)
- Ranking dos melhores clientes

## Estrutura do projeto

```
sistema-gestao-loja/
├── app.py            # Interface de linha de comando (menu principal)
├── database.py       # Conexão e criação das tabelas do banco SQLite
├── estoque.py         # Regras de negócio do estoque
├── clientes.py        # Regras de negócio de clientes
├── vendas.py          # Regras de negócio de vendas
├── relatorios.py       # Consultas e relatórios gerenciais
├── requirements.txt
└── README.md
```

## Como usar

1. Clone o repositório:
   ```bash
   git clone https://github.com/henriquesantosmaciel-alt/sistema-gestao-loja.git
   cd sistema-gestao-loja
   ```

2. (Opcional) Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Execute o programa (não há dependências externas, apenas Python 3 com `sqlite3` da biblioteca padrão):
   ```bash
   python app.py
   ```

4. Na primeira execução, o banco de dados `loja.db` é criado automaticamente com todas as tabelas necessárias.

## Requisitos

- Python 3.8 ou superior

## Roadmap (ideias de evolução)

- Interface gráfica (Tkinter ou web com Flask/Django)
- Emissão de recibos/notas em PDF
- Controle de fornecedores e compras
- Múltiplos usuários com login e permissões
- Backup automático do banco de dados

## Licença

Este projeto está disponível sob a licença MIT. Sinta-se livre para usar, modificar e distribuir.
