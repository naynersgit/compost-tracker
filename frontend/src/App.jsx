import { useEffect, useState } from 'react'
import {
  getIntakeEvents,
  createIntakeEvent,
  getIntakeSummary,
  getBatches,
  createBatch,
  getLoggingSummary,
  getFlaggedEvents,
} from './api'

function IntakeTab() {
  const [events, setEvents] = useState([])
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    material_type: 'food_scraps',
    volume_cy: '',
    hauler: '',
    logged_by: '',
  })

  async function refresh() {
    try {
      const [eventList, summaryData] = await Promise.all([
        getIntakeEvents(),
        getIntakeSummary(),
      ])
      setEvents(eventList)
      setSummary(summaryData)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await createIntakeEvent({
        ...form,
        volume_cy: parseFloat(form.volume_cy),
      })
      setForm({ ...form, volume_cy: '', hauler: '', logged_by: '' })
      await refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className="card">
        <h2>Log a delivery</h2>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Date</label>
            <input
              type="date"
              required
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Material type</label>
            <select
              value={form.material_type}
              onChange={(e) => setForm({ ...form, material_type: e.target.value })}
            >
              <option value="food_scraps">Food scraps</option>
              <option value="green_waste">Green waste</option>
            </select>
          </div>
          <div className="field">
            <label>Volume (cubic yards)</label>
            <input
              type="number"
              step="0.1"
              min="0"
              required
              value={form.volume_cy}
              onChange={(e) => setForm({ ...form, volume_cy: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Hauler</label>
            <input
              type="text"
              value={form.hauler}
              onChange={(e) => setForm({ ...form, hauler: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Logged by</label>
            <input
              type="text"
              value={form.logged_by}
              onChange={(e) => setForm({ ...form, logged_by: e.target.value })}
            />
          </div>
          {error && <div className="error-text">{error}</div>}
          <button type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Log delivery'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Recent deliveries</h2>
        {events.length === 0 ? (
          <div className="empty-state">No deliveries logged yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Material</th>
                <th>Volume (CY)</th>
                <th>Hauler</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id}>
                  <td>{ev.date}</td>
                  <td>{ev.material_type === 'food_scraps' ? 'Food scraps' : 'Green waste'}</td>
                  <td>{ev.volume_cy}</td>
                  <td>{ev.hauler || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}

function BatchesTab() {
  const [batches, setBatches] = useState([])
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const [form, setForm] = useState({
    batch_label: '',
    start_date: new Date().toISOString().slice(0, 10),
    notes: '',
  })

  async function refresh() {
    try {
      setBatches(await getBatches())
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await createBatch(form)
      setForm({ ...form, batch_label: '', notes: '' })
      await refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className="card">
        <h2>Start a batch</h2>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Batch label</label>
            <input
              type="text"
              placeholder="e.g. 2026-07-B01"
              required
              value={form.batch_label}
              onChange={(e) => setForm({ ...form, batch_label: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Start date</label>
            <input
              type="date"
              required
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Notes</label>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </div>
          {error && <div className="error-text">{error}</div>}
          <button type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Start batch'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Batches</h2>
        {batches.length === 0 ? (
          <div className="empty-state">No batches started yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Label</th>
                <th>Started</th>
                <th>Finished</th>
                <th>Output (CY)</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id}>
                  <td>{b.batch_label}</td>
                  <td>{b.start_date}</td>
                  <td>{b.end_date || 'In progress'}</td>
                  <td>{b.finished_volume_cy ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}

function ReviewTab() {
  const [summary, setSummary] = useState([])
  const [flagged, setFlagged] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  async function refresh() {
    setLoading(true)
    try {
      const [summaryData, flaggedData] = await Promise.all([
        getLoggingSummary(),
        getFlaggedEvents(),
      ])
      setSummary(summaryData)
      setFlagged(flaggedData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  return (
    <>
      <div className="card">
        <h2>Who's logged recently</h2>
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : summary.length === 0 ? (
          <div className="empty-state">No entries with a name attached yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Logged by</th>
                <th>Last entry</th>
                <th>Days since</th>
              </tr>
            </thead>
            <tbody>
              {summary.map((row) => (
                <tr key={row.logged_by}>
                  <td>{row.logged_by}</td>
                  <td>{row.last_date}</td>
                  <td style={row.days_since > 3 ? { color: '#a3372f', fontWeight: 600 } : undefined}>
                    {row.days_since}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="empty-state" style={{ marginTop: 8 }}>
          Entries in red haven't logged in over 3 days — adjust this threshold anytime.
        </div>
      </div>

      <div className="card">
        <h2>Entries that need a second look</h2>
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : flagged.length === 0 ? (
          <div className="empty-state">Nothing flagged — all recent entries look complete.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Material</th>
                <th>Volume</th>
                <th>Hauler</th>
                <th>Logged by</th>
                <th>Issue</th>
              </tr>
            </thead>
            <tbody>
              {flagged.map((row) => (
                <tr key={row.id}>
                  <td>{row.date}</td>
                  <td>{row.material_type === 'food_scraps' ? 'Food scraps' : 'Green waste'}</td>
                  <td>{row.volume_cy}</td>
                  <td>{row.hauler || '—'}</td>
                  <td>{row.logged_by || '—'}</td>
                  <td className="error-text">{row.reasons.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {error && <div className="error-text">{error}</div>}
    </>
  )
}

export default function App() {
  const [tab, setTab] = useState('intake')

  return (
    <div className="app">
      <div className="app-header">
        <h1>Compost Tracker</h1>
      </div>

      <div className="tabs">
        <button
          className={`tab ${tab === 'intake' ? 'active' : ''}`}
          onClick={() => setTab('intake')}
        >
          Intake
        </button>
        <button
          className={`tab ${tab === 'batches' ? 'active' : ''}`}
          onClick={() => setTab('batches')}
        >
          Batches
        </button>
        <button
          className={`tab ${tab === 'review' ? 'active' : ''}`}
          onClick={() => setTab('review')}
        >
          Review
        </button>
      </div>

      {tab === 'intake' && <IntakeTab />}
      {tab === 'batches' && <BatchesTab />}
      {tab === 'review' && <ReviewTab />}
    </div>
  )
}
