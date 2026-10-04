import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, TrendingUp, DollarSign, ReceiptText, Users } from 'lucide-react'

export default function ReportsManager() {
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchApi('/orders/').then(data => {
      setOrders(data)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  const totalRevenue = orders.reduce((acc, o) => acc + parseFloat(o.total_amount || 0), 0)
  const paidOrders = orders.filter(o => o.status === 'paid')

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Reports & Analytics</h1>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Revenue" value={`৳${totalRevenue.toFixed(2)}`} icon={<DollarSign/>} />
        <StatCard title="Total Orders" value={orders.length.toString()} icon={<ReceiptText/>} />
        <StatCard title="Completed Orders" value={paidOrders.length.toString()} icon={<TrendingUp/>} />
        <StatCard title="Avg Order Value" value={`৳${orders.length ? (totalRevenue/orders.length).toFixed(2) : '0.00'}`} icon={<Users/>} />
      </div>

      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA] mt-4">
        <h2 className="text-lg font-semibold mb-4">Recent Sales Activity</h2>
        <div className="h-64 flex items-end gap-2 mt-8">
          {/* Mock chart bars */}
          {[40, 70, 45, 90, 65, 85, 110].map((h, i) => (
            <div key={i} className="flex-1 bg-[#BDE8CB] rounded-t-md hover:bg-[#94D8AB] transition-colors relative group" style={{ height: `${h}%` }}>
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                Day {i+1}
              </div>
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-4 text-[#64748b] text-sm font-semibold">
          <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon }: { title: string, value: string, icon: React.ReactNode }) {
  return (
    <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA] flex items-center gap-4">
      <div className="w-12 h-12 rounded-xl bg-[#DCF3E3] text-[#2F855A] flex items-center justify-center">
        {icon}
      </div>
      <div>
        <div className="text-[#64748b] text-sm font-semibold">{title}</div>
        <div className="text-2xl font-bold">{value}</div>
      </div>
    </div>
  )
}
