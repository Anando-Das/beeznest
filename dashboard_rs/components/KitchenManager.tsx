import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2 } from 'lucide-react'

export default function KitchenManager() {
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    try {
      const data = await fetchApi('/orders/')
      // Only show active orders for kitchen
      setOrders(data.filter((o: any) => ['open', 'preparing'].includes(o.status)))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000) // Auto refresh
    return () => clearInterval(interval)
  }, [])

  const updateStatus = async (id: number, status: string) => {
    await fetchApi(`/orders/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    })
    loadData()
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Kitchen Display</h1>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA] min-h-[50vh]">
          <h2 className="text-lg font-semibold mb-4 flex justify-between">
            <span>New Tickets</span>
            <span className="bg-[#BDE8CB] px-2 rounded-full text-sm">{orders.filter(o => o.status === 'open').length}</span>
          </h2>
          <div className="flex flex-col gap-4">
            {orders.filter(o => o.status === 'open').map(order => (
              <Ticket key={order.id} order={order} onAction={() => updateStatus(order.id, 'preparing')} actionText="Start Preparing" actionColor="bg-[#FBE3B5] text-[#92400E]" />
            ))}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA] min-h-[50vh]">
          <h2 className="text-lg font-semibold mb-4 flex justify-between">
            <span>Preparing</span>
            <span className="bg-[#FBE3B5] px-2 rounded-full text-sm">{orders.filter(o => o.status === 'preparing').length}</span>
          </h2>
          <div className="flex flex-col gap-4">
            {orders.filter(o => o.status === 'preparing').map(order => (
              <Ticket key={order.id} order={order} onAction={() => updateStatus(order.id, 'served')} actionText="Mark Ready" actionColor="bg-[#94D8AB] text-[#14532D]" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Ticket({ order, onAction, actionText, actionColor }: { order: any, onAction: () => void, actionText: string, actionColor: string }) {
  return (
    <div className="border border-[#D5E6DA] rounded-xl p-4 shadow-sm bg-[#fbfefc]">
      <div className="flex justify-between font-bold text-lg mb-2 border-b border-[#D5E6DA] pb-2">
        <span>Order #{order.id}</span>
        <span>{order.table_name ? `T${order.table_name}` : order.order_type}</span>
      </div>
      <div className="py-2 text-sm flex flex-col gap-1">
        {order.items?.map((item: any, i: number) => (
          <div key={i} className="flex justify-between font-medium">
            <span>{item.quantity}x {item.menu_item_name}</span>
            {item.notes && <span className="text-xs text-red-500">{item.notes}</span>}
          </div>
        ))}
      </div>
      <div className="mt-4 pt-3 border-t border-[#D5E6DA]">
        <button onClick={onAction} className={`w-full py-2 rounded-lg font-bold text-sm ${actionColor}`}>
          {actionText}
        </button>
      </div>
    </div>
  )
}
