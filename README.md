# LojaOS - Sistema de Gestao de Loja

Sistema completo para organizar tudo o que uma loja precisa: **estoque**, **vendas**, **clientes**, **fornecedores/compras**, **financeiro**, **relatorios com graficos** e **controle de acesso por papel (admin/vendedor)**. Disponivel em duas versoes: uma **interface web moderna** (Flask, tema escuro minimalista) e uma **versao CLI** por linha de comando. Usa **SQLite** como banco local, sem necessidade de servidor externo.

## Destaques desta versao

- Senhas com hash seguro **PBKDF2** (via Werkzeug), sem implementacao caseira de criptografia.
- Protecao **CSRF** em todos os formularios (Flask-WTF).
- Chave secreta e configuracoes sensiveis carregadas de **variaveis de ambiente** (`config.py`), nunca hardcoded.
- **Validacao de dados** centralizada (`validators.py`) para todos os formularios e regras de negocio.
- Tratamento de erros consistente com paginas amigaveis (404, 500, erros de validacao).
- **Controle de acesso por papel**: administradores tem acesso total; vendedores veem apenas vendas e clientes.
- Buscas e filtros em estoque, clientes e vendas.
- Exportacao de vendas em **CSV** por periodo.
- Indices no banco de dados para consultas mais rapidas.

## Funcionalidades

### Dashboard
- Resumo de faturamento do dia e do mes, valor total em estoque
- Numero de vendas, clientes e produtos ativos
- Grafico de vendas dos ultimos 7 dias (Chart.js)
- Alerta visual de produtos com estoque critico

### Estoque (acesso: admin)
- Cadastro, busca e remocao (inativacao logica se ja usado em vendas)
- Controle de preco de custo e de venda, com validacao de valores
- Alerta automatico de estoque abaixo do minimo
- Reposicao manual de estoque

### Vendas (acesso: admin e vendedor)
- Registro de vendas com multiplos itens dinamicos (adicionar/remover linhas)
- Baixa automatica de estoque, com verificacao de disponibilidade
- Cancelamento de venda com restauracao de estoque (mantem historico, sem apagar)
- Emissao de **recibo em PDF** por venda
- Filtro de vendas por cliente
- Lancamento automatico no caixa

### Clientes (acesso: admin e vendedor)
- Cadastro com validacao de email
- Busca por nome, telefone ou email
- Pagina de detalhe com estatisticas (total gasto, ticket medio) e historico completo

### Fornecedores e compras (acesso: admin)
- Cadastro de fornecedores (nome, telefone, email, CNPJ)
- Registro de compras que repoe o estoque automaticamente
- Historico de compras por produto/fornecedor

### Relatorios (acesso: admin)
- Faturamento e lucro por periodo (receita - custo)
- Produtos mais vendidos e ranking dos melhores clientes
- Vendas por forma de pagamento
- Estoque critico
- **Exportacao de vendas em CSV** por intervalo de datas

### Usuarios (acesso: admin)
- Criacao de novos usuarios com papel admin ou vendedor
- Desativacao de usuarios (sem exclusao definitiva)

## Estrutura do projeto

```
sistema-gestao-loja/
├── web_app.py         # Aplicacao web Flask (interface principal recomendada)
├── app.py             # Interface CLI (linha de comando)
├── config.py          # Configuracoes e segredos via variaveis de ambiente
├── database.py        # Conexao, indices e criacao das tabelas SQLite
├── validators.py      # Validacao centralizada de dados de entrada
├── estoque.py         # Regras de negocio do estoque
├── clientes.py        # Regras de negocio de clientes
├── vendas.py          # Regras de negocio de vendas
├── fornecedores.py    # Fornecedores e compras
├── relatorios.py      # Consultas, relatorios e exportacao CSV
├── auth.py            # Autenticacao e controle de papeis
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

3. (Opcional, recomendado em producao) Defina variaveis de ambiente:
   ```bash
   export LOJAOS_SECRET_KEY="uma-chave-bem-aleatoria"
   export LOJAOS_DEBUG=false
   export LOJAOS_HTTPS=true
   ```
   Sem essas variaveis, o sistema gera uma chave aleatoria a cada execucao (adequado para testes locais).

4. Execute a aplicacao web:
   ```bash
   python web_app.py
   ```

5. Acesse [http://localhost:5000](http://localhost:5000) no navegador. No primeiro acesso, voce sera direcionado para criar o usuario administrador.

## Como usar (versao CLI)

Se preferir a versao por terminal (sem interface grafica):
```bash
python app.py
```

## Requisitos

- Python 3.8 ou superior
- Flask, Flask-WTF, Werkzeug e reportlab (instalados via `requirements.txt`)

## Roadmap (ideias de evolucao)

- Exportacao de relatorios tambem em PDF/Excel
- Codigo de barras para produtos
- Notificacoes automaticas de estoque baixo por email
- Modo multi-loja (varias filiais no mesmo sistema)
- Testes automatizados (pytest) para as regras de negocio

## Licenca

Este projeto esta disponivel sob a licenca MIT. Sinta-se livre para usar, modificar e distribuir.
