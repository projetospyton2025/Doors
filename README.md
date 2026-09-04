# Doors

Sistema web para cadastro, consulta, edição, exclusão e exportação das aplicações e portas que hoje estão no `Doors.xlsx`.

Os dados são gravados em banco relacional (SQLite por padrão). Reiniciar o computador, o navegador ou o container Docker não apaga os registros.

## Estrutura funcional (fonte: Doors.xlsx)

| Campo do Excel | Tipo | Obrigatório | Controle na interface | Observação |
|---|---|---|---|---|
| Plano (abas Work / Personal / Loterries) | texto controlado | sim | abas + select | A aba `Loterries` do Excel é exibida como **Lotteries** |
| APP NAME | texto | sim | input | Nome da aplicação |
| PATH | texto | sim | input | Caminho Windows/Linux do projeto |
| DOOR | inteiro 1–65535 | sim | number | Porta única em todo o sistema |
| LANGUAGE | lista | sim | select | Lista inicial: Python e HTML (aba `DADOS`) |
| NGINX | texto/URL | não | input | No Excel é endereço, não Sim/Não |
| DOCKER | Sim / Não | sim | switch | Lista da aba `DADOS` |
| ACCOUNT → GITHUB | texto/URL | não | input | Subcoluna de ACCOUNT |
| ACCOUNT → DRIVE | texto/URL | não | input | Subcoluna de ACCOUNT |
| id | inteiro | automático | oculto | Campo técnico |
| created_at / updated_at | data/hora | automático | oculto | Campos técnicos |

O único registro existente no Excel (`AudioTo-txt`, porta `5222`, plano Work) é importado automaticamente na primeira inicialização.

## Requisitos

- Python 3.11 ou superior
- Navegador moderno
- Docker e Docker Compose (opcional, para o ambiente empacotado)

## Execução local

```powershell
cd "M:\Meu Drive\ProjetosPython\Doors"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Abra [http://127.0.0.1:5333](http://127.0.0.1:5333). A porta **5333** está reservada para este sistema.

O arquivo SQLite fica em `data/doors.db`.

Para recriar somente o banco:

```powershell
python scripts/init_db.py
```

## Execução com Docker e Nginx

```powershell
copy .env.example .env
docker compose up --build
```

Fluxo em produção:

```text
Usuário → Nginx (:8080) → FastAPI (:5333) → SQLite em volume
```

- Aplicação direta: [http://localhost:5333](http://localhost:5333)
- Proxy Nginx: [http://localhost:8080](http://localhost:8080)

O volume nomeado `doors_data` preserva o banco quando o container é recriado ou removido. Para apagar os dados de propósito:

```powershell
docker compose down -v
```

## Testes

```powershell
pytest -q
```

Os testes cobrem cadastro, consulta, filtro, edição, exclusão, porta duplicada, dashboard, exportação e importação do `Doors.xlsx`.

## API

- `GET /api/dashboard`
- `GET /api/applications`
- `POST /api/applications`
- `GET /api/applications/{id}`
- `PUT /api/applications/{id}`
- `DELETE /api/applications/{id}`
- `GET /api/languages`
- `POST /api/languages`
- `GET /api/export/csv`
- `GET /api/export/xlsx`
- `POST /api/import/xlsx`
- `GET /health`

Filtros da listagem e da exportação: `q`, `plan`, `language`, `docker`, `nginx`, `sort`, `order`, `page`, `page_size`.

## Migração futura para PostgreSQL

Altere `DATABASE_URL` no `.env`:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/doors
```

A aplicação usa SQLAlchemy. O restante do código não depende de SQLite.

## Segurança

- Validação no frontend e no backend
- Acesso ao banco apenas via ORM
- Textos sanitizados e escapados na interface
- Segredos e URLs de banco ficam em variáveis de ambiente
- Em produção (`DEBUG=false`) as mensagens de erro não expõem detalhes internos
