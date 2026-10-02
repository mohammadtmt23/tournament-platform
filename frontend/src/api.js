// Local dev and docker-compose use the /api proxy; production sets VITE_API_BASE_URL.
const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = body?.detail
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(', ')
      : detail || res.statusText
    throw new Error(message)
  }
  return body
}

const post = (path, data) =>
  request(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined })

export const createTournament = (name, game) => post('/tournaments', { name, game })
export const addPlayer = (id, name) => post(`/tournaments/${id}/players`, { name })
export const startTournament = (id) => post(`/tournaments/${id}/start`)
export const getBracket = (id) => request(`/tournaments/${id}/bracket`)
export const reportResult = (id, round, position, winnerId) =>
  post(`/tournaments/${id}/matches/${round}/${position}/result`, { winner_id: winnerId })
