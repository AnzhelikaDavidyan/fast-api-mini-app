from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.schemas import Bonus, BonusCreate, BonusUpdate
from app.store import BonusStore, get_store

router = APIRouter(prefix="/bonuses", tags=["bonuses"])


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonus not found")


@router.get("", response_model=list[Bonus])
def list_bonuses(store: BonusStore = Depends(get_store)):
    return store.list_all()


@router.post("", response_model=Bonus, status_code=status.HTTP_201_CREATED)
def create_bonus(payload: BonusCreate, store: BonusStore = Depends(get_store)):
    return store.create(payload)


@router.get("/{bonus_id}", response_model=Bonus)
def get_bonus(bonus_id: int, store: BonusStore = Depends(get_store)):
    bonus = store.get(bonus_id)
    if bonus is None:
        raise _not_found()
    return bonus


@router.patch("/{bonus_id}", response_model=Bonus)
def update_bonus(bonus_id: int, payload: BonusUpdate, store: BonusStore = Depends(get_store)):
    bonus = store.update(bonus_id, payload)
    if bonus is None:
        raise _not_found()
    return bonus


@router.delete("/{bonus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bonus(bonus_id: int, store: BonusStore = Depends(get_store)):
    if not store.delete(bonus_id):
        raise _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
