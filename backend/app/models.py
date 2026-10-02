from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Tournament(Base):
    __tablename__ = "tournaments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    game: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="registration")


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("tournament_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    seed: Mapped[int | None] = mapped_column(default=None)


class MatchRow(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("tournament_id", "round", "position"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    round: Mapped[int]
    position: Mapped[int]
    player1_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), default=None)
    player2_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), default=None)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), default=None)
    status: Mapped[str] = mapped_column(String(20), default="pending")
