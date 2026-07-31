import { useEffect, useState } from 'react'
import { Menu, Leaf, Layers, ClipboardCheck } from 'lucide-react'
import {
  getIntakeEvents,
  createIntakeEvent,
  getIntakeSummary,
  getBatches,
  createBatch,
  getLoggingSummary,
  getFlaggedEvents,
} from './api'

function PillGroup({ options, value, onChange }) {
  return (
    <div className="pill-group">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={`pill ${value === opt.value ? 'selected' : ''}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

function Field({ label, required, children }) {
  return (
    <div className="field">
      <div className="field-label-row">
        <label>{label}</label>
        {required && <span className="required-tag">Required</span>}
      </div>
      {children}
    </div>
  )
}

function SuggestInput({ id, value, onChange, options, placeholder }) {
  return (
    <>
      <input
        list={id}
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      <datalist id={id}>
        {options.map((opt) => (
          <option key={opt} value={opt} />
        ))}
      </datalist>
    </>
  )
}

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

  const canSubmit = form.date && form.material_type && form.volume_cy !== ''

  const haulerOptions = [...new Set(events.map((ev) => ev.hauler).filter(Boolean))].sort()
  const loggerOptions = [...new Set(events.map((ev) => ev.logged_by).filter(Boolean))].sort()

  return (
    <>
      <div className="card">
        <h2>Food &amp; Green Waste Diversion</h2>
        <p className="card-subtitle">
          Log the material delivered to your site today. Enter total volume in cubic yards.
        </p>
        <form onSubmit={handleSubmit}>
          <Field label="Material type" required>
            <PillGroup
              options={[
                { value: 'food_scraps', label: 'Food scraps' },
                { value: 'green_waste', label: 'Green waste' },
              ]}
              value={form.material_type}
              onChange={(v) => setForm({ ...form, material_type: v })}
            />
          </Field>
          <Field label="Volume (cubic yards)" required>
            <input
              type="number"
              step="0.1"
              min="0"
              required
              value={form.volume_cy}
              onChange={(e) => setForm({ ...form, volume_cy: e.target.value })}
            />
          </Field>
          <Field label="Hauler">
            <SuggestInput
              id="hauler-options"
              value={form.hauler}
              onChange={(v) => setForm({ ...form, hauler: v })}
              options={haulerOptions}
              placeholder="Select or type a hauler"
            />
          </Field>
          <Field label="Logged by">
            <SuggestInput
              id="logger-options"
              value={form.logged_by}
              onChange={(v) => setForm({ ...form, logged_by: v })}
              options={loggerOptions}
              placeholder="Select or type your name"
            />
          </Field>
          <Field label="Date" required>
            <input
              type="date"
              required
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
            />
          </Field>
          {error && <div className="error-text">{error}</div>}
          <button type="submit" disabled={saving || !canSubmit}>
            {saving ? 'Saving…' : 'Submit'}
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

  const canSubmit = form.batch_label && form.start_date

  return (
    <>
      <div className="card">
        <h2>Start a batch</h2>
        <p className="card-subtitle">Give the new batch a label and today's date.</p>
        <form onSubmit={handleSubmit}>
          <Field label="Batch label" required>
            <input
              type="text"
              placeholder="e.g. 2026-07-B01"
              required
              value={form.batch_label}
              onChange={(e) => setForm({ ...form, batch_label: e.target.value })}
            />
          </Field>
          <Field label="Start date" required>
            <input
              type="date"
              required
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            />
          </Field>
          <Field label="Notes">
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </Field>
          {error && <div className="error-text">{error}</div>}
          <button type="submit" disabled={saving || !canSubmit}>
            {saving ? 'Saving…' : 'Submit'}
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
                  <td style={row.days_since > 3 ? { color: 'var(--danger)', fontWeight: 700 } : undefined}>
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

const TABS = [
  { key: 'intake', label: 'Diversion', title: 'Food & Greens Diversion', icon: Leaf, Component: IntakeTab },
  { key: 'batches', label: 'Batches', title: 'Batches', icon: Layers, Component: BatchesTab },
  { key: 'review', label: 'Review', title: 'Review', icon: ClipboardCheck, Component: ReviewTab },
]

export default function App() {
  const [tab, setTab] = useState('intake')
  const current = TABS.find((t) => t.key === tab)
  const Active = current.Component

  return (
    <div className="app">
      <div className="app-header">
        <div className="menu-icon" aria-hidden="true">
          <Menu size={22} color="#fff" />
        </div>
        <h1>{current.title}</h1>
        <div style={{ width: 32 }} />
      </div>

      <div className="page-content">
        <Active />
      </div>

      <nav className="bottom-nav">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            className={`nav-item ${tab === key ? 'active' : ''}`}
            onClick={() => setTab(key)}
          >
            <Icon size={22} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
