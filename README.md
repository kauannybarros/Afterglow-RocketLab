# RocketLab 2026.2 — repositório base

Base inicial para evoluir a atividade do RocketLab 2026.2. Ela preserva a organização do backend,
o modelo relacional do catálogo de filmes em SQLAlchemy 2.0 e o histórico de
migrações com Alembic, sem incluir interface, dados CSV, endpoints de negócio
ou rotinas de carga.

> **Nota:** `RocketLab` é apenas o nome de referência desta base. O diretório,
> nome do pacote, título da API e arquivo do banco podem ser renomeados para o
> que preferirem; eles não representam uma exigência da
> estrutura-base.

## Estrutura

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/        # ponto de composição dos futuros routers
│   │   ├── core/          # configurações e logging
│   │   ├── db/            # Base ORM, engine e sessões
│   │   └── movies/        # modelos SQLAlchemy do domínio de filmes
│   ├── migrations/        # ambiente e revisões Alembic
│   └── tests/
├── frontend/              # interface React, TypeScript e Vite
└── README.md
```

## Execução

Requer Python 3.11 ou superior.

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

A API mínima ficará disponível em `http://localhost:8000`; use
`http://localhost:8000/docs` para a documentação automática. O endpoint
`GET /health` permite conferir se a aplicação iniciou corretamente.

## Banco de dados e migrações

O modelo usa um esquema estrela para o catálogo de filmes:

- dimensões de filmes, gêneros, pessoas, produtoras e resumo de avaliações;
- fato de desempenho financeiro e de engajamento;
- tabelas de associação N:N entre filmes, gêneros, produtoras e pessoas;

O schema corresponde aos nove arquivos CSV atuais da camada Diamond, com a
adição de `movie_reviews`: uma avaliação individual por linha, na escala 0–10.
A tabela aceita diretamente as colunas `sk_movie_review_id`, `sk_movie_id`,
`nome`, `nota` e `comentario` do CSV enviado separadamente. `created_at` é
gerado pelo banco. O contexto generativo não faz parte desta base.

Os CSVs não são versionados neste repositório. Depois de aplicar as migrações,
faça uma validação completa dos arquivos sem alterar o banco:

```bash
cd backend
.venv/bin/python -m app.db.import_csv \
  --bases-1 ../../bases-1/bases_atv_dev1 \
  --bases-2 ../../bases-2/bases_atv_dev_2 \
  --dry-run
```

Para importar os dados:

```bash
.venv/bin/python -m app.db.import_csv \
  --bases-1 ../../bases-1/bases_atv_dev1 \
  --bases-2 ../../bases-2/bases_atv_dev_2
```

O importador:

- valida a presença, o cabeçalho e os tipos dos dez arquivos;
- processa os registros em lotes, sem carregar cada CSV inteiro na memória;
- respeita a ordem das chaves estrangeiras;
- usa uma transação por arquivo e interrompe a carga em dados inválidos;
- pode ser executado novamente, atualizando registros existentes sem duplicá-los;
- verifica a integridade das chaves estrangeiras ao final.

Use `--batch-size` para ajustar o tamanho dos lotes e `--database-url` para
selecionar outro arquivo SQLite. Por padrão, o comando usa o `DATABASE_URL`
configurado no arquivo `.env`.

As tabelas são criadas exclusivamente pelo Alembic. Para evoluir os modelos,
crie uma revisão e aplique-a:

```bash
cd backend
.venv/bin/alembic revision --autogenerate -m "descreva a alteração"
.venv/bin/alembic upgrade head
```

O banco padrão é SQLite local em `backend/rocketlab.db`. Ajuste
`DATABASE_URL` no arquivo `.env` para usar outro banco compatível.

## Frontend

O frontend apresenta o catálogo ordenado por avaliação e quantidade de
resenhas, com busca por título, filtros de gênero, nota, ano e status,
paginação, detalhes e avaliações, gerenciamento de filmes e listas
personalizadas. Uma lista pode ser criada vazia ou a partir de um filme, e
novos filmes podem ser adicionados pela página de detalhes. A interface usa um
tema escuro responsivo com detalhes em pink e azul ciano.

Com o backend em execução, abra outro terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

A interface ficará disponível em `http://localhost:5173`. Durante o
desenvolvimento, o Vite encaminha as requisições iniciadas em `/api` para o
backend em `http://localhost:8000`. Para usar outra URL, defina
`VITE_API_URL` no arquivo `.env`.
