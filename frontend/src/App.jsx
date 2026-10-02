import { useCallback, useEffect, useState } from 'react'
import * as api from './api'
import Bracket from './Bracket.jsx'

// The tournament id lives in the URL hash (#/t/3) so a bracket is shareable.
function readHash() {
  const m = window.location.hash.match(/^#\/t\/(\d+)$/)
  return m ? Number(m[1]) : null
}

function CreateForm({ onCreated, onError }) {
  const [name, setName] = useState('')
  const [game, setGame] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      const t = await api.createTournament(name, game)
      onCreated(t.id)
    } catch (err) {
      onError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Create a tournament</h2>
      <input placeholder="Tournament name" value={name}
             onChange={(e) => setName(e.target.value)} required />
      <input placeholder="Game" value={game}
             onChange={(e) => setGame(e.target.value)} required />
      <button type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create'}</button>
      {busy && (
        <p className="muted">
          The server sleeps when idle on free hosting, so the first request can take up to a minute.
        </p>
      )}
    </form>
  )
}

function Registration({ tid, data, refresh, onError }) {
  const [name, setName] = useState('')

  async function add(e) {
    e.preventDefault()
    try {
      await api.addPlayer(tid, name)
      setName('')
      refresh()
    } catch (err) {
      onError(err.message)
    }
  }

  async function start() {
    try {
      await api.startTournament(tid)
      refresh()
    } catch (err) {
      onError(err.message)
    }
  }

  return (
    <div className="card">
      <h2>Registration</h2>
      <p className="muted">Players are seeded in the order they register.</p>
      <form className="row" onSubmit={add}>
        <input placeholder="Player name" value={name}
               onChange={(e) => setName(e.target.value)} required />
        <button type="submit">Add player</button>
      </form>
      <ol className="players">
        {data.players.map((p) => <li key={p.id}>{p.name}</li>)}
      </ol>
      <button onClick={start} disabled={data.players.length < 2}>
        Start tournament ({data.players.length} players)
      </button>
    </div>
  )
}

export default function App() {
  const [tid, setTid] = useState(readHash())
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const onHash = () => { setTid(readHash()); setData(null); setError('') }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const refresh = useCallback(async () => {
    if (!tid) return
    try {
      setData(await api.getBracket(tid))
    } catch (err) {
      setError(err.message)
    }
  }, [tid])

  // Poll so everyone viewing the same bracket sees updates.
  useEffect(() => {
    refresh()
    if (!tid) return
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [tid, refresh])

  async function report(round, position, winnerId) {
    try {
      setData(await api.reportResult(tid, round, position, winnerId))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="app">
      <header>
        <a href="#/" className="brand">Tournament Platform</a>
      </header>

      {error && (
        <div className="error" onClick={() => setError('')}>{error} (click to dismiss)</div>
      )}

      {!tid && (
        <CreateForm
          onCreated={(id) => { window.location.hash = `#/t/${id}` }}
          onError={setError}
        />
      )}

      {tid && !data && !error && <p className="muted">Loading…</p>}

      {tid && data && (
        <>
          <div className="title">
            <h1>{data.tournament.name}</h1>
            <span className="muted">{data.tournament.game} · {data.tournament.status.replace('_', ' ')}</span>
          </div>

          {data.champion && (
            <div className="champion">🏆 Champion: {data.champion.name}</div>
          )}

          {data.tournament.status === 'registration' ? (
            <Registration tid={tid} data={data} refresh={refresh} onError={setError} />
          ) : (
            <Bracket rounds={data.rounds} onReport={report} />
          )}
        </>
      )}
    </div>
  )
}
