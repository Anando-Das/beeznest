import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Table2, X, Search, Coffee, Loader2 } from 'lucide-react'

function cn(...classes: (string | false | undefined)[]) { return classes.filter(Boolean).join(' ') }

export default function SalesManager() {
  const [tables, setTables] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTable, setSelectedTable] = useState<any>(null)
  const [orderOpen, setOrderOpen] = useState(false)
  const [orderItems, setOrderItems] = useState<any[]>([])

  const loadData = async () => {
    try {
      const [tData, cData] = await Promise.all([
        fetchApi('/tables/'),
        fetchApi('/categories/')
      ])
      setTables(tData)
      setCategories(cData)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleTableClick = (table: any) => {
    setSelectedTable(table)
    setOrderItems([]) // Reset order items for new table selection
    setOrderOpen(true)
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Daily sales</h1>
          <p className="text-sm text-[#64748b]">Tap a table to start an order.</p>
        </div>
        <div className="flex gap-2">
          <button className="min-h-11 rounded-xl border border-[#94D8AB] px-3 text-sm font-semibold">Takeaway</button>
          <button className="min-h-11 rounded-xl bg-[#94D8AB] px-4 text-sm font-bold">+ New order</button>
        </div>
      </div>
      
      <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
        <section className="rounded-2xl border border-[#D5E6DA] bg-white p-4 sm:p-6">
          <h2 className="text-lg font-semibold mb-5">Tables</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {tables.map((table) => (
              <button 
                key={table.id} 
                onClick={() => handleTableClick(table)} 
                className={cn(
                  'min-h-28 rounded-2xl border-2 p-3 text-left transition-transform hover:-translate-y-0.5',
                  table.status==='free'&&'border-[#94D8AB] bg-[#F0FAF3]',
                  table.status==='occupied'&&'border-[#F8C9C4] bg-[#fff8f7]',
                  table.status==='reserved'&&'border-[#CFE0F7] bg-[#f8fbff]'
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold">{table.name}</span>
                  <Table2 size={17} className="text-[#64748b]"/>
                </div>
                <div className="mt-3 text-xs text-[#64748b]">{table.seats} seats</div>
                <div className="mt-1 text-[10px] font-bold uppercase tracking-wide text-[#64748b]">{table.status}</div>
              </button>
            ))}
          </div>
        </section>
        
        <OrderPanel 
          table={selectedTable} 
          open={orderOpen} 
          setOpen={setOrderOpen} 
          categories={categories}
          orderItems={orderItems}
          setOrderItems={setOrderItems}
          onOrderComplete={loadData}
        />
      </div>
    </div>
  )
}

function OrderPanel({ table, open, setOpen, categories, orderItems, setOrderItems, onOrderComplete }: any) {
  const [submitting, setSubmitting] = useState(false)
  
  if (!open || !table) return <section className="rounded-2xl border border-[#D5E6DA] bg-white p-5 xl:sticky xl:top-24 hidden xl:block"><div className="text-center text-sm text-[#64748b] mt-10">Select a table to start an order</div></section>

  const addItem = (item: any) => {
    const existing = orderItems.find((i: any) => i.id === item.id)
    if (existing) {
      setOrderItems(orderItems.map((i: any) => i.id === item.id ? { ...i, qty: i.qty + 1 } : i))
    } else {
      setOrderItems([...orderItems, { ...item, qty: 1 }])
    }
  }

  const subtotal = orderItems.reduce((acc: number, i: any) => acc + (parseFloat(i.price) * i.qty), 0)

  const sendToKitchen = async () => {
    if (orderItems.length === 0) return
    setSubmitting(true)
    try {
      const order = await fetchApi('/orders/', {
        method: 'POST',
        body: JSON.stringify({
          table: table.id,
          order_type: 'dine-in',
          status: 'open',
          total_amount: subtotal
        })
      })
      
      for (const item of orderItems) {
        await fetchApi('/order-items/', {
          method: 'POST',
          body: JSON.stringify({
            order: order.id,
            menu_item: item.id,
            quantity: item.qty,
            price_at_time: item.price
          })
        })
      }
      
      setOpen(false)
      onOrderComplete()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="rounded-2xl border border-[#D5E6DA] bg-white p-5 xl:sticky xl:top-24 xl:h-fit">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">{table.name} · New Order</h2>
          <p className="text-xs text-[#64748b]">{table.seats} seats · Dine-in</p>
        </div>
        <button className="rounded-lg p-2 hover:bg-[#F0FAF3] xl:hidden" onClick={() => setOpen(false)}>
          <X size={18}/>
        </button>
      </div>
      
      <div className="mb-4 grid gap-2 max-h-40 overflow-y-auto">
        {categories.map((cat: any) => (
          <div key={cat.id}>
            <div className="text-xs font-bold text-[#6b8b76] mb-2">{cat.name}</div>
            <div className="grid grid-cols-2 gap-2">
              {cat.items?.map((item: any) => (
                <button 
                  key={item.id} 
                  onClick={() => addItem(item)}
                  className="min-h-16 rounded-xl border border-[#D5E6DA] p-2 text-left hover:border-[#6BC48C]"
                >
                  <div className="truncate text-xs font-semibold">{item.name}</div>
                  <div className="text-xs text-[#64748b]">৳{item.price}</div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      <div className="my-5 border-t border-[#D5E6DA] pt-4 min-h-[100px]">
        {orderItems.map((item: any) => (
          <div key={item.id} className="flex items-center justify-between text-sm mb-2">
            <span>{item.name} ×{item.qty}</span>
            <b>৳{parseFloat(item.price) * item.qty}</b>
          </div>
        ))}
        {orderItems.length === 0 && <div className="text-sm text-[#64748b] text-center">No items added</div>}
        
        <div className="mt-4 flex items-center justify-between border-t border-[#D5E6DA] pt-4 text-lg font-bold">
          <span>Total</span>
          <span>৳{subtotal}</span>
        </div>
      </div>
      
      <div className="flex flex-col gap-2">
        <button 
          onClick={sendToKitchen}
          disabled={submitting || orderItems.length === 0}
          className="min-h-12 w-full rounded-xl bg-[#94D8AB] text-sm font-bold text-[#14532D] disabled:opacity-50"
        >
          {submitting ? <Loader2 className="animate-spin mx-auto" /> : 'Send to kitchen'}
        </button>
      </div>
    </section>
  )
}
