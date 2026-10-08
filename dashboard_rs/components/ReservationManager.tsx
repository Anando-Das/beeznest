import { useEffect, useMemo, useState } from 'react'
import { fetchApi } from '@/lib/api'
import {
  Calendar, CheckCircle, Clock3, History, Loader2, Pencil, Plus, Users, X, XCircle
} from 'lucide-react'

type Role = 'OWNER' | 'MANAGER' | 'WAITER' | 'CASHIER' | 'KITCHEN' | string

type TableOption = {
  id: number
  name: string
  seats: number
  is_active: boolean
  zone?: number | null
  zone_name?: string | null
  operational_status?: string
}

type Reservation = {
  id: number
  customer_name: string
  customer_contact: string | null
  table: number
  table_name: string
  table_seats: number
  zone_name: string | null
  reservation_date: string
  start_time: string
  expected_duration_minutes: number
  end_time: string
  guest_count: number
  notes: string | null
  status: 'RESERVED' | 'CHECKED_IN' | 'COMPLETED' | 'NO_SHOW' | 'CANCELLED'
  created_by_name?: string | null
}

type HistoryItem = {
  id: number
  action: string
  previous_values: Record<string, unknown> | null
  new_values: Record<string, unknown> | null
  performed_by_name: string | null
  reason: string | null
  created_at: string
}

type FormState = {
  customer_name: string
  customer_contact: string
  table: string
  reservation_date: string
  start_time: string
  expected_duration_minutes: number
  guest_count: number
  notes: string
}

const EMPTY_FORM: FormState = {
  customer_name: '',
  customer_contact: '',
  table: '',
  reservation_date: '',
  start_time: '',
  expected_duration_minutes: 120,
  guest_count: 2,
  notes: '',
}

