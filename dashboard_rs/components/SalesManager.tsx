import { useState, useEffect, useRef, useCallback } from 'react'
import { fetchApi } from '@/lib/api'
import { Table2, X, Search, Coffee, Loader2, ChevronDown } from 'lucide-react'

function cn(...classes: (string | false | undefined)[]) { return classes.filter(Boolean).join(' ') }

export default function SalesManager() {
  const [tables, setTables] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [activeTakeaways, setActiveTakeaways] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedTable, setSelectedTable] = useState<any>(null)
  const [editingOrder, setEditingOrder] = useState<any>(null)
  const [orderOpen, setOrderOpen] = useState(false)
  const [orderItems, setOrderItems] = useState<any[]>([])
  const [isTakeaway, setIsTakeaway] = useState(false)

  const loadData = async () => {
    try {
      setError(null)
      const [tData, cData, oData] = await Promise.all([
        fetchApi('/tables/'),
        fetchApi('/categories/'),
        fetchApi('/orders/?status=open,preparing,served&order_type=takeaway')
      ])
      setTables(tData)
      setCategories(cData)
      setActiveTakeaways(oData)
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleTableClick = (table: any) => {
    setSelectedTable(table)
    setIsTakeaway(false)
    setEditingOrder(null)
    setOrderItems([]) // Reset order items for new table selection
    setOrderOpen(true)
  }

  const handleTakeawayClick = () => {
    setSelectedTable(null)
    setIsTakeaway(true)
    setEditingOrder(null)
    setOrderItems([]) // Reset order items for new takeaway order
    setOrderOpen(true)
  }

  const handleEditTakeawayClick = (order: any) => {
    setSelectedTable(null)
    setIsTakeaway(true)
    setEditingOrder(order)
    setOrderItems(order.items.map((item: any) => ({
      id: item.menu_item,
      name: item.menu_item_name,
      price: item.price_at_time,
      qty: item.quantity
    })))
    setOrderOpen(true)
  }

  const handleOrderClose = () => {
    setOrderOpen(false)
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold">✕</button>
        </div>
      )}
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Daily sales</h1>
          <p className="text-sm text-[#64748b]">Tap a table to start an order.</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleTakeawayClick}
            className="min-h-11 rounded-xl border border-[#94D8AB] px-3 text-sm font-semibold hover:bg-[#F0FAF3]"
          >
            Takeaway
          </button>
          <button className="min-h-11 rounded-xl bg-[#94D8AB] px-4 text-sm font-bold">+ New order</button>
        </div>
      </div>
      
      <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
        <div className="flex flex-col gap-5">
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

          <section className="rounded-2xl border border-[#D5E6DA] bg-white p-4 sm:p-6">
            <h2 className="text-lg font-semibold mb-5 flex justify-between items-center">
              <span>Active Takeaways</span>
              {activeTakeaways.length > 0 && (
                <span className="bg-[#BDE8CB] px-2 py-0.5 rounded-full text-xs font-bold text-[#14532D]">
                  {activeTakeaways.length}
                </span>
              )}
            </h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {activeTakeaways.map((order) => (
                <button 
                  key={order.id} 
                  onClick={() => handleEditTakeawayClick(order)}
                  className="min-h-28 rounded-2xl border-2 border-[#D5E6DA] p-3 text-left bg-white flex flex-col justify-between transition-transform hover:-translate-y-0.5 hover:border-[#94D8AB]"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold">#{order.id}</span>
                    <Coffee size={17} className="text-[#64748b]"/>
                  </div>
                  <div className="mt-3 text-sm font-bold">৳{order.total_amount}</div>
                  <div className="mt-1 text-[10px] font-bold uppercase tracking-wide text-[#64748b]">
                    <span className={cn(
                      'inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold',
                      order.status === 'open' ? 'bg-[#FBE3B5] text-[#92400E]' : 
                      order.status === 'served' ? 'bg-[#DCF3E3] text-[#2F855A]' : 
                      'bg-[#CFE0F7] text-[#1E40AF]'
                    )}>
                      {order.status}
                    </span>
                  </div>
                </button>
              ))}
              {activeTakeaways.length === 0 && (
                <div className="col-span-full text-center text-sm text-[#64748b] py-4">
                  No active takeaway orders
                </div>
              )}
            </div>
          </section>
        </div>
        
        <OrderPanel
          table={selectedTable}
          open={orderOpen}
          setOpen={handleOrderClose}
          categories={categories}
          orderItems={orderItems}
          setOrderItems={setOrderItems}
          onOrderComplete={loadData}
          isTakeaway={isTakeaway}
          editingOrder={editingOrder}
        />
      </div>
    </div>
  )
}

