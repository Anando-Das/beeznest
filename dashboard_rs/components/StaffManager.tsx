import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, Users, Plus, Link as LinkIcon, X } from 'lucide-react'

export default function StaffManager({ userRole }: { userRole?: string }) {
  const [staff, setStaff] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  const [showAdd, setShowAdd] = useState(false)
  const [showAssign, setShowAssign] = useState(false)
  const [editStaff, setEditStaff] = useState<any>(null)
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const loadData = async () => {
    try {
      const data = await fetchApi('/staff/')
      setStaff(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Staff Management</h1>
        <div className="flex gap-2">
          <button onClick={() => setShowAssign(true)} className="flex items-center gap-2 rounded-xl bg-white border border-[#D5E6DA] px-4 py-2 text-sm font-semibold hover:bg-[#F0FAF3]">
            <LinkIcon size={16} /> Assign Existing
          </button>
          <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 rounded-xl bg-[#94D8AB] px-4 py-2 text-sm font-bold text-[#14532D] hover:bg-[#6BC48C]">
            <Plus size={16} /> New Staff
          </button>
        </div>
      </div>
      
      {error && <div className="rounded-xl border border-[#F8C9C4] bg-[#fff8f7] p-3 text-sm text-[#92400E]">{error}</div>}

      <div className="rounded-2xl border border-[#D5E6DA] bg-white p-5">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {staff.map(s => (
            <div key={s.id} className="flex items-center gap-4 rounded-xl border border-[#D5E6DA] bg-[#fbfefc] p-4">
              <div className="flex size-12 items-center justify-center rounded-full bg-[#DCF3E3] text-[#2F855A]">
                <Users size={20} />
              </div>
              <div>
                <div className="font-bold">{s.first_name} {s.last_name || s.username}</div>
                <div className="text-sm text-[#64748b]">@{s.username}</div>
                <div className="mt-1 inline-block rounded-full bg-[#94D8AB] px-2 text-xs font-semibold text-[#14532D]">
                  {s.role || 'No Role'}
                </div>
                {!s.is_active && <div className="mt-1 ml-2 inline-block rounded-full bg-[#F8C9C4] px-2 text-xs font-semibold text-[#92400E]">Inactive</div>}
              </div>
              <div className="ml-auto flex flex-col items-end gap-2">
                <button 
                  onClick={() => setEditStaff(s)}
                  className="text-xs font-bold text-[#2F855A] hover:underline"
                >
                  Edit Role
                </button>
                <button 
                  disabled={togglingId === s.id}
                  onClick={async () => {
                    setTogglingId(s.id)
                    setError('')
                    try {
                      await fetchApi(`/staff/${s.id}/`, { method: 'PATCH', body: JSON.stringify({ is_active: !s.is_active }) })
                      await loadData()
                    } catch (err: any) {
                      setError(err.message || 'Failed to update status')
                    } finally {
                      setTogglingId(null)
                    }
                  }}
                  className="text-[10px] font-bold text-[#64748b] underline disabled:opacity-50"
                >
                  {togglingId === s.id ? 'Updating...' : (s.is_active ? 'Deactivate' : 'Activate')}
                </button>
              </div>
            </div>
          ))}
          {staff.length === 0 && (
            <div className="col-span-full py-8 text-center text-[#64748b]">No staff found</div>
          )}
        </div>
      </div>

      {showAdd && <AddStaffModal userRole={userRole} onClose={() => setShowAdd(false)} onReload={loadData} />}
      {showAssign && <AssignStaffModal userRole={userRole} onClose={() => setShowAssign(false)} onReload={loadData} />}
      {editStaff && <EditStaffModal userRole={userRole} staff={editStaff} onClose={() => setEditStaff(null)} onReload={loadData} />}
    </div>
  )
}

function AddStaffModal({ userRole, onClose, onReload }: { userRole?: string, onClose: () => void, onReload: () => void }) {
  const [formData, setFormData] = useState({ username: '', password: '', first_name: '', last_name: '', role: 'WAITER' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await fetchApi('/staff/', { method: 'POST', body: JSON.stringify(formData) })
      onReload()
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to create staff')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#14532D]/20 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Create New Staff</h2>
          <button onClick={onClose}><X size={20} /></button>
        </div>
        {error && <div className="mb-4 rounded border border-[#F8C9C4] bg-[#fff8f7] p-2 text-sm text-[#92400E]">{error}</div>}
        <form onSubmit={submit} className="flex flex-col gap-4">
          <input required placeholder="Username" className="rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
          <input required type="password" placeholder="Password" className="rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
          <div className="flex gap-2">
            <input required placeholder="First Name" className="w-full rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} />
            <input placeholder="Last Name" className="w-full rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} />
          </div>
          <select className="rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
            {userRole === 'OWNER' && <option value="OWNER">Owner</option>}
            <option value="MANAGER">Manager</option>
            <option value="CASHIER">Cashier</option>
            <option value="WAITER">Waiter</option>
            <option value="KITCHEN">Kitchen</option>
          </select>
          <button disabled={saving} className="mt-2 rounded-xl bg-[#14532D] p-3 font-bold text-white disabled:opacity-70">
            {saving ? 'Creating...' : 'Create Staff'}
          </button>
        </form>
      </div>
    </div>
  )
}

function AssignStaffModal({ userRole, onClose, onReload }: { userRole?: string, onClose: () => void, onReload: () => void }) {
  const [formData, setFormData] = useState({ username: '', role: 'WAITER' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await fetchApi('/staff/assign_existing/', { method: 'POST', body: JSON.stringify(formData) })
      onReload()
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to assign user. Make sure username is correct and unassigned.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#14532D]/20 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Assign Existing User</h2>
          <button onClick={onClose}><X size={20} /></button>
        </div>
        <p className="mb-4 text-sm text-[#64748b]">Enter the exact username of a registered but unassigned user to link them to your restaurant.</p>
        {error && <div className="mb-4 rounded border border-[#F8C9C4] bg-[#fff8f7] p-2 text-sm text-[#92400E]">{error}</div>}
        <form onSubmit={submit} className="flex flex-col gap-4">
          <input required placeholder="Username" className="rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
          <select className="rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
            {userRole === 'OWNER' && <option value="OWNER">Owner</option>}
            <option value="MANAGER">Manager</option>
            <option value="CASHIER">Cashier</option>
            <option value="WAITER">Waiter</option>
            <option value="KITCHEN">Kitchen</option>
          </select>
          <button disabled={saving} className="mt-2 rounded-xl bg-[#14532D] p-3 font-bold text-white disabled:opacity-70">
            {saving ? 'Assigning...' : 'Assign User'}
          </button>
        </form>
      </div>
    </div>
  )
}

function EditStaffModal({ userRole, staff, onClose, onReload }: { userRole?: string, staff: any, onClose: () => void, onReload: () => void }) {
  const [role, setRole] = useState(staff.role)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await fetchApi(`/staff/${staff.id}/`, { method: 'PATCH', body: JSON.stringify({ role }) })
      onReload()
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to update role.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#14532D]/20 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Edit Role</h2>
          <button onClick={onClose}><X size={20} /></button>
        </div>
        <p className="mb-4 text-sm text-[#64748b]">Change role for @{staff.username}.</p>
        {error && <div className="mb-4 rounded border border-[#F8C9C4] bg-[#fff8f7] p-2 text-sm text-[#92400E]">{error}</div>}
        <form onSubmit={submit} className="flex flex-col gap-4">
          <select className="rounded-xl border border-[#D5E6DA] p-2.5 outline-none focus:border-[#94D8AB]" value={role} onChange={e => setRole(e.target.value)}>
            {userRole === 'OWNER' && <option value="OWNER">Owner</option>}
            <option value="MANAGER">Manager</option>
            <option value="CASHIER">Cashier</option>
            <option value="WAITER">Waiter</option>
            <option value="KITCHEN">Kitchen</option>
          </select>
          <button disabled={saving} className="mt-2 rounded-xl bg-[#14532D] p-3 font-bold text-white disabled:opacity-70">
            {saving ? 'Saving...' : 'Save Role'}
          </button>
        </form>
      </div>
    </div>
  )
}
