import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2 } from 'lucide-react'

export default function CustomersManager() {
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    try {
      const data = await fetchApi('/customers/')
      setCustomers(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Customers</h1>
      </div>
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[#D5E6DA] text-[#64748b]">
              <th className="pb-3 font-semibold">Name</th>
              <th className="pb-3 font-semibold">Phone</th>
              <th className="pb-3 font-semibold">Email</th>
              <th className="pb-3 font-semibold">Points</th>
              <th className="pb-3 font-semibold">Member Since</th>
            </tr>
          </thead>
          <tbody>
            {customers.map(c => (
              <tr key={c.id} className="border-b border-[#F0FAF3] last:border-0">
                <td className="py-3 font-medium">{c.name}</td>
                <td className="py-3">{c.phone || '-'}</td>
                <td className="py-3">{c.email || '-'}</td>
                <td className="py-3 font-bold text-[#2F855A]">{c.points}</td>
                <td className="py-3 text-[#64748b]">{new Date(c.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {customers.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-[#64748b]">No customers found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
