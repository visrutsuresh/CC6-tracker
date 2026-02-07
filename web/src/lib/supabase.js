import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const key = import.meta.env.VITE_SUPABASE_ANON_KEY

let client = null
if (url && key) {
  try {
    client = createClient(url, key)
  } catch (e) {
    console.warn('Supabase init failed:', e)
  }
}

export const supabase = client
export const hasSupabase = () => !!client
