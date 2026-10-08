import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, X, Edit, Trash2, CreditCard, Receipt as ReceiptIcon, Printer } from 'lucide-react'

export default function OrdersManager() {
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editingOrder, setEditingOrder] = useState<any>(null)
  const [editItems, setEditItems] = useState<any[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [checkoutOrder, setCheckoutOrder] = useState<any>(null)
  const [paymentMethod, setPaymentMethod] = useState('cash')
  
  const [receiptOrder, setReceiptOrder] = useState<any>(null)

  useEffect(() => {
    loadOrders()
  }, [])

  const loadOrders = async () => {
    try {
      const data = await fetchApi('/orders/')
      setOrders(data)
      setError(null)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async (orderId: number) => {
    if (!confirm('Are you sure you want to cancel this order?')) return
    
    try {
      await fetchApi(`/orders/${orderId}/cancel/`, { method: 'POST' })
      loadOrders()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleEdit = (order: any) => {
    setEditingOrder(order)
    setEditItems(order.items.map((item: any) => ({
      id: item.menu_item,
      name: item.menu_item_name,
      price: item.price_at_time,
      qty: item.quantity,
      notes: item.notes
    })))
    setError(null)
  }

  const handleSaveEdit = async () => {
    if (editItems.length === 0) {
      setError('Order must have at least one item')
      return
    }
    
    setSubmitting(true)
    try {
      await fetchApi(`/orders/${editingOrder.id}/update_with_items/`, {
        method: 'PATCH',
        body: JSON.stringify({
          items: editItems.map((item: any) => ({
            menu_item: item.id,
            quantity: item.qty,
            notes: item.notes
          }))
        })
      })
      setEditingOrder(null)
      setEditItems([])
      loadOrders()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const updateItemQty = (itemId: number, delta: number) => {
    setEditItems(editItems.map((item: any) => 
      item.id === itemId ? { ...item, qty: Math.max(1, item.qty + delta) } : item
    ))
  }

  const removeItem = (itemId: number) => {
    setEditItems(editItems.filter((item: any) => item.id !== itemId))
  }

  const handleProcessPayment = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await fetchApi(`/orders/${checkoutOrder.id}/pay/`, {
        method: 'POST',
        body: JSON.stringify({ method: paymentMethod })
      })
      const updatedOrder = { ...checkoutOrder, status: 'paid', payment: { amount: checkoutOrder.total_amount, method: paymentMethod, timestamp: new Date().toISOString() }, restaurant_name: checkoutOrder.restaurant_name, customer_phone: checkoutOrder.customer_phone }
      setCheckoutOrder(null)
      setReceiptOrder(updatedOrder)
      loadOrders()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const printReceipt = () => {
    window.print()
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  if (receiptOrder) {
    return (
      <div className="flex flex-col gap-6 w-full max-w-md mx-auto print:max-w-full print:m-0 print:p-0">
        <div className="bg-white p-8 rounded-2xl border border-[#D5E6DA] print:border-none print:shadow-none print:p-4">
          <div className="text-center mb-6 border-b border-dashed border-gray-300 pb-6">
            <h1 className="text-2xl font-bold uppercase tracking-widest">{receiptOrder.restaurant_name}</h1>
            <p className="text-sm text-gray-500 mt-1">Receipt for Order #{receiptOrder.id}</p>
            {receiptOrder.customer_phone && (
              <p className="text-sm text-gray-500 mt-1">Customer: {receiptOrder.customer_phone}</p>
            )}
            <p className="text-sm text-gray-500 mt-1">{new Date(receiptOrder.payment?.timestamp || receiptOrder.created_at).toLocaleString()}</p>
          </div>
          
          <div className="mb-6 flex flex-col gap-3">
            {receiptOrder.items.map((item: any, i: number) => (
              <div key={i} className="flex justify-between text-sm">
                <span>{item.quantity}x {item.menu_item_name}</span>
                <span className="font-medium">৳{parseFloat(item.price_at_time) * item.quantity}</span>
              </div>
            ))}
          </div>
          
          <div className="border-t border-dashed border-gray-300 pt-4 mb-6">
            <div className="flex justify-between text-lg font-bold">
              <span>Total</span>
              <span>৳{receiptOrder.total_amount}</span>
            </div>
            {receiptOrder.payment && (
              <div className="flex justify-between text-sm text-gray-500 mt-2">
                <span className="capitalize">Paid via {receiptOrder.payment.method}</span>
                <span>{new Date(receiptOrder.payment.timestamp).toLocaleTimeString()}</span>
              </div>
            )}
            <div className="flex justify-between text-sm font-bold text-[#2F855A] mt-1">
              <span>Status</span>
              <span className="uppercase">{receiptOrder.status}</span>
            </div>
          </div>
          
          <div className="text-center text-sm text-gray-500 italic print:block">
            Thank you for dining with us!
          </div>
        </div>
        
        <div className="flex gap-4 print:hidden">
          <button 
            onClick={() => setReceiptOrder(null)}
            className="flex-1 py-3 rounded-xl border border-gray-300 font-semibold"
          >
            Back to Orders
          </button>
          <button 
            onClick={printReceipt}
            className="flex-1 py-3 rounded-xl bg-[#94D8AB] text-[#14532D] font-semibold flex justify-center items-center gap-2"
          >
            <Printer size={18} /> Print Receipt
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 print:hidden">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Orders</h1>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 font-bold">✕</button>
          </div>
        )}
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
              <th className="pb-3 font-semibold">Actions</th>
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
                    order.status === 'cancelled' ? 'bg-gray-100 text-gray-600' :
                    'bg-[#CFE0F7] text-[#1E40AF]'
                  }`}>
                    {order.status}
                  </span>
                </td>
                <td className="py-3 text-[#64748b]">{new Date(order.created_at).toLocaleString()}</td>
                <td className="py-3">
                  <div className="flex gap-2">
                    {order.status !== 'paid' && order.status !== 'cancelled' && (
                      <>
                        <button 
                          onClick={() => handleEdit(order)}
                          className="p-1.5 hover:bg-gray-100 rounded text-[#64748b]"
                          title="Edit order"
                        >
                          <Edit size={14} />
                        </button>
                        <button 
                          onClick={() => handleCancel(order.id)}
                          className="p-1.5 hover:bg-red-50 rounded text-red-500"
                          title="Cancel order"
                        >
                          <Trash2 size={14} />
                        </button>
                        <button 
                          onClick={() => setCheckoutOrder(order)}
                          className="px-3 py-1 bg-[#94D8AB] hover:bg-[#86CB9D] text-[#14532D] text-xs font-bold rounded flex items-center gap-1 ml-1"
                          title="Checkout/Pay"
                        >
                          <CreditCard size={14} /> Pay
                        </button>
                      </>
                    )}
                    {order.status === 'paid' && (
                      <button 
                        onClick={() => setReceiptOrder(order)}
                        className="p-1.5 hover:bg-[#D5E6DA] rounded text-[#14532D]"
                        title="View Receipt"
                      >
                        <ReceiptIcon size={14} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-[#64748b]">No orders found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editingOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Edit Order #{editingOrder.id}</h2>
              <button onClick={() => setEditingOrder(null)} className="p-1 hover:bg-gray-100 rounded">
                <X size={18} />
              </button>
            </div>
            
            <div className="max-h-60 overflow-y-auto mb-4">
              {editItems.map((item: any) => (
                <div key={item.id} className="flex items-center justify-between py-2 border-b border-gray-100">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{item.name}</div>
                    <div className="text-xs text-gray-500">৳{item.price}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={() => updateItemQty(item.id, -1)}
                      className="w-8 h-8 rounded border border-gray-300 hover:bg-gray-50"
                    >
                      -
                    </button>
                    <span className="w-8 text-center">{item.qty}</span>
                    <button 
                      onClick={() => updateItemQty(item.id, 1)}
                      className="w-8 h-8 rounded border border-gray-300 hover:bg-gray-50"
                    >
                      +
                    </button>
                    <button 
                      onClick={() => removeItem(item.id)}
                      className="ml-2 p-1 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="flex justify-between items-center mb-4 text-lg font-bold">
              <span>Total</span>
              <span>৳{editItems.reduce((acc: number, i: any) => acc + (parseFloat(i.price) * i.qty), 0)}</span>
            </div>
            
            <div className="flex gap-2">
              <button 
                onClick={() => setEditingOrder(null)}
                className="flex-1 py-2 rounded-xl border border-gray-300 text-gray-700 font-semibold"
              >
                Cancel
              </button>
              <button 
                onClick={handleSaveEdit}
                disabled={submitting || editItems.length === 0}
                className="flex-1 py-2 rounded-xl bg-[#94D8AB] text-[#14532D] font-semibold disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {checkoutOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Checkout Order #{checkoutOrder.id}</h2>
              <button onClick={() => setCheckoutOrder(null)} className="p-1 hover:bg-gray-100 rounded">
                <X size={18} />
              </button>
            </div>
            
            <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-100">
              <div className="flex justify-between text-lg font-bold mb-2 text-[#14532D]">
                <span>Total Amount</span>
                <span>৳{checkoutOrder.total_amount}</span>
              </div>
              <div className="text-sm text-gray-500">
                {checkoutOrder.items.length} items • {checkoutOrder.table_name ? `Table ${checkoutOrder.table_name}` : checkoutOrder.order_type}
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold mb-3">Payment Method</label>
              <div className="grid grid-cols-2 gap-3">
                {['cash', 'card', 'bkash', 'nagad'].map(method => (
                  <button
                    key={method}
                    onClick={() => setPaymentMethod(method)}
                    className={`py-3 px-4 rounded-xl border-2 font-semibold capitalize transition-colors ${
                      paymentMethod === method 
                        ? 'border-[#94D8AB] bg-[#F0FAF3] text-[#14532D]' 
                        : 'border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    {method}
                  </button>
                ))}
              </div>
            </div>
            
            <button 
              onClick={handleProcessPayment}
              disabled={submitting}
              className="w-full py-4 rounded-xl bg-[#94D8AB] text-[#14532D] font-bold text-lg disabled:opacity-50 hover:bg-[#86CB9D] transition-colors"
            >
              {submitting ? 'Processing...' : 'Confirm Payment'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
