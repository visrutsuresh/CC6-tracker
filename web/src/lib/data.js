import { supabase, hasSupabase } from './supabase'

const DAILY_COUNTS = 'daily_counts'
const SAVE_REQUESTS = 'save_requests'
const LOCAL_STORAGE_KEY = 'cc6_tracker_history'

function normalizeEntry(row) {
  return {
    date: row.class_date || row.date,
    are_you_with_me: Number(row.are_you_with_me) || 0,
    thumbs_up: Number(row.thumbs_up) || 0,
  }
}

export async function loadHistory() {
  if (hasSupabase()) {
    try {
      const { data, error } = await supabase
        .from(DAILY_COUNTS)
        .select('*')
        .order('class_date')

      if (error) throw error
      const rows = data || []
      return rows.map((r) => ({
        date: r.class_date,
        are_you_with_me: r.are_you_with_me ?? 0,
        thumbs_up: r.thumbs_up ?? 0,
      }))
    } catch (e) {
      console.warn('Supabase load failed:', e)
    }
  }

  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed)
      ? parsed.map((r) => ({
          date: r.date || r.class_date,
          are_you_with_me: Number(r.are_you_with_me) || 0,
          thumbs_up: Number(r.thumbs_up) || 0,
        }))
      : []
  } catch {
    return []
  }
}

export async function saveDailyCounts(classDate, areCount, thumbsCount) {
  const row = {
    class_date: classDate,
    are_you_with_me: areCount,
    thumbs_up: thumbsCount,
  }

  if (hasSupabase()) {
    const { error } = await supabase.from(DAILY_COUNTS).upsert(row, {
      onConflict: 'class_date',
    })
    if (error) throw error
    return
  }

  const history = await loadHistory()
  const filtered = history.filter((r) => r.date !== classDate)
  filtered.push({ date: classDate, are_you_with_me: areCount, thumbs_up: thumbsCount })
  filtered.sort((a, b) => (a.date < b.date ? -1 : 1))
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(filtered))
}

export async function submitSaveRequest(classDate, areCount, thumbsCount) {
  if (!hasSupabase()) return false
  const { error } = await supabase.from(SAVE_REQUESTS).insert({
    class_date: classDate,
    are_you_with_me: areCount,
    thumbs_up: thumbsCount,
    status: 'pending',
  })
  if (error) throw error
  return true
}

export async function getPendingRequests() {
  if (!hasSupabase()) return []
  try {
    const { data, error } = await supabase
      .from(SAVE_REQUESTS)
      .select('*')
      .eq('status', 'pending')
      .order('created_at', { ascending: false })

    if (error) throw error
    return data || []
  } catch (e) {
    console.warn('getPendingRequests failed:', e)
    return []
  }
}

export async function approveRequest(requestId) {
  if (!hasSupabase()) return
  const { data: row, error: fetchErr } = await supabase
    .from(SAVE_REQUESTS)
    .select('class_date, are_you_with_me, thumbs_up')
    .eq('id', requestId)
    .single()

  if (fetchErr || !row) return

  await supabase.from(DAILY_COUNTS).upsert(
    {
      class_date: row.class_date,
      are_you_with_me: row.are_you_with_me,
      thumbs_up: row.thumbs_up,
    },
    { onConflict: 'class_date' }
  )

  await supabase.from(SAVE_REQUESTS).update({ status: 'approved' }).eq('id', requestId)
}

export async function rejectRequest(requestId) {
  if (!hasSupabase()) return
  await supabase.from(SAVE_REQUESTS).update({ status: 'rejected' }).eq('id', requestId)
}
