"""Single-elimination bracket logic. Pure functions, no database.

Matches are addressed by (round, position). Round 1 is the first round.
The winner of (r, p) advances to (r + 1, p // 2); even positions fill
player1 of the next match, odd positions fill player2.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Match:
    round: int
    position: int
    player1: Optional[int] = None
    player2: Optional[int] = None
    winner: Optional[int] = None
    status: str = "pending"  # pending | ready | complete | bye


def seed_order(size: int) -> list[int]:
    """Standard bracket seeding for a power-of-two size.

    size=8 -> [1, 8, 4, 5, 2, 7, 3, 6], so seeds 1 and 2 can only meet
    in the final, and top seeds get the byes when the field is short.
    """
    order = [1]
    while len(order) < size:
        n = len(order) * 2
        order = [x for s in order for x in (s, n + 1 - s)]
    return order


def _next_power_of_two(n: int) -> int:
    size = 1
    while size < n:
        size *= 2
    return size


def _advance(matches: dict, m: Match) -> None:
    """Move m's winner into the next round, if there is one."""
    nxt = matches.get((m.round + 1, m.position // 2))
    if nxt is None:
        return
    if m.position % 2 == 0:
        nxt.player1 = m.winner
    else:
        nxt.player2 = m.winner
    if nxt.player1 is not None and nxt.player2 is not None:
        nxt.status = "ready"


def generate_bracket(player_ids: list[int]) -> dict[tuple[int, int], Match]:
    """Build a full single-elimination bracket.

    player_ids must be in seed order (index 0 = seed 1). Byes are given
    to the top seeds and resolved immediately.
    """
    n = len(player_ids)
    if n < 2:
        raise ValueError("need at least 2 players")
    if len(set(player_ids)) != n:
        raise ValueError("duplicate players")

    size = _next_power_of_two(n)
    n_rounds = size.bit_length() - 1
    slots = [player_ids[s - 1] if s <= n else None for s in seed_order(size)]

    matches: dict[tuple[int, int], Match] = {}
    for r in range(1, n_rounds + 1):
        for p in range(size // (2 ** r)):
            matches[(r, p)] = Match(round=r, position=p)

    for p in range(size // 2):
        m = matches[(1, p)]
        m.player1, m.player2 = slots[2 * p], slots[2 * p + 1]
        if m.player1 is not None and m.player2 is not None:
            m.status = "ready"
        else:  # bye: the lone player advances automatically
            m.winner = m.player1 if m.player1 is not None else m.player2
            m.status = "bye"
            _advance(matches, m)
    return matches


def report_result(matches: dict, round_: int, position: int, winner: int) -> Match:
    """Record a winner and advance them. Raises ValueError on bad input."""
    m = matches.get((round_, position))
    if m is None:
        raise ValueError("no such match")
    if m.status != "ready":
        raise ValueError(f"match is not ready (status={m.status})")
    if winner not in (m.player1, m.player2):
        raise ValueError("winner is not a player in this match")
    m.winner = winner
    m.status = "complete"
    _advance(matches, m)
    return m


def champion(matches: dict) -> Optional[int]:
    final_round = max(r for r, _ in matches)
    return matches[(final_round, 0)].winner
