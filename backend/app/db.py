from __future__ import annotations

import os
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./qeymatban.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), default="ملک جدید")
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    neighborhood: Mapped[str] = mapped_column(String(100), index=True)
    city: Mapped[str] = mapped_column(String(100), default="تهران")
    area_sqm: Mapped[float] = mapped_column(Float)
    year_built: Mapped[int] = mapped_column(Integer)
    floor: Mapped[int] = mapped_column(Integer)
    total_floors: Mapped[int] = mapped_column(Integer)
    rooms: Mapped[int] = mapped_column(Integer)
    has_parking: Mapped[bool] = mapped_column(Boolean, default=False)
    has_elevator: Mapped[bool] = mapped_column(Boolean, default=False)
    has_storage: Mapped[bool] = mapped_column(Boolean, default=False)
    renovated: Mapped[bool] = mapped_column(Boolean, default=False)
    light_score: Mapped[int] = mapped_column(Integer)
    view_score: Mapped[int] = mapped_column(Integer)
    access_score: Mapped[int] = mapped_column(Integer)
    listed_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions: Mapped[list[Transaction]] = relationship(back_populates="property", cascade="all, delete-orphan")
    valuations: Mapped[list[Valuation]] = relationship(back_populates="property", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    sold_price: Mapped[float] = mapped_column(Float)
    sold_date: Mapped[date] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    property: Mapped[Property] = relationship(back_populates="transactions")


class Valuation(Base):
    __tablename__ = "valuations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    price_low: Mapped[float] = mapped_column(Float)
    price_mid: Mapped[float] = mapped_column(Float)
    price_high: Mapped[float] = mapped_column(Float)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.8)
    shap_values: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    model_version: Mapped[str] = mapped_column(String(100), default="heuristic-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    property: Mapped[Property] = relationship(back_populates="valuations")
    comparables: Mapped[list[ValuationComparable]] = relationship(cascade="all, delete-orphan")


class ValuationComparable(Base):
    __tablename__ = "valuation_comparables"

    valuation_id: Mapped[str] = mapped_column(ForeignKey("valuations.id", ondelete="CASCADE"), primary_key=True)
    comparable_id: Mapped[str] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True)
    similarity: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_demo_properties() -> None:
    with SessionLocal() as session:
        if session.scalar(select(Property.id).limit(1)):
            return
        demo = [
            ("آپارتمان دوخوابه، نیاوران", 148, 1400, 3, 5, 3, True, True, True, True, 5, 4, 5, 24_800_000_000),
            ("واحد نوساز، کامرانیه", 155, 1402, 5, 7, 3, True, True, True, False, 5, 5, 4, 27_200_000_000),
            ("آپارتمان خوش‌نقشه، دزاشیب", 136, 1399, 2, 4, 3, True, True, False, True, 4, 4, 5, 22_900_000_000),
            ("واحد نورگیر، نیاوران", 142, 1401, 4, 6, 3, True, True, True, False, 5, 4, 5, 24_100_000_000),
            ("آپارتمان خانوادگی، جماران", 160, 1398, 1, 4, 4, True, True, True, True, 4, 5, 4, 25_600_000_000),
            ("واحد دنج، فرمانیه", 130, 1397, 3, 5, 2, False, True, True, True, 4, 4, 5, 21_700_000_000),
        ]
        for item in demo:
            title, area, year, floor, total_floors, rooms, parking, elevator, storage, renovated, light, view, access, price = item
            session.add(Property(title=title, neighborhood="نیاوران", city="تهران", area_sqm=area, year_built=year, floor=floor, total_floors=total_floors, rooms=rooms, has_parking=parking, has_elevator=elevator, has_storage=storage, renovated=renovated, light_score=light, view_score=view, access_score=access, listed_price=price))
        session.commit()
