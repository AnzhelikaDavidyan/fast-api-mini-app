import os

from dotenv import load_dotenv
from sqlalchemy import Engine, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

load_dotenv()  # picks up DATABASE_URL from .env; a real env var still wins
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bonuses.db")


class Base(DeclarativeBase):
    pass


class PromoRow(Base):
    __tablename__ = "promos"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    terms: Mapped[str] = mapped_column(Text)
    offer: Mapped[str] = mapped_column(Text)


class BonusRow(Base):
    __tablename__ = "bonuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    min_deposit: Mapped[float]
    amount: Mapped[float]
    promo_id: Mapped[int] = mapped_column(ForeignKey("promos.id"), unique=True)

    promo: Mapped[PromoRow] = relationship(lazy="joined", cascade="all, delete-orphan", single_parent=True)


def make_engine(url: str = DATABASE_URL, **kwargs) -> Engine:
    if url.startswith("sqlite"):
        kwargs.setdefault("connect_args", {"check_same_thread": False})
    return create_engine(url, **kwargs)


def init_db(engine: Engine) -> sessionmaker:
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
