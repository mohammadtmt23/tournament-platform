import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import bracket as bk
from .db import Base, engine, get_db
from .models import MatchRow, Player, Tournament
from .schemas import PlayerCreate, ResultIn, TournamentCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Tournament Platform", lifespan=lifespan)

# The API has no cookies or auth, so a wildcard origin is acceptable here.
# Set CORS_ORIGINS="https://your-site.com,https://other.com" to restrict it.
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


def _get_tournament(db: Session, tid: int) -> Tournament:
    t = db.get(Tournament, tid)
    if t is None:
        raise HTTPException(404, "tournament not found")
    return t


def _bracket_view(db: Session, t: Tournament) -> dict:
    players = db.scalars(select(Player).where(Player.tournament_id == t.id)
                         .order_by(Player.seed, Player.id)).all()
    names = {p.id: p.name for p in players}
    rows = db.scalars(select(MatchRow).where(MatchRow.tournament_id == t.id)
                      .order_by(MatchRow.round, MatchRow.position)).all()

    def ref(pid):
        return None if pid is None else {"id": pid, "name": names[pid]}

    rounds: dict[int, list] = {}
    for m in rows:
        rounds.setdefault(m.round, []).append({
            "position": m.position, "status": m.status,
            "player1": ref(m.player1_id), "player2": ref(m.player2_id),
            "winner": ref(m.winner_id),
        })
    final = next((m for m in rows if m.round == max((r.round for r in rows), default=0)), None)
    return {
        "tournament": {"id": t.id, "name": t.name, "game": t.game, "status": t.status},
        "players": [{"id": p.id, "name": p.name, "seed": p.seed} for p in players],
        "rounds": [{"round": r, "matches": ms} for r, ms in sorted(rounds.items())],
        "champion": ref(final.winner_id) if final and final.winner_id else None,
    }


@app.post("/tournaments", status_code=201)
def create_tournament(body: TournamentCreate, db: Session = Depends(get_db)):
    t = Tournament(name=body.name, game=body.game)
    db.add(t)
    db.commit()
    return {"id": t.id, "name": t.name, "game": t.game, "status": t.status}


@app.post("/tournaments/{tid}/players", status_code=201)
def register_player(tid: int, body: PlayerCreate, db: Session = Depends(get_db)):
    t = _get_tournament(db, tid)
    if t.status != "registration":
        raise HTTPException(409, "registration is closed")
    p = Player(tournament_id=tid, name=body.name.strip())
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "player name already registered")
    return {"id": p.id, "name": p.name}


@app.post("/tournaments/{tid}/start")
def start_tournament(tid: int, db: Session = Depends(get_db)):
    t = _get_tournament(db, tid)
    if t.status != "registration":
        raise HTTPException(409, "tournament already started")
    players = db.scalars(select(Player).where(Player.tournament_id == tid)
                         .order_by(Player.id)).all()
    if len(players) < 2:
        raise HTTPException(409, "need at least 2 players to start")
    for i, p in enumerate(players, start=1):  # seed = registration order
        p.seed = i
    matches = bk.generate_bracket([p.id for p in players])
    for (r, pos), m in matches.items():
        db.add(MatchRow(tournament_id=tid, round=r, position=pos,
                        player1_id=m.player1, player2_id=m.player2,
                        winner_id=m.winner, status=m.status))
    t.status = "in_progress"
    db.commit()
    return _bracket_view(db, t)


@app.get("/tournaments/{tid}/bracket")
def get_bracket(tid: int, db: Session = Depends(get_db)):
    return _bracket_view(db, _get_tournament(db, tid))


@app.post("/tournaments/{tid}/matches/{round_}/{position}/result")
def report_match_result(tid: int, round_: int, position: int, body: ResultIn,
                        db: Session = Depends(get_db)):
    t = _get_tournament(db, tid)
    rows = db.scalars(select(MatchRow).where(MatchRow.tournament_id == tid)).all()
    if not rows:
        raise HTTPException(409, "tournament has not started")
    by_key = {(r.round, r.position): r for r in rows}
    row = by_key.get((round_, position))
    if row is None:
        raise HTTPException(404, "match not found")
    if row.status != "ready":
        raise HTTPException(409, f"match is not ready (status={row.status})")
    if body.winner_id not in (row.player1_id, row.player2_id):
        raise HTTPException(400, "winner is not a player in this match")

    # Rebuild the in-memory bracket, apply the result with the tested engine,
    # then write back every row that changed.
    mem = {k: bk.Match(r.round, r.position, r.player1_id, r.player2_id,
                       r.winner_id, r.status) for k, r in by_key.items()}
    bk.report_result(mem, round_, position, body.winner_id)
    for k, m in mem.items():
        r = by_key[k]
        r.player1_id, r.player2_id = m.player1, m.player2
        r.winner_id, r.status = m.winner, m.status
    if bk.champion(mem) is not None:
        t.status = "complete"
    db.commit()
    return _bracket_view(db, t)
