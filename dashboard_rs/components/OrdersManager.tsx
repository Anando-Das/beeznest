import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2 } from 'lucide-react'

export default function OrdersManager() {
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchApi('/orders/').then(data => {
      setOrders(data)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Orders</h1>
      </div>
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[#D5E6DA] text-[#64748b]">
              <th className="pb-3 font-semibold">Order ID</th>
              <th className="pb-3 font-semibold">Table/Type</th>
              <th className="pb-3 font-semibold">Amount</th>
              <th className="pb-3 font-semibold">Status</th>
              <th className="pb-3 font-semibold">Date</th>
            </tr>
          </thead>
          <tbody>
            {orders.map(order => (
              <tr key={order.id} className="border-b border-[#F0FAF3] last:border-0">
                <td className="py-3 font-medium">#{order.id}</td>
                <td className="py-3">{order.table_name ? `Table ${order.table_name}` : order.order_type}</td>
                <td className="py-3">৳{order.total_amount}</td>
                <td className="py-3">
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold ${
                    order.status === 'paid' ? 'bg-[#DCF3E3] text-[#2F855A]' : 
                    order.status === 'open' ? 'bg-[#FBE3B5] text-[#92400E]' : 
                    'bg-[#CFE0F7] text-[#1E40AF]'
                  }`}>
                    {order.status}
                  </span>
                </td>
                <td className="py-3 text-[#64748b]">{new Date(order.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-[#64748b]">No orders found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