function cn(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

function apiErrorMessage(err: unknown) {
  const e = err as { message?: string; cause?: Record<string, unknown> }
  const cause = e.cause
  if (cause && typeof cause === 'object') {
    if (typeof cause.detail === 'string') return cause.detail
    const parts: string[] = []
    for (const [key, value] of Object.entries(cause)) {
      if (key === 'requires_capacity_confirmation' || key === 'table_capacity') continue
      if (Array.isArray(value)) parts.push(`${key}: ${value.join(' ')}`)
      else if (typeof value === 'string') parts.push(value)
    }
    if (parts.length) return parts.join(' ')
  }
  return e.message || 'Something went wrong.'
}

function needsCapacityConfirm(err: unknown) {
  const cause = (err as { cause?: Record<string, unknown> }).cause
  const flag = cause?.requires_capacity_confirmation
  return Boolean(flag && (flag === true || (Array.isArray(flag) && flag[0])))
}

function statusClass(status: Reservation['status']) {
  if (status === 'RESERVED') return 'bg-blue-100 text-blue-800'
  if (status === 'CHECKED_IN') return 'bg-green-100 text-green-800'
  if (status === 'COMPLETED') return 'bg-slate-100 text-slate-700'
  if (status === 'NO_SHOW') return 'bg-amber-100 text-amber-800'
  return 'bg-red-100 text-red-800'
}

function formatTime(value: string) {
  return value?.slice(0, 5) || value
}

export default function ReservationManager({
  userRole,
  prefillTableId,
  onPrefillConsumed,
}: {
  userRole?: Role
  prefillTableId?: number | null
  onPrefillConsumed?: () => void
}) {
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [tables, setTables] = useState<TableOption[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Reservation | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [capacityPrompt, setCapacityPrompt] = useState(false)
  const [historyFor, setHistoryFor] = useState<Reservation | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [confirmModal, setConfirmModal] = useState<{ title: string; message: string; onConfirm: () => void } | null>(null)

  const [filterDate, setFilterDate] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterTable, setFilterTable] = useState('')
  const [filterSearch, setFilterSearch] = useState('')

  const canWrite = userRole === 'OWNER' || userRole === 'MANAGER' || userRole === 'WAITER'
  const canCorrect = userRole === 'OWNER' || userRole === 'MANAGER'
  const activeTables = useMemo(() => tables.filter((t) => t.is_active), [tables])

  const showError = (err: unknown) => {
    setErrorMsg(apiErrorMessage(err))
    setTimeout(() => setErrorMsg(''), 7000)
  }

  const showSuccess = (msg: string) => {
    setSuccessMsg(msg)
    setTimeout(() => setSuccessMsg(''), 4000)
  }

  const loadData = async () => {
    const params = new URLSearchParams()
    if (filterDate) params.set('reservation_date', filterDate)
    if (filterStatus) params.set('status', filterStatus)
    if (filterTable) params.set('table', filterTable)
    if (filterSearch) params.set('search', filterSearch)
    const query = params.toString() ? `?${params.toString()}` : ''
    try {
      const [resData, tabData] = await Promise.all([
        fetchApi(`/reservations/${query}`),
        fetchApi('/tables/'),
      ])
      setReservations(resData)
      setTables(tabData)
    } catch (err) {
      showError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!prefillTableId || !canWrite) return
    setEditing(null)
    setForm({ ...EMPTY_FORM, table: String(prefillTableId) })
    setCapacityPrompt(false)
    setFormOpen(true)
    onPrefillConsumed?.()
  }, [prefillTableId, canWrite, onPrefillConsumed])

  const openCreate = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setCapacityPrompt(false)
    setFormOpen(true)
  }

  const openEdit = (r: Reservation) => {
    setEditing(r)
    setForm({
      customer_name: r.customer_name,
      customer_contact: r.customer_contact || '',
      table: String(r.table),
      reservation_date: r.reservation_date,
      start_time: formatTime(r.start_time),
      expected_duration_minutes: r.expected_duration_minutes,
      guest_count: r.guest_count,
      notes: r.notes || '',
    })
    setCapacityPrompt(false)
    setFormOpen(true)
  }

  const submitForm = async (confirmOverCapacity = false) => {
    if (saving) return
    setSaving(true)
    setErrorMsg('')
    const body: Record<string, unknown> = {
      customer_name: form.customer_name,
      customer_contact: form.customer_contact,
      table: Number(form.table),
      reservation_date: form.reservation_date,
      start_time: form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time,
      expected_duration_minutes: Number(form.expected_duration_minutes),
      guest_count: Number(form.guest_count),
      notes: form.notes,
    }
    if (confirmOverCapacity) body.confirm_over_capacity = true
    try {
      if (editing) {
        await fetchApi(`/reservations/${editing.id}/`, { method: 'PATCH', body: JSON.stringify(body) })
        showSuccess('Reservation updated.')
      } else {
        await fetchApi('/reservations/', { method: 'POST', body: JSON.stringify(body) })
        showSuccess('Reservation created.')
      }
      setFormOpen(false)
      setCapacityPrompt(false)
      setEditing(null)
      setForm(EMPTY_FORM)
      await loadData()
    } catch (err) {
      if (needsCapacityConfirm(err)) {
        setCapacityPrompt(true)
        setErrorMsg(apiErrorMessage(err))
      } else {
        showError(err)
      }
    } finally {
      setSaving(false)
    }
  }

  const runAction = async (r: Reservation, path: string, success: string) => {
    if (saving) return
    setSaving(true)
    try {
      await fetchApi(`/reservations/${r.id}/${path}/`, { method: 'POST', body: JSON.stringify({}) })
      showSuccess(success)
      setConfirmModal(null)
      await loadData()
    } catch (err) {
      setConfirmModal(null)
      showError(err)
    } finally {
      setSaving(false)
    }
  }

  const openHistory = async (r: Reservation) => {
    setHistoryFor(r)
    setHistoryLoading(true)
    try {
      const data = await fetchApi(`/reservations/${r.id}/history/`)
      setHistory(data)
    } catch (err) {
      showError(err)
      setHistoryFor(null)
    } finally {
      setHistoryLoading(false)
    }
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6 relative">
      {errorMsg && (
        <div className="bg-red-50 text-red-800 p-4 rounded-xl flex items-center justify-between border border-red-200">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg('')}><X size={18} /></button>
        </div>
      )}
      {successMsg && (
        <div className="bg-[#DCF3E3] text-[#14532D] p-4 rounded-xl flex items-center justify-between border border-[#94D8AB]">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg('')}><X size={18} /></button>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold">Reservations</h1>
        {canWrite && (
          <button onClick={openCreate} className="flex min-h-11 items-center gap-2 rounded-xl bg-[#94D8AB] px-4 text-sm font-bold text-[#14532D] hover:bg-[#6BC48C]">
            <Plus size={16} /> New reservation
          </button>
        )}
      </div>

      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA] grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <input type="date" value={filterDate} onChange={(e) => setFilterDate(e.target.value)} className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm" />
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm bg-white">
          <option value="">All statuses</option>
          {['RESERVED', 'CHECKED_IN', 'COMPLETED', 'NO_SHOW', 'CANCELLED'].map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
        <select value={filterTable} onChange={(e) => setFilterTable(e.target.value)} className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm bg-white">
          <option value="">All tables</option>
          {tables.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <input value={filterSearch} onChange={(e) => setFilterSearch(e.target.value)} placeholder="Customer name or contact" className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm" />
        <button onClick={() => { setLoading(true); loadData() }} className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm font-semibold hover:bg-[#F0FAF3]">Apply filters</button>
      </div>

      <div className="bg-white rounded-2xl border border-[#D5E6DA] overflow-x-auto">
        <table className="w-full text-left text-sm min-w-[860px]">
          <thead className="bg-[#F0FAF3] text-[#6b8b76]">
            <tr>
              <th className="p-4 font-semibold">Customer</th>
              <th className="p-4 font-semibold">Table</th>
              <th className="p-4 font-semibold">Date & time</th>
              <th className="p-4 font-semibold">Guests</th>
              <th className="p-4 font-semibold">Status</th>
              <th className="p-4 font-semibold">Created by</th>
              <th className="p-4 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D5E6DA]">
            {reservations.map((r) => (
              <tr key={r.id}>
                <td className="p-4">
                  <div className="font-medium">{r.customer_name}</div>
                  <div className="text-xs text-[#64748b]">{r.customer_contact || '—'}</div>
                </td>
                <td className="p-4">
                  <div>{r.table_name}</div>
                  <div className="text-xs text-[#64748b]">{r.zone_name || 'No zone'} · {r.table_seats} seats</div>
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-1"><Calendar size={14} /> {r.reservation_date}</div>
                  <div className="text-xs text-[#64748b] flex items-center gap-1 mt-1">
                    <Clock3 size={12} /> {formatTime(r.start_time)}–{formatTime(r.end_time)} ({r.expected_duration_minutes} min)
                  </div>
                </td>
                <td className="p-4"><Users size={14} className="inline mr-1 text-gray-400" />{r.guest_count}</td>
                <td className="p-4">
                  <span className={cn('px-2 py-1 rounded-full text-xs font-bold', statusClass(r.status))}>{r.status.replace('_', ' ')}</span>
                </td>
                <td className="p-4 text-[#64748b]">{r.created_by_name || '—'}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button onClick={() => openHistory(r)} className="p-1.5 bg-[#F0FAF3] text-[#2F855A] rounded-lg" title="History"><History size={16} /></button>
                    {canWrite && r.status === 'RESERVED' && (
                      <>
                        <button onClick={() => openEdit(r)} className="p-1.5 bg-white border border-[#D5E6DA] rounded-lg" title="Edit"><Pencil size={16} /></button>
                        <button onClick={() => setConfirmModal({ title: 'Check in guest?', message: `Check in ${r.customer_name} at ${r.table_name}?`, onConfirm: () => runAction(r, 'check-in', 'Guest checked in.') })} className="p-1.5 bg-green-50 text-green-700 rounded-lg" title="Check in"><CheckCircle size={16} /></button>
                        <button onClick={() => setConfirmModal({ title: 'Mark no-show?', message: `Mark ${r.customer_name} as no-show? This keeps the history.`, onConfirm: () => runAction(r, 'no-show', 'Marked as no-show.') })} className="p-1.5 bg-amber-50 text-amber-700 rounded-lg" title="No show"><XCircle size={16} /></button>
                        <button onClick={() => setConfirmModal({ title: 'Cancel reservation?', message: `Cancel ${r.customer_name}'s reservation? The record is kept for history.`, onConfirm: () => runAction(r, 'cancel', 'Reservation cancelled.') })} className="px-2 py-1 bg-red-50 text-red-700 rounded-lg text-xs font-semibold">Cancel</button>
                      </>
                    )}
                    {canWrite && r.status === 'CHECKED_IN' && (
                      <button onClick={() => setConfirmModal({ title: 'Complete reservation?', message: `Mark ${r.customer_name} as completed?`, onConfirm: () => runAction(r, 'complete', 'Reservation completed.') })} className="px-2 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold">Complete</button>
                    )}
                    {canCorrect && (r.status === 'CANCELLED' || r.status === 'NO_SHOW' || r.status === 'COMPLETED') && (
                      <button
                        onClick={() => setConfirmModal({
                          title: 'Correct status to RESERVED?',
                          message: 'This is an auditable correction. The previous history is kept.',
                          onConfirm: async () => {
                            setSaving(true)
                            try {
                              await fetchApi(`/reservations/${r.id}/correct/`, { method: 'POST', body: JSON.stringify({ status: 'RESERVED', reason: 'Operational correction' }) })
                              showSuccess('Status corrected.')
                              setConfirmModal(null)
                              await loadData()
                            } catch (err) {
                              setConfirmModal(null)
                              showError(err)
                            } finally {
                              setSaving(false)
                            }
                          }
                        })}
                        className="px-2 py-1 bg-white border border-[#D5E6DA] rounded-lg text-xs font-semibold"
                      >
                        Correct
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {reservations.length === 0 && (
              <tr><td colSpan={7} className="p-8 text-center text-[#64748b]">No reservations found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {formOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">{editing ? 'Edit reservation' : 'New reservation'}</h2>
            <form onSubmit={(e) => { e.preventDefault(); submitForm(capacityPrompt) }} className="flex flex-col gap-3">
              <label className="text-sm font-semibold">Customer name
                <input required value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
              </label>
              <label className="text-sm font-semibold">Contact
                <input value={form.customer_contact} onChange={(e) => setForm({ ...form, customer_contact: e.target.value })} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
              </label>
              <label className="text-sm font-semibold">Table
                <select required value={form.table} onChange={(e) => { setForm({ ...form, table: e.target.value }); setCapacityPrompt(false) }} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2 bg-white">
                  <option value="">Select table…</option>
                  {activeTables.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} · {t.zone_name || 'No zone'} · {t.seats} seats
                    </option>
                  ))}
                </select>
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="text-sm font-semibold">Date
                  <input required type="date" value={form.reservation_date} onChange={(e) => setForm({ ...form, reservation_date: e.target.value })} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
                </label>
                <label className="text-sm font-semibold">Start time
                  <input required type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
                </label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <label className="text-sm font-semibold">Duration (minutes)
                  <input required type="number" min={1} value={form.expected_duration_minutes} onChange={(e) => setForm({ ...form, expected_duration_minutes: Number(e.target.value) })} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
                </label>
                <label className="text-sm font-semibold">Guest count
                  <input required type="number" min={1} value={form.guest_count} onChange={(e) => { setForm({ ...form, guest_count: Number(e.target.value) }); setCapacityPrompt(false) }} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
                </label>
              </div>
              <label className="text-sm font-semibold">Notes
                <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="mt-1 w-full rounded-xl border border-[#D5E6DA] px-3 py-2" rows={3} />
              </label>
              {capacityPrompt && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                  Guest count exceeds this table’s capacity. Submit again to confirm the over-capacity booking.
                </div>
              )}
              <div className="flex justify-end gap-2 mt-2">
                <button type="button" onClick={() => setFormOpen(false)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Close</button>
                <button type="submit" disabled={saving} className="px-4 py-2 bg-[#94D8AB] text-[#14532D] rounded-xl font-bold disabled:opacity-50">
                  {saving ? 'Saving…' : capacityPrompt ? 'Confirm over capacity' : editing ? 'Save changes' : 'Create reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {historyFor && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">History · {historyFor.customer_name}</h2>
              <button onClick={() => setHistoryFor(null)}><X size={18} /></button>
            </div>
            {historyLoading ? <Loader2 className="animate-spin" /> : (
              <div className="flex flex-col gap-3">
                {history.map((h) => (
                  <div key={h.id} className="rounded-xl border border-[#D5E6DA] p-3 text-sm">
                    <div className="font-semibold">{h.action.replace('_', ' ')}</div>
                    <div className="text-xs text-[#64748b]">{new Date(h.created_at).toLocaleString()} · {h.performed_by_name || 'Unknown'}</div>
                    {h.reason && <div className="mt-1 text-xs">Reason: {h.reason}</div>}
                  </div>
                ))}
                {history.length === 0 && <p className="text-sm text-[#64748b]">No history yet.</p>}
              </div>
            )}
          </div>
        </div>
      )}

      {confirmModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm text-center">
            <h2 className="text-xl font-bold mb-2">{confirmModal.title}</h2>
            <p className="text-sm text-gray-600 mb-6">{confirmModal.message}</p>
            <div className="flex justify-center gap-3">
              <button onClick={() => setConfirmModal(null)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Back</button>
              <button disabled={saving} onClick={confirmModal.onConfirm} className="px-4 py-2 bg-[#14532D] text-white rounded-xl font-bold disabled:opacity-50">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
