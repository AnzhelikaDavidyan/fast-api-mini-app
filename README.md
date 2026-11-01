# fast-api-mini-app

Simple CRUD app with FastAPI for **bonuses** and their **promos**, stored in PostgreSQL
(or SQLite when no database is configured).

- **Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, PostgreSQL 16 (psycopg 3), pytest, Pylint
- **Requires:** Python 3.10+, Git, and (for Postgres) Homebrew on macOS

## Project layout

```
app/
  main.py            FastAPI app
  routers/bonuses.py HTTP endpoints (/bonuses)
  schemas.py         Request/response models
  store.py           BonusStore: reads/writes the database
  database.py        Tables, engine, DATABASE_URL loading
sql/bonuses.sql      Plain-SQL reference of the schema and queries (not used by the app)
tests/               pytest suite (uses an in-memory DB, never touches Postgres)
.githooks/           commit-msg hook (commit message format)
.github/workflows/   Pylint CI
```

## Database schema

Each bonus has exactly one promo (one-to-one through `bonuses.promo_id`).
Deleting a bonus deletes its promo.

```
promos                         bonuses
------------------------       ---------------------------------
id      INTEGER  PK      <---  promo_id     INTEGER  FK, UNIQUE
name    VARCHAR(120)           id           INTEGER  PK
terms   TEXT                   name         VARCHAR(120)
offer   TEXT                   description  TEXT
                               min_deposit  FLOAT
                               amount       FLOAT
```

Tables are created automatically the first time the app talks to the database.

The app builds its queries with SQLAlchemy (`app/store.py`). For reference,
[`sql/bonuses.sql`](sql/bonuses.sql) has the same schema and queries in plain SQL. The app
doesn't use that file; running it with
`psql -U bonuses_user -d bonuses -f sql/bonuses.sql` leaves your data unchanged.

## Setup (first time)

### 1. Clone and create a virtual environment

```sh
git clone https://github.com/AnzhelikaDavidyan/fast-api-mini-app.git
cd fast-api-mini-app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Enable the commit message check

```sh
git config core.hooksPath .githooks
```

### 3. Install and start PostgreSQL (macOS)

```sh
brew install postgresql@16
brew services start postgresql@16
```

`brew services` keeps Postgres running in the background and starts it again after a reboot.
Check it with `pg_isready` (should print `accepting connections`).

### 4. Create the database user and database

```sh
psql postgres -c "CREATE USER bonuses_user WITH PASSWORD 'bonuses_pass';"
psql postgres -c "CREATE DATABASE bonuses OWNER bonuses_user;"
```

### 5. Point the app at the database

```sh
cp .env.example .env
```

`.env` holds the connection string and is git-ignored, so passwords never get committed:

```
DATABASE_URL=postgresql+psycopg://bonuses_user:bonuses_pass@localhost:5432/bonuses
```

Format: `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`.
A `DATABASE_URL` set in your shell overrides `.env`. Without either, the app uses a local
SQLite file `bonuses.db`.

## Run the app

```sh
.venv/bin/uvicorn app.main:app --reload
```

- Interactive API docs: http://127.0.0.1:8000/docs
- `--reload` restarts the server when you edit code. Stop it with `Ctrl+C`.
- `Address already in use` means another server is on port 8000: stop it, or run on another
  port with `--port 8001`.

### Endpoints

| Method | Path             | What it does                                     |
|--------|------------------|--------------------------------------------------|
| GET    | `/bonuses`       | List all bonuses                                 |
| POST   | `/bonuses`       | Create a bonus (with its promo) → `201`          |
| GET    | `/bonuses/{id}`  | Get one bonus → `404` if missing                 |
| PATCH  | `/bonuses/{id}`  | Update only the fields you send                  |
| DELETE | `/bonuses/{id}`  | Delete a bonus and its promo → `204`             |

Example:

```sh
curl -X POST http://127.0.0.1:8000/bonuses \
  -H "Content-Type: application/json" \
  -d '{"name": "Welcome Bonus", "description": "100% on first deposit",
       "minDeposit": 20, "amount": 100,
       "promo": {"name": "WELCOME100", "terms": "Wagering x35", "offer": "100% up to $100"}}'
```

## Look at the data

From the terminal:

```sh
psql -U bonuses_user -d bonuses -c '\dt'
psql -U bonuses_user -d bonuses -c 'SELECT * FROM bonuses;'
psql -U bonuses_user -d bonuses -c 'SELECT b.id, b.name, b.amount, p.name AS promo
                                     FROM bonuses b JOIN promos p ON p.id = b.promo_id;'
```

With a GUI, connect using:

| Field    | Value          |
|----------|----------------|
| Host     | `localhost`    |
| Port     | `5432`         |
| User     | `bonuses_user` |
| Password | `bonuses_pass` |
| Database | `bonuses`      |

- **DBeaver** (free): browse rows *and* see the relations as an ER diagram.
  Open the connection → `bonuses` → Schemas → `public` → right-click **Tables** →
  **View Diagram**.
- **TablePlus**: fast for browsing and editing rows; no ER diagram.
- **pgAdmin**: official Postgres tool; right-click the database → **ERD For Database**.

## Tests and linting

```sh
.venv/bin/python -m pytest
.venv/bin/pip install pylint==4.1.3
.venv/bin/pylint $(git ls-files '*.py')
```

Tests use a fresh in-memory SQLite database per test. GitHub Actions runs Pylint on every
push and pull request (Python 3.10–3.13).

## Commit and push

Commit subjects must be `feat: {message}`, `fix: {message}` or `chore: {message}`;
the `commit-msg` hook (step 2 of setup) rejects anything else.

```sh
git add -A
git commit -m "feat: add bonus filtering"
git push
```

`git pull --rebase` avoids "Merge branch …" commits, which the hook would reject.

The first `git push` asks for GitHub credentials: username, then a
[personal access token](https://github.com/settings/tokens/new) with the `repo` scope as the
password (your account password won't work). macOS Keychain remembers it afterwards.
Alternatively run `gh auth login` once and Git will use that login.
