function roundName(round, total) {
  const fromEnd = total - round
  if (fromEnd === 0) return 'Final'
  if (fromEnd === 1) return 'Semifinals'
  if (fromEnd === 2) return 'Quarterfinals'
  return `Round ${round}`
}

function PlayerRow({ player, isWinner, canPick, onPick }) {
  if (!player) return <div className="player empty">TBD</div>
  const cls = `player${isWinner ? ' winner' : ''}${canPick ? ' pickable' : ''}`
  if (canPick) {
    return (
      <button className={cls} onClick={onPick} title="Click to advance this player">
        {player.name}
      </button>
    )
  }
  return <div className={cls}>{player.name}</div>
}

function MatchCard({ match, onPick }) {
  const ready = match.status === 'ready'
  return (
    <div className={`match ${match.status}`}>
      <PlayerRow
        player={match.player1}
        isWinner={match.winner && match.winner.id === match.player1?.id}
        canPick={ready}
        onPick={() => onPick(match.player1.id)}
      />
      <PlayerRow
        player={match.player2}
        isWinner={match.winner && match.winner.id === match.player2?.id}
        canPick={ready}
        onPick={() => onPick(match.player2.id)}
      />
      {match.status === 'bye' && <div className="tag">bye</div>}
      {ready && <div className="tag live">click the winner</div>}
    </div>
  )
}

export default function Bracket({ rounds, onReport }) {
  return (
    <div className="bracket">
      {rounds.map((rd) => (
        <div className="round" key={rd.round}>
          <h3>{roundName(rd.round, rounds.length)}</h3>
          <div className="round-matches">
            {rd.matches.map((m) => (
              <MatchCard
                key={m.position}
                match={m}
                onPick={(winnerId) => onReport(rd.round, m.position, winnerId)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
