import pytest

from app.bracket import champion, generate_bracket, report_result, seed_order


def test_seed_order_8():
    assert seed_order(8) == [1, 8, 4, 5, 2, 7, 3, 6]


@pytest.mark.parametrize("n", range(2, 33))
def test_structure_for_every_field_size(n):
    players = list(range(1, n + 1))
    b = generate_bracket(players)
    size = 1
    while size < n:
        size *= 2
    assert len(b) == size - 1  # a single-elim bracket has size-1 matches
    round1 = [m for (r, _), m in b.items() if r == 1]
    # every player appears exactly once in round 1
    seen = [p for m in round1 for p in (m.player1, m.player2) if p is not None]
    assert sorted(seen) == players
    # byes = size - n
    assert sum(m.status == "bye" for m in round1) == size - n


def test_top_seeds_get_byes():
    b = generate_bracket([1, 2, 3, 4, 5])  # size 8 -> seeds 1,2,3 get byes
    byes = {m.winner for (r, _), m in b.items() if r == 1 and m.status == "bye"}
    assert byes == {1, 2, 3}


def test_seeds_1_and_2_only_meet_in_final():
    b = generate_bracket(list(range(1, 9)))
    # play every match, always picking the better (lower-numbered) seed
    for r in (1, 2, 3):
        for (rr, p), m in sorted(b.items()):
            if rr == r and m.status == "ready":
                report_result(b, rr, p, min(m.player1, m.player2))
    final = b[(3, 0)]
    assert champion(b) == 1
    assert {final.player1, final.player2} == {1, 2}


@pytest.mark.parametrize("n", [2, 3, 5, 7, 8, 13, 16])
def test_full_tournament_produces_one_champion(n):
    b = generate_bracket(list(range(1, n + 1)))
    max_round = max(r for r, _ in b)
    for r in range(1, max_round + 1):
        for (rr, p), m in sorted(b.items()):
            if rr == r and m.status == "ready":
                report_result(b, rr, p, m.player1)
    assert champion(b) is not None
    assert all(m.status in ("complete", "bye") for m in b.values())


def test_rejects_bad_results():
    b = generate_bracket([1, 2, 3, 4])
    with pytest.raises(ValueError):
        report_result(b, 1, 0, 99)  # not a player in the match
    with pytest.raises(ValueError):
        report_result(b, 2, 0, 1)  # final is not ready yet
    report_result(b, 1, 0, 1)
    with pytest.raises(ValueError):
        report_result(b, 1, 0, 1)  # already complete


def test_input_validation():
    with pytest.raises(ValueError):
        generate_bracket([1])
    with pytest.raises(ValueError):
        generate_bracket([1, 1, 2])
