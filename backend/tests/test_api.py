import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_tournament(client, n_players):
    tid = client.post("/tournaments", json={"name": "Spring Open", "game": "Rocket League"}).json()["id"]
    for i in range(n_players):
        assert client.post(f"/tournaments/{tid}/players", json={"name": f"P{i + 1}"}).status_code == 201
    return tid


def test_start_creates_bracket_with_byes(client):
    tid = make_tournament(client, 5)
    r = client.post(f"/tournaments/{tid}/start")
    assert r.status_code == 200
    data = r.json()
    assert [len(rd["matches"]) for rd in data["rounds"]] == [4, 2, 1]
    assert sum(m["status"] == "bye" for m in data["rounds"][0]["matches"]) == 3
    assert data["tournament"]["status"] == "in_progress"


def test_play_full_tournament(client):
    tid = make_tournament(client, 6)
    data = client.post(f"/tournaments/{tid}/start").json()
    for _ in range(3):  # at most 3 rounds
        for rd in data["rounds"]:
            for m in rd["matches"]:
                if m["status"] == "ready":
                    r = client.post(
                        f"/tournaments/{tid}/matches/{rd['round']}/{m['position']}/result",
                        json={"winner_id": m["player1"]["id"]})
                    assert r.status_code == 200
                    data = r.json()
    assert data["champion"] is not None
    assert data["tournament"]["status"] == "complete"


def test_cannot_start_with_one_player(client):
    tid = make_tournament(client, 1)
    assert client.post(f"/tournaments/{tid}/start").status_code == 409


def test_cannot_register_after_start(client):
    tid = make_tournament(client, 2)
    client.post(f"/tournaments/{tid}/start")
    r = client.post(f"/tournaments/{tid}/players", json={"name": "Late"})
    assert r.status_code == 409


def test_duplicate_player_name_rejected(client):
    tid = make_tournament(client, 1)
    r = client.post(f"/tournaments/{tid}/players", json={"name": "P1"})
    assert r.status_code == 409


def test_bad_result_requests(client):
    tid = make_tournament(client, 4)
    client.post(f"/tournaments/{tid}/start")
    assert client.post(f"/tournaments/{tid}/matches/1/0/result", json={"winner_id": 9999}).status_code == 400
    assert client.post(f"/tournaments/{tid}/matches/2/0/result", json={"winner_id": 1}).status_code == 409
    assert client.post(f"/tournaments/{tid}/matches/9/9/result", json={"winner_id": 1}).status_code == 404
    assert client.get("/tournaments/999/bracket").status_code == 404


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_cors_headers_present(client):
    r = client.options("/tournaments", headers={
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
    })
    assert r.headers.get("access-control-allow-origin") in ("*", "https://example.com")
