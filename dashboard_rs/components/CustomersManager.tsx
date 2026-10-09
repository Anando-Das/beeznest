import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, Plus, Edit, X, Search, User, Clock, DollarSign, Receipt, Sparkles, TrendingUp, TrendingDown } from 'lucide-react'

export default function CustomersManager() {
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', phone: '', email: '' })
  const [orderHistory, setOrderHistory] = useState<any>(null)
  const [orderHistoryLoading, setOrderHistoryLoading] = useState(false)
  const [orderHistoryError, setOrderHistoryError] = useState<string | null>(null)
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const [showOrderDetail, setShowOrderDetail] = useState(false)
  const [loyaltyTransactions, setLoyaltyTransactions] = useState<any[]>([])
  const [loyaltyLoading, setLoyaltyLoading] = useState(false)
  const [loyaltyError, setLoyaltyError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      setError(null)
      const data = await fetchApi('/customers/')
      setCustomers(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleAddClick = () => {
    setForm({ name: '', phone: '', email: '' })
    setError(null)
    setShowAddModal(true)
  }

  const handleEditClick = (customer: any) => {
    setSelectedCustomer(customer)
    setForm({ name: customer.name, phone: customer.phone || '', email: customer.email || '' })
    setError(null)
    setShowEditModal(true)
  }

  const handleDetailClick = async (customer: any) => {
    setSelectedCustomer(customer)
    setShowDetailModal(true)
    setOrderHistory(null)
    setOrderHistoryError(null)
    setOrderHistoryLoading(true)
    setLoyaltyTransactions([])
    setLoyaltyError(null)
    setLoyaltyLoading(true)

    try {
      const [orderData, loyaltyData] = await Promise.all([
        fetchApi(`/customers/${customer.id}/order_history/`),
        fetchApi(`/point-transactions/?customer=${customer.id}`).catch(() => [])
      ])
      setOrderHistory(orderData)
      setLoyaltyTransactions(loyaltyData)
    } catch (err: any) {
      setOrderHistoryError(err.message || 'Failed to load order history')
    } finally {
      setOrderHistoryLoading(false)
      setLoyaltyLoading(false)
    }
  }

  const handleSubmit = async (isEdit: boolean) => {
    if (submitting) return
    if (!form.name.trim()) {
      setError('Name is required')
      return
    }
    
    setSubmitting(true)
    setError(null)
    try {
      if (isEdit && selectedCustomer) {
        await fetchApi(`/customers/${selectedCustomer.id}/`, {
          method: 'PATCH',
          body: JSON.stringify({
            name: form.name.trim(),
            phone: form.phone.trim() || null,
            email: form.email.trim() || null
          })
        })
      } else {
        await fetchApi('/customers/', {
          method: 'POST',
          body: JSON.stringify({
            name: form.name.trim(),
            phone: form.phone.trim() || null,
            email: form.email.trim() || null
          })
        })
      }
      
      setShowAddModal(false)
      setShowEditModal(false)
      setSelectedCustomer(null)
      setForm({ name: '', phone: '', email: '' })
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to save customer')
    } finally {
      setSubmitting(false)
    }
  }

  const filteredCustomers = customers.filter(c => {
    const query = searchQuery.toLowerCase()
    return (
      c.name.toLowerCase().includes(query) ||
      (c.phone && c.phone.includes(query)) ||
      (c.email && c.email.toLowerCase().includes(query))
    )
  })

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold">Customers</h1>
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748b]" size={16} />
            <input
              type="text"
              placeholder="Search customers..."
              className="pl-9 pr-4 py-2 rounded-xl border border-[#D5E6DA] bg-white text-sm focus:border-[#94D8AB] focus:outline-none w-64"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button
            onClick={handleAddClick}
            className="min-h-10 rounded-xl bg-[#94D8AB] px-4 text-sm font-bold text-[#14532D] hover:bg-[#7EC796] flex items-center gap-2"
          >
            <Plus size={16} />
            Add Customer
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold">✕</button>
        </div>
      )}
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[#D5E6DA] text-[#64748b]">
              <th className="pb-3 font-semibold">Name</th>
              <th className="pb-3 font-semibold">Phone</th>
              <th className="pb-3 font-semibold">Email</th>
              <th className="pb-3 font-semibold">Points</th>
              <th className="pb-3 font-semibold">Orders</th>
              <th className="pb-3 font-semibold">Member Since</th>
              <th className="pb-3 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredCustomers.map(c => (
              <tr key={c.id} className="border-b border-[#F0FAF3] last:border-0 hover:bg-[#F0FAF3]">
                <td className="py-3 font-medium">{c.name}</td>
                <td className="py-3">{c.phone || '-'}</td>
                <td className="py-3">{c.email || '-'}</td>
                <td className="py-3 font-bold text-[#2F855A]">{c.points}</td>
                <td className="py-3">{c.order_count || 0}</td>
                <td className="py-3 text-[#64748b]">{new Date(c.created_at).toLocaleDateString()}</td>
                <td className="py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => handleDetailClick(c)}
                      className="p-1.5 hover:bg-[#F0FAF3] rounded text-[#64748b]"
                      title="View Details"
                    >
                      <User size={14} />
                    </button>
                    <button
                      onClick={() => handleEditClick(c)}
                      className="p-1.5 hover:bg-[#F0FAF3] rounded text-[#64748b]"
                      title="Edit Customer"
                    >
                      <Edit size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredCustomers.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-[#64748b]">
                  {searchQuery ? 'No customers match your search' : 'No customers found'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add Customer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Add Customer</h2>
              <button onClick={() => setShowAddModal(false)} className="p-1 hover:bg-gray-100 rounded">
                <X size={18} />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#64748b] mb-1">Name *</label>
                <input
                  type="text"
                  className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm focus:border-[#94D8AB] focus:outline-none"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Customer name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#64748b] mb-1">Phone</label>
                <input
                  type="tel"
                  className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm focus:border-[#94D8AB] focus:outline-none"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder="Phone number"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#64748b] mb-1">Email</label>
                <input
                  type="email"
                  className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm focus:border-[#94D8AB] focus:outline-none"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="Email address"
                />
              </div>
            </div>
            
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-2 rounded-xl border border-gray-300 text-gray-700 font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSubmit(false)}
                disabled={submitting || !form.name.trim()}
                className="flex-1 py-2 rounded-xl bg-[#94D8AB] text-[#14532D] font-semibold disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Add Customer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Customer Modal */}
      {showEditModal && selectedCustomer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Edit Customer</h2>
              <button onClick={() => setShowEditModal(false)} className="p-1 hover:bg-gray-100 rounded">
                <X size={18} />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#64748b] mb-1">Name *</label>
                <input
                  type="text"
                  className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm focus:border-[#94D8AB] focus:outline-none"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Customer name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#64748b] mb-1">Phone</label>
                <input
                  type="tel"
                  className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm focus:border-[#94D8AB] focus:outline-none"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder="Phone number"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#64748b] mb-1">Email</label>
                <input
                  type="email"
                  className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm focus:border-[#94D8AB] focus:outline-none"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="Email address"
                />
              </div>
            </div>
            
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 py-2 rounded-xl border border-gray-300 text-gray-700 font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSubmit(true)}
                disabled={submitting || !form.name.trim()}
                className="flex-1 py-2 rounded-xl bg-[#94D8AB] text-[#14532D] font-semibold disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Customer Detail Modal */}
      {showDetailModal && selectedCustomer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold">Customer Details</h2>
              <button onClick={() => setShowDetailModal(false)} className="p-1 hover:bg-gray-100 rounded">
                <X size={18} />
              </button>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Customer Info */}
              <div className="lg:col-span-1">
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-[#94D8AB] flex items-center justify-center">
                      <User className="text-[#14532D]" size={24} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{selectedCustomer.name}</h3>
                      <p className="text-sm text-[#64748b]">Customer ID: #{selectedCustomer.id}</p>
                    </div>
                  </div>

                  <div className="border-t border-[#D5E6DA] pt-4 space-y-3">
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Phone</span>
                      <span className="font-medium">{selectedCustomer.phone || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Email</span>
                      <span className="font-medium">{selectedCustomer.email || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Points</span>
                      <span className="font-bold text-[#2F855A]">{selectedCustomer.points}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Member Since</span>
                      <span className="font-medium">{new Date(selectedCustomer.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Order Statistics */}
                  {orderHistory && (
                    <div className="border-t border-[#D5E6DA] pt-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <Receipt className="text-[#64748b]" size={16} />
                        <span className="font-semibold">Order Statistics</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-[#64748b]">Total Orders</span>
                        <span className="font-bold text-[#2F855A]">{orderHistory.total_orders}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-[#64748b]">Total Spending</span>
                        <span className="font-bold text-[#2F855A]">৳{orderHistory.total_spending}</span>
                      </div>
                      {orderHistory.most_recent_order_date && (
                        <div className="flex justify-between items-center">
                          <span className="text-[#64748b]">Last Order</span>
                          <span className="font-medium">{new Date(orderHistory.most_recent_order_date).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Loyalty Points History */}
                  <div className="border-t border-[#D5E6DA] pt-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="text-[#64748b]" size={16} />
                      <span className="font-semibold">Loyalty Points History</span>
                    </div>
                    {loyaltyLoading ? (
                      <div className="flex justify-center py-4">
                        <Loader2 className="animate-spin text-[#64748b]" size={16} />
                      </div>
                    ) : loyaltyError ? (
                      <div className="text-xs text-red-600">{loyaltyError}</div>
                    ) : loyaltyTransactions.length === 0 ? (
                      <div className="text-xs text-[#64748b]">No loyalty transactions</div>
                    ) : (
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {loyaltyTransactions.slice(0, 10).map((tx: any) => (
                          <div key={tx.id} className="flex items-center justify-between text-xs py-2 border-b border-[#F0FAF3] last:border-0">
                            <div className="flex-1">
                              <div className="font-medium capitalize">{tx.transaction_type.toLowerCase()}</div>
                              <div className="text-[#64748b]">
                                {new Date(tx.created_at).toLocaleDateString()}
                                {tx.order_id && ` • Order #${tx.order_id}`}
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              {tx.points > 0 ? (
                                <TrendingUp size={12} className="text-[#2F855A]" />
                              ) : (
                                <TrendingDown size={12} className="text-[#DC2626]" />
                              )}
                              <span className={`font-bold ${tx.points > 0 ? 'text-[#2F855A]' : 'text-[#DC2626]'}`}>
                                {tx.points > 0 ? '+' : ''}{tx.points}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Order History */}
              <div className="lg:col-span-2">
                <div className="border-t border-[#D5E6DA] lg:border-t-0 lg:border-l lg:pl-6 pt-6 lg:pt-0">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Clock size={18} />
                    Order History
                  </h3>

                  {orderHistoryLoading && (
                    <div className="flex justify-center py-8">
                      <Loader2 className="animate-spin text-[#64748b]" />
                    </div>
                  )}

                  {orderHistoryError && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">
                      {orderHistoryError}
                    </div>
                  )}

                  {orderHistory && !orderHistoryLoading && (
                    <>
                      {orderHistory.orders.length === 0 ? (
                        <div className="text-center py-8 text-[#64748b]">
                          No orders found for this customer
                        </div>
                      ) : (
                        <div className="space-y-3 max-h-96 overflow-y-auto">
                          {orderHistory.orders.map((order: any) => (
                            <div
                              key={order.id}
                              className="border border-[#D5E6DA] rounded-xl p-4 hover:bg-[#F0FAF3] cursor-pointer transition-colors"
                              onClick={() => {
                                setSelectedOrder(order)
                                setShowOrderDetail(true)
                              }}
                            >
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <div className="font-semibold">Order #{order.id}</div>
                                  <div className="text-xs text-[#64748b]">
                                    {new Date(order.created_at).toLocaleString()}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="font-bold text-[#2F855A]">৳{order.total_amount}</div>
                                  <div className={`text-xs px-2 py-0.5 rounded-full inline-block ${
                                    order.status === 'paid' ? 'bg-[#DCF3E3] text-[#2F855A]' :
                                    order.status === 'cancelled' ? 'bg-[#FEE2E2] text-[#DC2626]' :
                                    'bg-[#FBE3B5] text-[#92400E]'
                                  }`}>
                                    {order.status}
                                  </div>
                                </div>
                              </div>
                              <div className="flex gap-2 text-xs text-[#64748b] mb-2">
                                <span className="capitalize">{order.order_type}</span>
                                {order.table_name && <span>• {order.table_name}</span>}
                              </div>
                              <div className="text-xs text-[#64748b]">
                                {order.items.length === 1
                                  ? `${order.items[0].quantity}x ${order.items[0].menu_item_name}`
                                  : `${order.items.length} items`
                                }
                              </div>
                              {order.payment_method && (
                                <div className="text-xs text-[#64748b] mt-1">
                                  Paid via {order.payment_method}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-[#D5E6DA]">
              <button
                onClick={() => setShowDetailModal(false)}
                className="w-full py-2 rounded-xl bg-[#94D8AB] text-[#14532D] font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Order Detail Modal */}
      {showOrderDetail && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold">Order Details #{selectedOrder.id}</h2>
              <button onClick={() => setShowOrderDetail(false)} className="p-1 hover:bg-gray-100 rounded">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-[#64748b]">Date:</span>
                  <span className="ml-2 font-medium">{new Date(selectedOrder.created_at).toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-[#64748b]">Type:</span>
                  <span className="ml-2 font-medium capitalize">{selectedOrder.order_type}</span>
                </div>
                <div>
                  <span className="text-[#64748b]">Status:</span>
                  <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-semibold ${
                    selectedOrder.status === 'paid' ? 'bg-[#DCF3E3] text-[#2F855A]' :
                    selectedOrder.status === 'cancelled' ? 'bg-[#FEE2E2] text-[#DC2626]' :
                    'bg-[#FBE3B5] text-[#92400E]'
                  }`}>
                    {selectedOrder.status}
                  </span>
                </div>
                {selectedOrder.table_name && (
                  <div>
                    <span className="text-[#64748b]">Table:</span>
                    <span className="ml-2 font-medium">{selectedOrder.table_name}</span>
                  </div>
                )}
              </div>

              <div className="border-t border-[#D5E6DA] pt-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Receipt size={16} />
                  Items
                </h3>
                <div className="space-y-2">
                  {selectedOrder.items.map((item: any, index: number) => (
                    <div key={index} className="flex justify-between items-center text-sm py-2 border-b border-[#F0FAF3] last:border-0">
                      <div className="flex-1">
                        <div className="font-medium">{item.menu_item_name}</div>
                        <div className="text-xs text-[#64748b]">
                          {item.quantity} x ৳{item.price_at_time}
                        </div>
                        {item.notes && (
                          <div className="text-xs text-[#64748b] italic">Note: {item.notes}</div>
                        )}
                      </div>
                      <div className="font-semibold">
                        ৳{(parseFloat(item.price_at_time) * item.quantity).toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-[#D5E6DA] pt-4">
                <div className="flex justify-between items-center text-lg font-bold">
                  <span>Total</span>
                  <span className="text-[#2F855A]">৳{selectedOrder.total_amount}</span>
                </div>
              </div>

              {selectedOrder.payment_method && (
                <div className="border-t border-[#D5E6DA] pt-4">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <DollarSign size={16} />
                    Payment
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-[#64748b]">Method:</span>
                      <span className="ml-2 font-medium capitalize">{selectedOrder.payment_method}</span>
                    </div>
                    <div>
                      <span className="text-[#64748b]">Amount:</span>
                      <span className="ml-2 font-bold">৳{selectedOrder.payment_amount}</span>
                    </div>
                    {selectedOrder.payment_timestamp && (
                      <div className="col-span-2">
                        <span className="text-[#64748b]">Paid on:</span>
                        <span className="ml-2 font-medium">{new Date(selectedOrder.payment_timestamp).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-[#D5E6DA]">
              <button
                onClick={() => setShowOrderDetail(false)}
                className="w-full py-2 rounded-xl bg-[#94D8AB] text-[#14532D] font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
