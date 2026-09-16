# LojaOS - Sistema de Gestao de Loja

Sistema completo para organizar tudo o que uma loja precisa: **estoque**, **vendas**, **clientes**, **fornecedores/compras**, **financeiro** e **relatorios com graficos**. Disponivel em duas versoes: uma **interface web moderna** (Flask, tema escuro minimalista) e uma **versao CLI** por linha de comando. Usa **SQLite** como banco local, sem necessidade de servidor externo.

## Funcionalidades

### Dashboard
- Resumo de faturamento do dia e do mes
- Numero de vendas, clientes e produtos cadastrados
- Grafico de vendas dos ultimos 7 dias (Chart.js)
- Alerta visual de produtos com estoque critico

### Estoque
- Cadastro, edicao e remocao de produtos
- Controle de preco de custo e de venda
- Alerta automatico de estoque abaixo do minimo
- Reposicao manual de estoque

### Vendas
- Registro de vendas com multiplos itens em uma unica tela
- Baixa automatica de estoque ao vender
- Cancelamento de venda com restauracao de estoque
- Emissao de **recibo em PDF** por venda
- Lancamento automatico no caixa

### Clientes
- Cadastro de clientes (nome, telefone, email)
- Pagina de detalhe com historico completo de compras

### Fornecedores e compras
- Cadastro de fornecedores (nome, telefone, email, CNPJ)
- Registro de compras que repoe o estoque automaticamente
- Historico de compras por produto/fornecedor

### Relatorios
- Faturamento e lucro por periodo (receita - custo)
- Produtos mais vendidos
- Ranking dos melhores clientes
- Estoque critico

### Autenticacao
- Tela de login com usuario e senha (hash com salt, sem dependencias externas de criptografia)
- Primeiro acesso cria o usuario administrador

## Estrutura do projeto

```
sistema-gestao-loja/
├── web_app.py         # Aplicacao web Flask (interface principal recomendada)
├── app.py             # Interface CLI (linha de comando)
├── database.py        # Conexao e criacao das tabelas SQLite
├── estoque.py         # Regras de negocio do estoque
├── clientes.py        # Regras de negocio de clientes
├── vendas.py          # Regras de negocio de vendas
├── fornecedores.py    # Fornecedores e compras
├── relatorios.py      # Consultas e relatorios gerenciais
├── auth.py            # Autenticacao de usuarios
├── recibo.py          # Geracao de recibo em PDF
├── templates/          # Templates HTML (Jinja2) da interface web
├── static/style.css   # Estilo moderno e minimalista (tema escuro)
├── requirements.txt
└── README.md
```

## Como usar (interface web - recomendado)

1. Clone o repositorio:
   ```bash
   git clone https://github.com/henriquesantosmaciel-alt/sistema-gestao-loja.git
   cd sistema-gestao-loja
   ```

2. Crie um ambiente virtual e instale as dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. Execute a aplicacao web:
   ```bash
   python web_app.py
   ```

4. Acesse [http://localhost:5000](http://localhost:5000) no navegador. No primeiro acesso, voce sera direcionado para criar o usuario administrador.

## Como usar (versao CLI)

Se preferir a versao por terminal (sem interface grafica):
```bash
python app.py
```

## Requisitos

- Python 3.8 ou superior
- Flask e reportlab (instalados via `requirements.txt`)

## Roadmap (ideias de evolucao)

- Multiplos usuarios com permissoes diferenciadas (admin, vendedor)
- Exportacao de relatorios em PDF/Excel
- Codigo de barras para produtos
- Notificacoes automaticas de estoque baixo por email
- Modo multi-loja (varias filiais no mesmo sistema)

## Licenca

Este projeto esta disponivel sob a licenca MIT. Sinta-se livre para usar, modificar e distribuir.
