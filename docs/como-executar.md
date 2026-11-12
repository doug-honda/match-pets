# Como executar o Match Pets

## Estrutura do projeto

```
match-pets/
├── backend/            API em FastAPI (Python)
│   ├── main.py             rotas da API e entrega das telas
│   ├── compatibilidade.py  cálculo de compatibilidade (HU04)
│   ├── models.py           tabelas (SQLAlchemy)
│   ├── schemas.py          validação dos dados (Pydantic)
│   ├── database.py         conexão com o banco
│   └── tests/              testes automatizados dos critérios de aceite (pytest)
├── frontend/           telas (HTML, CSS e JavaScript)
│   ├── css/
│   └── js/
├── database/schema.sql criação das tabelas no PostgreSQL
├── docs/               regra de compatibilidade e este guia
├── exemplos/           animais de exemplo com foto, para demonstração
├── iniciar_demo.py     modo demonstração (sem PostgreSQL)
├── docker-compose.yml  PostgreSQL local com Docker
└── .devcontainer/      configuração do GitHub Codespaces
```

## Funcionalidades

| História | Sprint | O que faz | Tela |
|---|---|---|---|
| HU01 Cadastro do adotante | 1 | Cria a conta; bloqueia e-mail ou CPF repetido | `index.html` |
| HU02 Cadastro de animais | 1 | Responsável cadastra animais (com foto opcional) e marca a disponibilidade | `animais.html` |
| HU03 Perfil do adotante | 1 | Rotina, moradia, família e preferências | `perfil-adocao.html` |
| Login | 2 | Necessário para pedir adoção e enviar acompanhamento | `login.html` |
| HU04 Compatibilidade | 2 | Nota de 0 a 100 por animal, ordenada, com destaque para nota ≥ 75 | `compatibilidade.html` |
| HU05 Solicitação de adoção | 2 | Pedido com confirmação; o animal fica reservado; aviso de indisponível | `compatibilidade.html`, `minhas-adocoes.html` |
| HU06 Acompanhamento pós-adoção | 2 | Atualização com texto e foto (JPG, PNG ou WEBP, até 5 MB) e histórico | `minhas-adocoes.html`, `gestao.html` |

A regra de compatibilidade está em [`compatibilidade.md`](compatibilidade.md). Os pesos ficam na tabela `criterio_compatibilidade` e podem ser ajustados sem mudar o código. O endereço raiz (`/`) abre a tela inicial (`inicio.html`); `/status` informa se a API está no ar; `/docs` tem a documentação interativa da API.

## Opção 1: GitHub Codespaces (só o navegador)

1. No repositório, clique em **Code** → **Codespaces** → **Create codespace on main**.
2. Aguarde a criação (na primeira vez, alguns minutos). O banco sobe com `database/schema.sql`, a API inicia sozinha e os animais de exemplo são carregados.
3. Na aba **Ports**, abra o endereço da porta 8000.

O endereço é privado por padrão. Para outra pessoa acessar: botão direito na porta 8000 → **Port Visibility** → **Public**.

Para limpar os dados de teste (mantém os critérios de compatibilidade) e recolocar os exemplos, no terminal do Codespace:

```bash
python exemplos/zerar_dados.py
python exemplos/carregar_exemplos.py
```

## Opção 2: modo demonstração (só o Python 3.10+)

Usa um banco SQLite local; funciona em Windows, Mac e Linux.

```bash
python iniciar_demo.py           # Windows: py iniciar_demo.py
python iniciar_demo.py --zerar   # recomeça com o banco vazio
```

Na primeira vez, instala as dependências numa pasta `.venv-demo` (alguns minutos). Depois, carrega os animais de exemplo e abre o navegador. Para encerrar: Ctrl+C.

## Opção 3: com PostgreSQL

**1. Banco de dados**

Com Docker (cria o banco `matchpet` e as tabelas):

```bash
docker compose up -d
```

Ou com o Postgres.app (Mac):

```bash
createdb matchpet
psql -d matchpet -f database/schema.sql
```

O `schema.sql` pode ser rodado de novo num banco já existente: ele só cria o que falta e não apaga dados.

**2. Dependências e configuração**

```bash
python3 -m venv .venv
# Windows: .venv\Scripts\activate    |    Mac/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env    # Windows: copy .env.example .env
```

Com o Docker, o `.env` funciona como está. Com o Postgres.app, troque o usuário pelo seu usuário do macOS, sem senha (há um exemplo no `.env.example`).

**3. Iniciar**

```bash
uvicorn main:app --app-dir backend --reload
```

Abra `http://localhost:8000`. Para carregar os animais de exemplo: `python exemplos/carregar_exemplos.py`. As fotos enviadas ficam em `backend/fotos_acompanhamento/` (ignorada pelo Git); para outro local, defina `FOTOS_DIR` no `.env`.

## Testes automatizados

Os critérios de aceite da HU01 à HU06 têm testes com pytest, pelo menos um por cenário (34 testes), incluindo o exemplo calculado de `compatibilidade.md` e os riscos RISK06 e RISK07. Eles usam um banco SQLite em memória, então rodam sem PostgreSQL.

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```
