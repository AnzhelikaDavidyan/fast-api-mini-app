-- =============================================================================
-- Raw SQL reference for the Bonuses API (PostgreSQL)
-- =============================================================================
--
-- NOTE: The app does NOT run this file. It talks to the database through
-- SQLAlchemy (ORM):
--   - app/database.py  defines the tables (BonusRow -> bonuses, PromoRow -> promos)
--                      and creates them on startup with Base.metadata.create_all()
--   - app/store.py     builds every query below with SQLAlchemy
--
-- This file shows the plain SQL equivalent of what SQLAlchemy sends, so you can
-- read it, run pieces of it in psql / DBeaver, or rebuild the schema by hand.
-- If you change the models in app/database.py, update this file to match.
--
-- Run it all (creates tables if missing, then runs the example queries):
--   psql -U bonuses_user -d bonuses -f sql/bonuses.sql
-- The examples run inside BEGIN ... ROLLBACK, so they never change your data.
-- Values in the examples (ids, names, amounts) are placeholders; SQLAlchemy
-- sends them as bound parameters instead.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Schema  (SQLAlchemy: Base.metadata.create_all in app/database.py)
-- -----------------------------------------------------------------------------
-- One-to-one: every bonus owns exactly one promo through bonuses.promo_id.

CREATE TABLE IF NOT EXISTS promos (
    id      SERIAL       PRIMARY KEY,
    name    VARCHAR(120) NOT NULL,
    terms   TEXT         NOT NULL,
    offer   TEXT         NOT NULL
);

CREATE TABLE IF NOT EXISTS bonuses (
    id          SERIAL           PRIMARY KEY,
    name        VARCHAR(120)     NOT NULL,
    description TEXT             NOT NULL,
    min_deposit DOUBLE PRECISION NOT NULL,
    amount      DOUBLE PRECISION NOT NULL,
    promo_id    INTEGER          NOT NULL UNIQUE REFERENCES promos (id)
);


-- Everything below is an example query. The transaction is rolled back at the
-- end of the file, so running it leaves the data untouched.
BEGIN;


-- -----------------------------------------------------------------------------
-- Create a bonus with its promo  (BonusStore.create -> POST /bonuses)
-- -----------------------------------------------------------------------------
-- SQLAlchemy runs two INSERTs in one transaction: the promo first, then the
-- bonus pointing at the new promo id. Same thing as a single statement:

WITH new_promo AS (
    INSERT INTO promos (name, terms, offer)
    VALUES ('WELCOME100', 'Wagering x35, valid 7 days', '100% up to $100')
    RETURNING id
)
INSERT INTO bonuses (name, description, min_deposit, amount, promo_id)
SELECT 'Welcome Bonus', '100% on your first deposit', 20, 100, id
FROM new_promo
RETURNING id;


-- -----------------------------------------------------------------------------
-- List all bonuses with their promos  (BonusStore.list_all -> GET /bonuses)
-- -----------------------------------------------------------------------------
-- relationship(lazy="joined") in app/database.py is why the promo is joined in.

SELECT b.id, b.name, b.description, b.min_deposit, b.amount,
       p.id AS promo_id, p.name AS promo_name, p.terms, p.offer
FROM bonuses AS b
LEFT JOIN promos AS p ON p.id = b.promo_id
ORDER BY b.id;


-- -----------------------------------------------------------------------------
-- Get one bonus  (BonusStore.get -> GET /bonuses/{id})
-- -----------------------------------------------------------------------------
-- No row means the API answers 404.

SELECT b.id, b.name, b.description, b.min_deposit, b.amount,
       p.id AS promo_id, p.name AS promo_name, p.terms, p.offer
FROM bonuses AS b
LEFT JOIN promos AS p ON p.id = b.promo_id
WHERE b.id = 1;


-- -----------------------------------------------------------------------------
-- Update a bonus  (BonusStore.update -> PATCH /bonuses/{id})
-- -----------------------------------------------------------------------------
-- Only the fields sent in the request are changed. API field minDeposit is
-- column min_deposit. Example: PATCH {"amount": 150, "minDeposit": 25}

UPDATE bonuses
SET amount = 150, min_deposit = 25
WHERE id = 1;

-- If the request includes "promo", its content is replaced but its id is kept:

UPDATE promos
SET name = 'WELCOME150', terms = 'Wagering x30, valid 7 days', offer = '100% up to $150'
WHERE id = (SELECT promo_id FROM bonuses WHERE id = 1);


-- -----------------------------------------------------------------------------
-- Delete a bonus and its promo  (BonusStore.delete -> DELETE /bonuses/{id})
-- -----------------------------------------------------------------------------
-- cascade="all, delete-orphan" makes SQLAlchemy delete the promo too.
-- The bonus goes first because it holds the foreign key.

WITH deleted AS (
    DELETE FROM bonuses
    WHERE id = 1
    RETURNING promo_id
)
DELETE FROM promos
WHERE id IN (SELECT promo_id FROM deleted);


-- Undo all the example changes above. Use COMMIT instead to keep them.
ROLLBACK;
