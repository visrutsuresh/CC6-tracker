import { useState, useEffect, useCallback } from 'react'
import {
  loadHistory,
  saveDailyCounts,
  submitSaveRequest,
  getPendingRequests,
  approveRequest,
  rejectRequest,
} from './lib/data'
import { hasSupabase } from './lib/supabase'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import './App.css'

const ADMIN_USERNAME = 'admin123'
const ADMIN_PASSWORD = 'password123'

const COLORS = { are_you_with_me: '#22c55e', thumbs_up: '#3b82f6' }

function App() {
  const [areCount, setAreCount] = useState(0)
  const [thumbsCount, setThumbsCount] = useState(0)
  const [isAdmin, setIsAdmin] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [showStats, setShowStats] = useState(false)
  const [popEmoji, setPopEmoji] = useState(null)
  const [history, setHistory] = useState([])
  const [pendingRequests, setPendingRequests] = useState([])
  const [message, setMessage] = useState(null)
  const [messageType, setMessageType] = useState('success')
  const [loading, setLoading] = useState(false)
  const [selectedDate, setSelectedDate] = useState(() => {
    const d = new Date()
    return d.toISOString().slice(0, 10)
  })
  const [statsView, setStatsView] = useState('Line chart')

  const refreshHistory = useCallback(async () => {
    const data = await loadHistory()
    setHistory(data)
  }, [])

  const refreshPending = useCallback(async () => {
    if (hasSupabase()) {
      const reqs = await getPendingRequests()
      setPendingRequests(reqs)
    }
  }, [])

  useEffect(() => {
    refreshHistory()
    refreshPending()
  }, [refreshHistory, refreshPending])

  const showMsg = (msg, type = 'success') => {
    setMessage(msg)
    setMessageType(type)
    setTimeout(() => setMessage(null), 4000)
  }

  const setPop = (emoji) => {
    setPopEmoji(emoji)
    setTimeout(() => setPopEmoji(null), 700)
  }

  const handleArePlus = () => {
    setPop('🔥🔥🔥')
    setAreCount((c) => c + 1)
  }
  const handleAreMinus = () => {
    setPop('💩💩💩')
    setAreCount((c) => Math.max(0, c - 1))
  }
  const handleThumbsPlus = () => {
    setPop('👍👍👍')
    setThumbsCount((c) => c + 1)
  }
  const handleThumbsMinus = () => {
    setPop('👎👎👎')
    setThumbsCount((c) => Math.max(0, c - 1))
  }

  const handleReset = () => {
    setAreCount(0)
    setThumbsCount(0)
  }

  const handleLogin = (e) => {
    e.preventDefault()
    const form = e.target
    const un = form.username?.value
    const pw = form.password?.value
    if (un === ADMIN_USERNAME && pw === ADMIN_PASSWORD) {
      setIsAdmin(true)
      setShowLogin(false)
    } else {
      showMsg('Invalid username or password', 'error')
    }
  }

  const handleSave = async () => {
    if (areCount === 0 && thumbsCount === 0) {
      showMsg('Counts are both zero. Did you mean to save?', 'warning')
      return
    }

    setLoading(true)
    try {
      if (isAdmin || !hasSupabase()) {
        await saveDailyCounts(selectedDate, areCount, thumbsCount)
        showMsg('Date saved to history (existing entry, if any, was updated).')
        setAreCount(0)
        setThumbsCount(0)
        refreshHistory()
      } else {
        const ok = await submitSaveRequest(selectedDate, areCount, thumbsCount)
        if (ok) {
          showMsg('Submitted for approval. The admin will review your counts.')
          setAreCount(0)
          setThumbsCount(0)
          refreshPending()
        } else {
          showMsg('Could not submit. Database may not be configured.', 'error')
        }
      }
    } catch (err) {
      showMsg(err?.message || 'Save failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id) => {
    try {
      await approveRequest(id)
      refreshHistory()
      refreshPending()
    } catch (err) {
      showMsg(err?.message || 'Approve failed', 'error')
    }
  }

  const handleReject = async (id) => {
    try {
      await rejectRequest(id)
      refreshPending()
    } catch (err) {
      showMsg(err?.message || 'Reject failed', 'error')
    }
  }

  const lineChartData =
    history.length > 0
      ? history
          .sort((a, b) => (a.date < b.date ? -1 : 1))
          .map((r) => ({
            date: r.date,
            'Are you with me': r.are_you_with_me,
            'Thumbs up': r.thumbs_up,
          }))
      : []

  const totals =
    history.length > 0
      ? [
          {
            name: 'Are you with me',
            counter: 'are_you_with_me',
            value: history.reduce((s, r) => s + (r.are_you_with_me || 0), 0),
          },
          {
            name: 'Thumbs up',
            counter: 'thumbs_up',
            value: history.reduce((s, r) => s + (r.thumbs_up || 0), 0),
          },
        ].filter((t) => t.value > 0)
      : []

  const viewOptions =
    isAdmin && hasSupabase()
      ? ['Requests', 'Line chart', 'Bar chart', 'Pie chart', 'Stats table', 'Raw data']
      : ['Line chart', 'Bar chart', 'Pie chart', 'Stats table', 'Raw data']

  return (
    <div className="app">
      {popEmoji && (
        <div className="pop-emoji-overlay">
          <span className="pop-emoji">{popEmoji}</span>
        </div>
      )}

      {/* Header */}
      <header className="header">
        <div className="header-left">
          <h1>CC6 TRACKER</h1>
          <p>
            Track how many times the guy says <code>`ARE YOU WITH ME?`</code> and{' '}
            <code>`THUMBS UP`</code> during class.
          </p>
        </div>
        <div className="header-right">
          {isAdmin ? (
            <>
              <button className="btn btn-secondary btn-sm" onClick={() => setIsAdmin(false)}>
                Admin (logout)
              </button>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Logged in as admin
              </span>
            </>
          ) : (
            <>
              <button
                className="btn btn-login btn-sm"
                onClick={() => setShowLogin(!showLogin)}
              >
                Admin login
              </button>
              {showLogin && (
                <form className="admin-form" onSubmit={handleLogin}>
                  <input
                    type="text"
                    name="username"
                    placeholder="Username"
                    autoComplete="username"
                  />
                  <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    autoComplete="current-password"
                  />
                  <div className="admin-form-buttons">
                    <button type="submit" className="btn btn-primary btn-sm">
                      Log in
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setShowLogin(false)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </>
          )}
        </div>
      </header>

      {message && (
        <div className={`message message-${messageType}`}>{message}</div>
      )}

      {/* Live Counter */}
      <section className="section">
        <h2>Live Counter (this class / this date)</h2>
        <div className="counter-grid">
          <div className="counter-col">
            <h3>ARE YOU WITH ME?</h3>
            <button className="btn counter-buttons" onClick={handleArePlus}>
              WITH YOU 🔥🔥🔥
            </button>
            <div className="counter-number">{areCount}</div>
            <button className="btn counter-buttons" onClick={handleAreMinus}>
              NOT WITH YOU 💩💩💩
            </button>
          </div>
          <div className="counter-col">
            <h3>THUMBS UP</h3>
            <button className="btn counter-buttons" onClick={handleThumbsPlus}>
              THUMBS UP 👍👍👍
            </button>
            <div className="counter-number">{thumbsCount}</div>
            <button className="btn counter-buttons" onClick={handleThumbsMinus}>
              THUMBS DOWN 👎👎👎
            </button>
          </div>
          <div className="counter-col">
            <h3>Controls</h3>
            <button className="btn btn-danger counter-buttons" onClick={handleReset}>
              Reset current counts
            </button>
          </div>
        </div>
      </section>

      <div className="divider" />

      {/* Save section */}
      <section className="section">
        <h2>Save this class / date totals</h2>
        <div className="save-row">
          <label>
            Class date:{' '}
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
          </label>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={loading}
          >
            Save this date to history
          </button>
        </div>
      </section>

      <div className="divider" />

      {/* Statistics */}
      <section className="section">
        <h2>Statistics over time</h2>
        <button
          className="btn btn-secondary stats-toggle"
          onClick={() => setShowStats(!showStats)}
        >
          {showStats ? 'Hide' : 'Show'} statistics
        </button>

        {showStats ? (
          <>
            <div className="stats-views">
              {viewOptions.map((opt) => (
                <label key={opt}>
                  <input
                    type="radio"
                    name="statsView"
                    checked={statsView === opt}
                    onChange={() => setStatsView(opt)}
                  />
                  {opt}
                </label>
              ))}
            </div>

            {statsView === 'Requests' && (
              <div>
                <h3>Pending save requests (approve or reject)</h3>
                {pendingRequests.length === 0 ? (
                  <div className="message message-info">No pending requests.</div>
                ) : (
                  pendingRequests.map((r) => (
                    <div key={r.id} className="request-item">
                      <div className="request-info">
                        <strong>
                          Date: {r.class_date} — Are you with me: {r.are_you_with_me}, Thumbs
                          up: {r.thumbs_up}
                        </strong>
                        {r.created_at && (
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            Submitted {r.created_at.slice(0, 19).replace('T', ' ')}
                          </div>
                        )}
                      </div>
                      <div className="request-actions">
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleApprove(r.id)}
                        >
                          Approve
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleReject(r.id)}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {statsView !== 'Requests' && history.length === 0 && (
              <div className="message message-info">
                No history yet. Start counting and save a date first.
              </div>
            )}

            {statsView !== 'Requests' && history.length > 0 && (
              <>
                {statsView === 'Raw data' && (
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Are you with me</th>
                          <th>Thumbs up</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history
                          .sort((a, b) => (a.date < b.date ? -1 : 1))
                          .map((r, i) => (
                            <tr key={i}>
                              <td>{r.date}</td>
                              <td>{r.are_you_with_me}</td>
                              <td>{r.thumbs_up}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {statsView === 'Stats table' && (
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th></th>
                          <th>are_you_with_me</th>
                          <th>thumbs_up</th>
                        </tr>
                      </thead>
                      <tbody>
                        {['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max'].map(
                          (stat) => {
                            const a = history.map((r) => r.are_you_with_me)
                            const t = history.map((r) => r.thumbs_up)
                            const v = (arr, s) => {
                              if (s === 'count') return arr.length
                              const n = arr.length
                              const sorted = [...arr].sort((a, b) => a - b)
                              const sum = arr.reduce((x, y) => x + y, 0)
                              const mean = sum / n
                              const variance =
                                arr.reduce((s, x) => s + (x - mean) ** 2, 0) / n
                              const std = Math.sqrt(variance)
                              if (s === 'mean') return mean.toFixed(2)
                              if (s === 'std') return std.toFixed(2)
                              if (s === 'min') return sorted[0]
                              if (s === 'max') return sorted[n - 1]
                              if (s === '25%') return sorted[Math.floor(n * 0.25)]
                              if (s === '50%') return sorted[Math.floor(n * 0.5)]
                              if (s === '75%') return sorted[Math.floor(n * 0.75)]
                              return '-'
                            }
                            return (
                              <tr key={stat}>
                                <td>{stat}</td>
                                <td>{v(a, stat)}</td>
                                <td>{v(t, stat)}</td>
                              </tr>
                            )
                          }
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {statsView === 'Line chart' && (
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={lineChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="date" stroke="var(--text-muted)" />
                        <YAxis stroke="var(--text-muted)" />
                        <Tooltip
                          contentStyle={{
                            background: 'var(--surface)',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)',
                          }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="Are you with me"
                          stroke={COLORS.are_you_with_me}
                          strokeWidth={2}
                          dot={{ fill: COLORS.are_you_with_me }}
                          connectNulls
                        />
                        <Line
                          type="monotone"
                          dataKey="Thumbs up"
                          stroke={COLORS.thumbs_up}
                          strokeWidth={2}
                          dot={{ fill: COLORS.thumbs_up }}
                          connectNulls
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {statsView === 'Bar chart' && (
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={history
                          .sort((a, b) => (a.date < b.date ? -1 : 1))
                          .map((r) => ({
                            date: r.date,
                            'Are you with me': r.are_you_with_me,
                            'Thumbs up': r.thumbs_up,
                          }))}
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis
                          dataKey="date"
                          stroke="var(--text-muted)"
                          angle={-45}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis stroke="var(--text-muted)" />
                        <Tooltip
                          contentStyle={{
                            background: 'var(--surface)',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)',
                          }}
                        />
                        <Legend />
                        <Bar dataKey="Are you with me" fill={COLORS.are_you_with_me} />
                        <Bar dataKey="Thumbs up" fill={COLORS.thumbs_up} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {statsView === 'Pie chart' && totals.length > 0 && (
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={totals}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={120}
                          label={({ name, value }) => `${name}: ${value}`}
                        >
                          {totals.map((_, i) => (
                            <Cell
                              key={i}
                              fill={
                                totals[i].counter === 'are_you_with_me'
                                  ? COLORS.are_you_with_me
                                  : COLORS.thumbs_up
                              }
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            background: 'var(--surface)',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)',
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {statsView === 'Pie chart' && totals.length === 0 && (
                  <div className="message message-info">No data to display in pie chart.</div>
                )}
              </>
            )}
          </>
        ) : (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Press &quot;Show statistics&quot; to see history and charts.
          </p>
        )}
      </section>
    </div>
  )
}

export default App
