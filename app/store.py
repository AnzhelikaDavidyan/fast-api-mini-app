from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.database import BonusRow, PromoRow, init_db, make_engine
from app.schemas import Bonus, BonusCreate, BonusUpdate, Promo

# API field name -> column name, where they differ.
_COLUMNS = {"minDeposit": "min_deposit"}


def _to_schema(row: BonusRow) -> Bonus:
    return Bonus(
        id=row.id,
        name=row.name,
        description=row.description,
        minDeposit=row.min_deposit,
        amount=row.amount,
        promo=Promo(id=row.promo.id, name=row.promo.name, terms=row.promo.terms, offer=row.promo.offer),
    )


class BonusStore:
    """SQL-backed storage. Routes only see this interface."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session = session_factory

    def list_all(self) -> list[Bonus]:
        with self._session() as s:
            rows = s.scalars(select(BonusRow).order_by(BonusRow.id))
            return [_to_schema(r) for r in rows]

    def get(self, bonus_id: int) -> Bonus | None:
        with self._session() as s:
            row = s.get(BonusRow, bonus_id)
            return _to_schema(row) if row else None

    def create(self, data: BonusCreate) -> Bonus:
        with self._session.begin() as s:
            row = BonusRow(
                name=data.name,
                description=data.description,
                min_deposit=data.minDeposit,
                amount=data.amount,
                promo=PromoRow(**data.promo.model_dump()),
            )
            s.add(row)
            s.flush()
            return _to_schema(row)

    def update(self, bonus_id: int, data: BonusUpdate) -> Bonus | None:
        with self._session.begin() as s:
            row = s.get(BonusRow, bonus_id)
            if row is None:
                return None
            changes = data.model_dump(exclude_unset=True, exclude_none=True)
            if "promo" in changes:
                # Keep the promo's id; replace its content.
                for field, value in changes.pop("promo").items():
                    setattr(row.promo, field, value)
            for field, value in changes.items():
                setattr(row, _COLUMNS.get(field, field), value)
            s.flush()
            return _to_schema(row)

    def delete(self, bonus_id: int) -> bool:
        with self._session.begin() as s:
            row = s.get(BonusRow, bonus_id)
            if row is None:
                return False
            s.delete(row)
            return True


_store: BonusStore | None = None


def get_store() -> BonusStore:
    global _store
    if _store is None:
        _store = BonusStore(init_db(make_engine()))
    return _store
