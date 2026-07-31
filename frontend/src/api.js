// Falls back to your local backend if no environment variable is set —
// but in production (or whenever you want to test against Railway),
// set VITE_API_BASE in a .env file to override this.
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
 
export async function getIntakeEvents() {
  const res = await fetch(`${API_BASE}/intake-events/`)
  if (!res.ok) throw new Error('Could not load intake events')
  return res.json()
}
 
export async function createIntakeEvent(event) {
  const res = await fetch(`${API_BASE}/intake-events/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
  })
  if (!res.ok) throw new Error('Could not save intake event')
  return res.json()
}
 
export async function getIntakeSummary() {
  const res = await fetch(`${API_BASE}/intake-events/summary`)
  if (!res.ok) throw new Error('Could not load summary')
  return res.json()
}
 
export async function getBatches() {
  const res = await fetch(`${API_BASE}/batches/`)
  if (!res.ok) throw new Error('Could not load batches')
  return res.json()
}
 
export async function createBatch(batch) {
  const res = await fetch(`${API_BASE}/batches/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(batch),
  })
  if (!res.ok) throw new Error('Could not save batch')
  return res.json()
}