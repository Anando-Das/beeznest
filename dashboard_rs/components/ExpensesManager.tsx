import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, Plus, Trash } from 'lucide-react'

export default function ExpensesManager() {
  const [expenses, setExpenses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({ category: '', amount: '', description: '' })

  const loadData = async () => {
    try {
      const data = await fetchApi('/expenses/')
      setExpenses(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const addExpense = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.category || !formData.amount) return
    await fetchApi('/expenses/', {
      method: 'POST',
      body: JSON.stringify({ ...formData, amount: parseFloat(formData.amount) }),
    })
    setFormData({ category: '', amount: '', description: '' })
    loadData()
  }

  const deleteExpense = async (id: number) => {
    if (!confirm('Are you sure?')) return
    await fetchApi(`/expenses/${id}/`, { method: 'DELETE' })
    loadData()
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Expenses</h1>
      </div>
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <h2 className="text-lg font-semibold mb-4">Add Expense</h2>
        <form onSubmit={addExpense} className="flex gap-2 mb-6">
          <input
            required
            value={formData.category}
            onChange={e => setFormData({...formData, category: e.target.value})}
            placeholder="Category (e.g. Utilities)"
            className="flex-1 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm outline-none focus:border-[#94D8AB]"
          />
          <input
            required
            type="number"
            value={formData.amount}
            onChange={e => setFormData({...formData, amount: e.target.value})}
            placeholder="Amount"
            className="w-32 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm outline-none focus:border-[#94D8AB]"
          />
          <input
            value={formData.description}
            onChange={e => setFormData({...formData, description: e.target.value})}
            placeholder="Description (optional)"
            className="flex-1 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm outline-none focus:border-[#94D8AB]"
          />
          <button type="submit" className="bg-[#94D8AB] px-4 py-2 rounded-xl text-sm font-bold text-[#14532D]">Add</button>
        </form>

        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[#D5E6DA] text-[#64748b]">
              <th className="pb-3 font-semibold">Date</th>
              <th className="pb-3 font-semibold">Category</th>
              <th className="pb-3 font-semibold">Description</th>
              <th className="pb-3 font-semibold">Amount</th>
              <th className="pb-3 font-semibold">Action</th>
            </tr>
          </thead>
          <tbody>
            {expenses.map(exp => (
              <tr key={exp.id} className="border-b border-[#F0FAF3] last:border-0">
                <td className="py-3 font-medium">{exp.date}</td>
                <td className="py-3">{exp.category}</td>
                <td className="py-3">{exp.description || '-'}</td>
                <td className="py-3 font-semibold text-[#92400E]">৳{exp.amount}</td>
                <td className="py-3">
                  <button onClick={() => deleteExpense(exp.id)} className="text-red-500 hover:bg-red-50 p-1 rounded-md"><Trash size={14}/></button>
                </td>
              </tr>
            ))}
            {expenses.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-[#64748b]">No expenses found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
