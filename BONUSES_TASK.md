# Exercise: finish the bonuses API

Your bonuses API already has CRUD endpoints, a router, a shared store through `Depends`,
PostgreSQL through SQLAlchemy, and tests. This exercise adds what a real list API needs:
stricter validation, timestamps, and search, filtering, sorting and pagination.

The checks are written: [`tests/test_bonuses_exercise.py`](tests/test_bonuses_exercise.py),
37 tests in four levels. Level 1 already passes. **You're done when all 37 pass** and the
original `tests/test_bonuses.py` still passes.

```sh
.venv/bin/python -m pytest tests/test_bonuses_exercise.py -v   # the exercise
.venv/bin/python -m pytest                                     # everything
```

Rules: don't edit the test files; change the app until they pass. Work one level at a time.
When a test fails, read its name and the assertion first; most of them say exactly what's wrong.

Starting point: **17 of 37 pass** (all of Level 1, and the validation rules that already exist).

---

## Files you'll change

| File | What changes |
|---|---|
| `app/schemas.py` | trimmed names (Level 2), `createdAt` / `updatedAt` on `Bonus` (Level 3) |
| `app/database.py` | `created_at` and `updated_at` columns on `BonusRow` (Level 3) |
| `app/store.py` | set timestamps (Level 3), `list_all` with filters, sorting and paging (Level 4) |
| `app/routers/bonuses.py` | query parameters on `GET /bonuses` (Level 4) |
| `sql/bonuses.sql` | keep the raw SQL reference in step with the new columns and queries |

---

## Level 1: CRUD (already passes: 8 tests)

These check the API as it is now. If one fails later, you broke something that used to work.

## Level 2: Validation (12 tests)

- Bonus `name` and promo `name`: 1–120 characters **after trimming spaces**.
  `"   "` is invalid; `"  Reload Bonus  "` is saved as `"Reload Bonus"`. The same applies on PATCH.
- `amount` and `minDeposit` must be numbers `>= 0` (already true).
- `promo` is required, with all three fields (already true).
- `/bonuses/abc` gives `422` (already true).

Hint: `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]`.
Define it once and use it in `PromoIn`, `BonusCreate` and `BonusUpdate`.

## Level 3: Timestamps (5 tests)

- A bonus gets `createdAt` and `updatedAt`, both set to the same "now" on create.
- The client can't set them: a `createdAt` in the request body is ignored.
- PATCH moves `updatedAt` forward, including a PATCH that only changes the promo.
  `createdAt` never changes.
- API fields are camelCase, columns snake_case (`created_at`), like `minDeposit`.

Hint: set the time in Python with `datetime.now(timezone.utc)`. Database defaults such as
`func.now()` only have one-second precision in SQLite, so the tests would see no change.

### Your Postgres database needs the columns too

The tests use a fresh SQLite database, but your real `bonuses` table already exists, and
`create_all()` **never changes an existing table**. After Level 3, the running app will
fail with `column bonuses.created_at does not exist` until you add the columns yourself.

Write an `ALTER TABLE bonuses ADD COLUMN ...` for each column and run it with `psql`.
Existing rows have no value yet, so think about what `NOT NULL` requires (look up
`DEFAULT now()`). Then add the same statement to `sql/bonuses.sql`. This manual step is
what migration tools like Alembic automate.

## Level 4: Search, filter, sort, paginate (12 tests)

`GET /bonuses` accepts optional query parameters:

| Param | Meaning | Rules |
|---|---|---|
| `q` | text in the bonus name, description **or promo name**, case-insensitive | optional |
| `maxDeposit` | only bonuses whose `minDeposit` is at most this ("what can I get for $50?") | `>= 0` |
| `sort` | `id` (default): oldest first. `amount`: highest amount first, ties oldest first | anything else is `422` |
| `limit` | max results | default `20`, `1`–`100` |
| `offset` | how many to skip | default `0`, `>= 0` |

All of them can be combined: `/bonuses?q=reload&maxDeposit=100&sort=amount&limit=5`.

Hints:
- Searching the promo name means joining `promos`: `select(BonusRow).join(BonusRow.promo)`.
- `or_(...)`, `.ilike(f"%{q}%")`, `.where(...)` only when a filter was given, `.order_by(a, b)`.
- `sort: Literal["id", "amount"] = "id"` makes FastAPI reject other values for you.
- `Query(20, ge=1, le=100)` for the limits.
- With `lazy="joined"` plus your own join, add `.unique()` to the result if SQLAlchemy asks for it.

### Check on Postgres, not only the tests

SQLite's `LIKE` ignores case for English letters, so the tests pass whether you use `.like()`
or `.ilike()`. PostgreSQL's `LIKE` is case-sensitive. Start the server and check in `/docs` that
`?q=friday` finds a bonus named "FRIDAY50". If it doesn't, you used `.like()`.

---

## Definition of done

- [ ] `pytest tests/test_bonuses_exercise.py`: 37 passed
- [ ] `pytest`: everything passes
- [ ] `pylint $(git ls-files '*.py')`: 10/10
- [ ] Postgres has the new columns, and the running app works at `/docs`
- [ ] `?q=` search checked against Postgres (see above)
- [ ] `sql/bonuses.sql` updated with the new columns and the list query
- [ ] Committed, e.g. `feat: add search, filters and timestamps to bonuses`, and pushed

## Stretch goals (no tests; check them yourself)

1. **Total count:** return `{"items": [...], "total": 42}` so a frontend can show page numbers.
2. **Alembic:** set it up and turn the Level 3 `ALTER TABLE` into your first migration.
3. **Money type:** change `amount` and `min_deposit` to `NUMERIC(12, 2)` (`Decimal` in Python).
4. **AI step:** `POST /bonuses/{id}/explain` sends the promo terms to Claude and returns a
   plain-language explanation of the wagering rules.

---

## Knowledge check

Answer in your own words, then send your answers for review. Don't look at the code for
1–10; do look at it for 11–14.

**SQL**

1. What's the difference between `WHERE` and `HAVING`? Give an example where you need `HAVING`.
2. `LEFT JOIN` vs `INNER JOIN`: which bonuses would disappear from the list with an inner
   join to `promos` if a bonus had no promo? Can that happen in this schema, and why not?
3. Why should `amount` be `NUMERIC(12, 2)` and not `FLOAT`?
4. What does `RETURNING id` do, and why did `sql/bonuses.sql` need it to insert a promo and
   its bonus in one statement?
5. What is a transaction? What happens to a half-finished one if the app crashes?
6. Search uses `ILIKE '%reload%'`. Why can't a normal index speed that up, and what would
   you look into instead?

**SQLAlchemy**

7. Engine vs Session: what does each do, and how many of each does the app create?
8. What's the difference between `session.flush()` and `commit`?
9. In `update()` we never write `UPDATE`. How does SQLAlchemy know what to update?
10. What is the N+1 problem, and which setting in `database.py` avoids it for bonuses?

**This project**

11. Why are there two kinds of models (Pydantic in `schemas.py`, SQLAlchemy in `database.py`)?
    What would go wrong with just one?
12. The tests never touch Postgres, yet they test the real routes. Explain how
    `app.dependency_overrides` and `get_store` make that possible.
13. Why did you have to run `ALTER TABLE` by hand in Level 3, when `create_all()` made the
    table in the first place?
14. Your tests passed with `.like()` but search broke on Postgres. What does that tell you
    about testing on SQLite, and how would you test against Postgres instead?
