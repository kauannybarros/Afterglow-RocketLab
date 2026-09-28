# RocketLab 2026.2

Aplicação web para catálogo de filmes, desenvolvida com FastAPI, SQLAlchemy,
React e TypeScript. O sistema permite consultar e filtrar o catálogo,
gerenciar filmes, registrar avaliações de 0 a 10 e organizar filmes em listas
personalizadas.

## Funcionalidades

- catálogo com ordenação por melhores avaliados ou ordem alfabética;
- pesquisa e filtros por gênero, nota mínima, ano e status;
- cadastro, edição, visualização e exclusão de filmes;
- avaliações com notas decimais de 0 a 10 e comentário opcional;
- médias recalculadas a partir das notas individuais, limitadas ao máximo de 10;
- listas permanentes WatchList e Favoritos, além de listas personalizadas;
- ações rápidas para marcar um filme como favorito ou como “Quero assistir”;
- renomeação e exclusão de listas personalizadas e remoção de filmes das listas;
- importação idempotente dos arquivos CSV fornecidos;
- interface responsiva com tema escuro.

## Estrutura do projeto

```text
rocketlab2026-2/
├── backend/
│   ├── app/
│   │   ├── api/           # composição dos endpoints
│   │   ├── core/          # configurações, exceções e logging
│   │   ├── db/            # banco, sessões e importação dos CSVs
│   │   └── movies/        # modelos e regras do domínio de filmes
│   ├── migrations/        # migrações Alembic
│   └── tests/             # testes automatizados do backend
├── frontend/
│   └── src/               # aplicação React
└── README.md
```

## Pré-requisitos

- Python 3.11 ou superior;
- Node.js 20.19 ou superior, ou Node.js 22.12 ou superior;
- npm;
- arquivos CSV em `bases-1` e `bases-2`, caso queira carregar o catálogo
  fornecido para a atividade.

## Como executar

Os comandos abaixo consideram que o terminal está inicialmente na raiz do
repositório `rocketlab2026-2`.

### 1. Configurar o backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
.venv/bin/alembic upgrade head
```

Esse processo cria o ambiente virtual, instala as dependências, configura as
variáveis locais e cria ou atualiza o banco SQLite em
`backend/rocketlab.db`.

### 2. Importar os CSVs (opcional)

O sistema funciona sem a importação e permite cadastrar filmes manualmente.
Para carregar o catálogo fornecido, mantenha as bases como pastas irmãs do
repositório:

```text
Pasta_Principal/
├── bases-1/bases_atv_dev1/
├── bases-2/bases_atv_dev_2/
└── rocketlab2026-2/
```

Ainda dentro de `backend`, valide primeiro os arquivos sem alterar o banco:

```bash
.venv/bin/python -m app.db.import_csv \
  --bases-1 ../../bases-1/bases_atv_dev1 \
  --bases-2 ../../bases-2/bases_atv_dev_2 \
  --dry-run
```

Depois, faça a importação:

```bash
.venv/bin/python -m app.db.import_csv \
  --bases-1 ../../bases-1/bases_atv_dev1 \
  --bases-2 ../../bases-2/bases_atv_dev_2
```

O importador pode ser executado novamente: registros existentes são
atualizados sem criar duplicações.

### 3. Iniciar o backend

Ainda dentro de `backend`, execute:

```bash
.venv/bin/uvicorn app.main:app --reload
```

O backend ficará disponível em:

- API: `http://localhost:8000`;
- documentação interativa: `http://localhost:8000/docs`;
- verificação de saúde: `http://localhost:8000/health`.

### 4. Iniciar o frontend

Com o backend em execução, abra outro terminal na raiz do repositório:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

A interface ficará disponível em `http://localhost:5173`. Durante o
desenvolvimento, o Vite encaminha as requisições iniciadas em `/api` para o
backend em `http://localhost:8000`.

## Variáveis de ambiente

O backend utiliza o arquivo `backend/.env`. As principais opções são:

- `DATABASE_URL`: conexão com o banco, usando SQLite local por padrão;
- `BACKEND_CORS_ORIGINS`: origens autorizadas a acessar a API;
- `LOG_LEVEL`: nível de logging da aplicação.

O frontend utiliza `frontend/.env`. Para acessar um backend em outro endereço,
altere `VITE_API_URL`.

## Banco de dados e migrações

O banco utiliza um esquema estrela para armazenar filmes, gêneros, pessoas,
produtoras, desempenho e o resumo das avaliações. O Alembic é o único
responsável pela criação e evolução das tabelas.

Para aplicar todas as migrações pendentes:

```bash
cd backend
.venv/bin/alembic upgrade head
```

Para criar uma nova migração após alterar os modelos:

```bash
.venv/bin/alembic revision --autogenerate -m "descreva a alteração"
.venv/bin/alembic upgrade head
```

Cada avaliação individual possui uma nota obrigatória e um comentário
opcional. Todas as notas participam da média e da quantidade de avaliações,
mas somente aquelas com comentário são apresentadas como resenhas.

## Importação dos dados

O importador:

- valida a presença, o cabeçalho e os tipos dos dez arquivos;
- processa os registros em lotes;
- respeita a ordem das chaves estrangeiras;
- interrompe cada carga caso encontre dados inválidos;
- atualiza registros existentes sem duplicá-los;
- verifica a integridade das chaves estrangeiras ao final.

Use `--batch-size` para ajustar o tamanho dos lotes e `--database-url` para
selecionar outro banco SQLite.

## Testes e verificações

Para executar os testes e o lint do backend:

```bash
cd backend
.venv/bin/pytest -q
.venv/bin/ruff check app tests
```

Para verificar os tipos e gerar o build de produção do frontend:

```bash
cd frontend
npm run typecheck
npm run build
```
