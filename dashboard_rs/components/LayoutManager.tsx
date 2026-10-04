import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, Plus, Trash, Table2 } from 'lucide-react'

export default function LayoutManager() {
  const [tables, setTables] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [newTableName, setNewTableName] = useState('')
  const [seats, setSeats] = useState(2)

  const loadData = async () => {
    try {
      const data = await fetchApi('/tables/')
      setTables(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const addTable = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTableName.trim()) return
    await fetchApi('/tables/', {
      method: 'POST',
      body: JSON.stringify({ name: newTableName, seats }),
    })
    setNewTableName('')
    loadData()
  }

  const deleteTable = async (id: number) => {
    if (!confirm('Are you sure?')) return
    await fetchApi(`/tables/${id}/`, { method: 'DELETE' })
    loadData()
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Layout Designer</h1>
      </div>
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <h2 className="text-lg font-semibold mb-4">Add Table</h2>
        <form onSubmit={addTable} className="flex gap-2 mb-6">
          <input
            required
            value={newTableName}
            onChange={e => setNewTableName(e.target.value)}
            placeholder="Table name (e.g. T1)"
            className="flex-1 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm outline-none focus:border-[#94D8AB]"
          />
          <input
            required
            type="number"
            value={seats}
            onChange={e => setSeats(parseInt(e.target.value))}
            placeholder="Seats"
            className="w-24 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm outline-none focus:border-[#94D8AB]"
          />
          <button type="submit" className="bg-[#94D8AB] px-4 py-2 rounded-xl text-sm font-bold text-[#14532D]">Add</button>
        </form>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
          {tables.map(table => (
            <div key={table.id} className="border border-[#D5E6DA] rounded-2xl p-4 flex flex-col items-center relative group bg-[#F0FAF3]">
              <Table2 className="text-[#6b8b76] mb-2" size={32} />
              <div className="font-bold">{table.name}</div>
              <div className="text-xs text-[#64748b]">{table.seats} seats</div>
              <button 
                onClick={() => deleteTable(table.id)}
                className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 p-1 text-red-500 bg-white rounded-full shadow-sm"
              >
                <Trash size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
