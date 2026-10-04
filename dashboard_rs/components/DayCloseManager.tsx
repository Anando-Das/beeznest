import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, Plus, Trash } from 'lucide-react'

export default function DayCloseManager() {
  const [closes, setCloses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    try {
      const data = await fetchApi('/day-close/')
      setCloses(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const doDayClose = async () => {
    if (!confirm('Are you sure you want to run day close?')) return
    await fetchApi('/day-close/', {
      method: 'POST',
      body: JSON.stringify({
        total_sales: 24500, // mock calculation
        total_expenses: 1200, // mock calculation
        cash_in_drawer: 23000,
        expected_cash: 23300
      }),
    })
    loadData()
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Day Close</h1>
        <button onClick={doDayClose} className="bg-[#14532D] text-white px-4 py-2 rounded-xl text-sm font-bold">
          Run Day Close
        </button>
      </div>
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[#D5E6DA] text-[#64748b]">
              <th className="pb-3 font-semibold">Date</th>
              <th className="pb-3 font-semibold">Total Sales</th>
              <th className="pb-3 font-semibold">Total Expenses</th>
              <th className="pb-3 font-semibold">Cash in Drawer</th>
              <th className="pb-3 font-semibold">Expected Cash</th>
            </tr>
          </thead>
          <tbody>
            {closes.map(c => (
              <tr key={c.id} className="border-b border-[#F0FAF3] last:border-0">
                <td className="py-3 font-medium">{c.date}</td>
                <td className="py-3 text-[#2F855A] font-semibold">৳{c.total_sales}</td>
                <td className="py-3 text-[#92400E] font-semibold">৳{c.total_expenses}</td>
                <td className="py-3">৳{c.cash_in_drawer}</td>
                <td className="py-3">৳{c.expected_cash}</td>
              </tr>
            ))}
            {closes.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-[#64748b]">No day close records found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
