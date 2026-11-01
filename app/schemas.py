from pydantic import BaseModel, Field


class PromoIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    terms: str = Field(..., min_length=1)
    offer: str = Field(..., min_length=1)


class Promo(PromoIn):
    id: int


class BonusCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    minDeposit: float = Field(..., ge=0)
    amount: float = Field(..., ge=0)
    promo: PromoIn


class BonusUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = None
    minDeposit: float | None = Field(None, ge=0)
    amount: float | None = Field(None, ge=0)
    promo: PromoIn | None = None


class Bonus(BaseModel):
    id: int
    name: str
    description: str
    minDeposit: float
    amount: float
    promo: Promo