function OrderPanel({ table, open, setOpen, categories, orderItems, setOrderItems, onOrderComplete, isTakeaway, editingOrder }: any) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [customerPhone, setCustomerPhone] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')

  // Autocomplete state
  const [phoneSuggestions, setPhoneSuggestions] = useState<any[]>([])
  const [emailSuggestions, setEmailSuggestions] = useState<any[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null)
  const [showPhoneDropdown, setShowPhoneDropdown] = useState(false)
  const [showEmailDropdown, setShowEmailDropdown] = useState(false)

  // Refs for debouncing and dropdown management
  const phoneSearchRef = useRef<number | null>(null)
  const emailSearchRef = useRef<number | null>(null)
  const phoneDropdownRef = useRef<HTMLDivElement>(null)
  const emailDropdownRef = useRef<HTMLDivElement>(null)
  const requestIdRef = useRef<number>(0)

  // Debounced search function - MUST be called before any conditional returns
  const searchCustomers = useCallback(async (query: string, type: 'phone' | 'email') => {
    if (query.length < 3) {
      if (type === 'phone') setPhoneSuggestions([])
      else setEmailSuggestions([])
      return
    }

    setSearchLoading(true)
    setSearchError(null)

    const currentRequestId = ++requestIdRef.current

    try {
      const endpoint = type === 'phone'
        ? `/customers/search/?phone=${encodeURIComponent(query)}`
        : `/customers/search/?email=${encodeURIComponent(query)}`

      const results = await fetchApi(endpoint)

      // Ignore stale responses
      if (currentRequestId !== requestIdRef.current) return

      if (type === 'phone') setPhoneSuggestions(results)
      else setEmailSuggestions(results)
    } catch (err: any) {
      if (currentRequestId !== requestIdRef.current) return
      setSearchError(err.message || 'Search failed')
      if (type === 'phone') setPhoneSuggestions([])
      else setEmailSuggestions([])
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setSearchLoading(false)
      }
    }
  }, [])

  // Clear customer state when panel closes
  useEffect(() => {
    if (!open) {
      setCustomerPhone('')
      setCustomerName('')
      setCustomerEmail('')
      setSelectedCustomer(null)
      setPhoneSuggestions([])
      setEmailSuggestions([])
      setShowPhoneDropdown(false)
      setShowEmailDropdown(false)
    }
  }, [open])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (phoneDropdownRef.current && !phoneDropdownRef.current.contains(event.target as Node)) {
        setShowPhoneDropdown(false)
      }
      if (emailDropdownRef.current && !emailDropdownRef.current.contains(event.target as Node)) {
        setShowEmailDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (phoneSearchRef.current) clearTimeout(phoneSearchRef.current)
      if (emailSearchRef.current) clearTimeout(emailSearchRef.current)
    }
  }, [])

  if (!open || (!table && !isTakeaway)) return <section className="rounded-2xl border border-[#D5E6DA] bg-white p-5 xl:sticky xl:top-24 hidden xl:block"><div className="text-center text-sm text-[#64748b] mt-10">Select a table to start an order</div></section>

  // Handle phone input with debouncing
  const handlePhoneChange = (value: string) => {
    setCustomerPhone(value)

    // Invalidate selection if phone no longer matches
    if (selectedCustomer && selectedCustomer.phone !== value.trim()) {
      setSelectedCustomer(null)
    }

    // Clear previous timeout
    if (phoneSearchRef.current) {
      clearTimeout(phoneSearchRef.current)
    }

    // Debounce search
    if (value.trim().length >= 3) {
      phoneSearchRef.current = window.setTimeout(() => {
        searchCustomers(value.trim(), 'phone')
      }, 300)
      setShowPhoneDropdown(true)
    } else {
      setPhoneSuggestions([])
      setShowPhoneDropdown(false)
    }
  }

  // Handle email input with debouncing
  const handleEmailChange = (value: string) => {
    setCustomerEmail(value)

    // Invalidate selection if email no longer matches
    if (selectedCustomer && selectedCustomer.email?.toLowerCase() !== value.trim().toLowerCase()) {
      setSelectedCustomer(null)
    }

    // Clear previous timeout
    if (emailSearchRef.current) {
      clearTimeout(emailSearchRef.current)
    }

    // Debounce search
    if (value.trim().length >= 3) {
      emailSearchRef.current = window.setTimeout(() => {
        searchCustomers(value.trim(), 'email')
      }, 300)
      setShowEmailDropdown(true)
    } else {
      setEmailSuggestions([])
      setShowEmailDropdown(false)
    }
  }

  // Handle customer selection
  const handleSelectCustomer = (customer: any) => {
    setSelectedCustomer(customer)
    setCustomerPhone(customer.phone || '')
    setCustomerName(customer.name || '')
    setCustomerEmail(customer.email || '')
    setShowPhoneDropdown(false)
    setShowEmailDropdown(false)
    setPhoneSuggestions([])
    setEmailSuggestions([])
  }

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
    setError(null)
    try {
      let endpoint = '/orders/create_with_items/'
      let method = 'POST'
      const payload: any = {
        items: orderItems.map((item: any) => ({
          menu_item: item.id,
          quantity: item.qty,
          notes: null
        }))
      }

      if (editingOrder) {
        endpoint = `/orders/${editingOrder.id}/update_with_items/`
        method = 'PATCH'
      } else {
        payload.table = isTakeaway ? null : table.id
        payload.order_type = isTakeaway ? 'takeaway' : 'dine-in'
        payload.status = 'open'

        // Use customer_id if a customer is selected
        if (selectedCustomer) {
          payload.customer_id = selectedCustomer.id
        } else {
          // Fall back to phone/name/email for new customer creation
          if (customerPhone.trim() !== '') {
            payload.customer_phone = customerPhone.trim()
          }
          if (customerName.trim() !== '') {
            payload.customer_name = customerName.trim()
          }
          if (customerEmail.trim() !== '') {
            payload.customer_email = customerEmail.trim()
          }
        }
      }

      await fetchApi(endpoint, {
        method: method,
        body: JSON.stringify(payload)
      })

      setOpen(false)
      onOrderComplete()
    } catch (err: any) {
      setError(err.message || 'Failed to create order')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="rounded-2xl border border-[#D5E6DA] bg-white p-5 xl:sticky xl:top-24 xl:h-fit">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">
            {isTakeaway 
              ? (editingOrder ? `Editing Takeaway #${editingOrder.id}` : 'Takeaway Order') 
              : `${table.name} · New Order`}
          </h2>
          <p className="text-xs text-[#64748b]">
            {isTakeaway ? (editingOrder ? `Status: ${editingOrder.status}` : 'No table') : `${table.seats} seats · Dine-in`}
          </p>
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
      
      {!editingOrder && (
        <div className="mb-4 border-t border-[#D5E6DA] pt-4 space-y-3">
          <div className="relative" ref={phoneDropdownRef}>
            <label className="block text-xs font-semibold text-[#64748b] mb-1">Customer Phone (Optional)</label>
            <div className="relative">
              <input
                type="tel"
                placeholder="e.g. 01700000000"
                className={cn(
                  "w-full rounded-xl border border-[#D5E6DA] bg-gray-50 px-3 py-2.5 text-sm focus:border-[#94D8AB] focus:bg-white focus:outline-none",
                  selectedCustomer && "bg-[#F0FAF3] border-[#94D8AB]"
                )}
                value={customerPhone}
                onChange={(e) => handlePhoneChange(e.target.value)}
                onFocus={() => customerPhone.length >= 3 && setShowPhoneDropdown(true)}
              />
              {selectedCustomer && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-[#14532D] bg-[#94D8AB] px-2 py-0.5 rounded-full">
                  Selected
                </div>
              )}
            </div>

            {/* Phone autocomplete dropdown */}
            {showPhoneDropdown && (phoneSuggestions.length > 0 || searchLoading || searchError) && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-[#D5E6DA] rounded-xl shadow-lg max-h-48 overflow-y-auto">
                {searchLoading && (
                  <div className="p-3 text-center text-sm text-[#64748b]">
                    <Loader2 className="animate-spin mx-auto" size={16} />
                  </div>
                )}
                {searchError && (
                  <div className="p-3 text-center text-sm text-red-600">
                    {searchError}
                  </div>
                )}
                {!searchLoading && !searchError && phoneSuggestions.length === 0 && (
                  <div className="p-3 text-center text-sm text-[#64748b]">
                    No customers found
                  </div>
                )}
                {!searchLoading && !searchError && phoneSuggestions.map((customer) => (
                  <button
                    key={customer.id}
                    onClick={() => handleSelectCustomer(customer)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-[#F0FAF3] border-b border-[#D5E6DA] last:border-0"
                  >
                    <div className="font-semibold">{customer.name}</div>
                    <div className="text-xs text-[#64748b]">{customer.phone}</div>
                    {customer.email && (
                      <div className="text-xs text-[#64748b]">{customer.email}</div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#64748b] mb-1">Customer Name (Optional)</label>
            <input
              type="text"
              placeholder="e.g. John Doe"
              className={cn(
                "w-full rounded-xl border border-[#D5E6DA] bg-gray-50 px-3 py-2.5 text-sm focus:border-[#94D8AB] focus:bg-white focus:outline-none",
                selectedCustomer && "bg-[#F0FAF3] border-[#94D8AB]"
              )}
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              readOnly={!!selectedCustomer}
            />
          </div>

          <div className="relative" ref={emailDropdownRef}>
            <label className="block text-xs font-semibold text-[#64748b] mb-1">Customer Email (Optional)</label>
            <div className="relative">
              <input
                type="email"
                placeholder="e.g. john@example.com"
                className={cn(
                  "w-full rounded-xl border border-[#D5E6DA] bg-gray-50 px-3 py-2.5 text-sm focus:border-[#94D8AB] focus:bg-white focus:outline-none",
                  selectedCustomer && "bg-[#F0FAF3] border-[#94D8AB]"
                )}
                value={customerEmail}
                onChange={(e) => handleEmailChange(e.target.value)}
                onFocus={() => customerEmail.length >= 3 && setShowEmailDropdown(true)}
              />
              {selectedCustomer && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-[#14532D] bg-[#94D8AB] px-2 py-0.5 rounded-full">
                  Selected
                </div>
              )}
            </div>

            {/* Email autocomplete dropdown */}
            {showEmailDropdown && (emailSuggestions.length > 0 || searchLoading || searchError) && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-[#D5E6DA] rounded-xl shadow-lg max-h-48 overflow-y-auto">
                {searchLoading && (
                  <div className="p-3 text-center text-sm text-[#64748b]">
                    <Loader2 className="animate-spin mx-auto" size={16} />
                  </div>
                )}
                {searchError && (
                  <div className="p-3 text-center text-sm text-red-600">
                    {searchError}
                  </div>
                )}
                {!searchLoading && !searchError && emailSuggestions.length === 0 && (
                  <div className="p-3 text-center text-sm text-[#64748b]">
                    No customers found
                  </div>
                )}
                {!searchLoading && !searchError && emailSuggestions.map((customer) => (
                  <button
                    key={customer.id}
                    onClick={() => handleSelectCustomer(customer)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-[#F0FAF3] border-b border-[#D5E6DA] last:border-0"
                  >
                    <div className="font-semibold">{customer.name}</div>
                    <div className="text-xs text-[#64748b]">{customer.phone}</div>
                    {customer.email && (
                      <div className="text-xs text-[#64748b]">{customer.email}</div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {selectedCustomer && (
            <button
              onClick={() => {
                setSelectedCustomer(null)
                setCustomerPhone('')
                setCustomerName('')
                setCustomerEmail('')
              }}
              className="text-xs text-[#64748b] hover:text-[#14532D] underline"
            >
              Clear customer selection
            </button>
          )}
        </div>
      )}
      
      <div className="flex flex-col gap-2">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 font-bold">✕</button>
          </div>
        )}
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
