import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Plus, Edit, Trash, Loader2 } from 'lucide-react'

export default function MenuManager() {
  const [categories, setCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [newCatName, setNewCatName] = useState('')

  const loadData = async () => {
    try {
      const data = await fetchApi('/categories/')
      setCategories(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const addCategory = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCatName.trim()) return
    await fetchApi('/categories/', {
      method: 'POST',
      body: JSON.stringify({ name: newCatName, sort_order: categories.length }),
    })
    setNewCatName('')
    loadData()
  }

  const deleteCategory = async (id: number) => {
    if (!confirm('Are you sure?')) return
    await fetchApi(`/categories/${id}/`, { method: 'DELETE' })
    loadData()
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Menu Management</h1>
      </div>
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <h2 className="text-lg font-semibold mb-4">Categories</h2>
        <form onSubmit={addCategory} className="flex gap-2 mb-6">
          <input
            value={newCatName}
            onChange={e => setNewCatName(e.target.value)}
            placeholder="New category name"
            className="flex-1 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm outline-none focus:border-[#94D8AB]"
          />
          <button type="submit" className="bg-[#94D8AB] px-4 py-2 rounded-xl text-sm font-bold text-[#14532D]">Add</button>
        </form>

        <div className="flex flex-col gap-4">
          {categories.map(cat => (
            <div key={cat.id} className="border border-[#D5E6DA] rounded-xl p-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold text-lg">{cat.name}</h3>
                <button onClick={() => deleteCategory(cat.id)} className="text-red-500 hover:bg-red-50 p-2 rounded-lg"><Trash size={16} /></button>
              </div>
              <div className="pl-4 border-l-2 border-[#D5E6DA]">
                {cat.items?.map((item: any) => (
                  <div key={item.id} className="flex justify-between py-2 text-sm">
                    <span>{item.name}</span>
                    <span className="font-semibold">৳{item.price}</span>
                  </div>
                ))}
                <AddItemForm categoryId={cat.id} onAdded={loadData} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function AddItemForm({ categoryId, onAdded }: { categoryId: number, onAdded: () => void }) {
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [adding, setAdding] = useState(false)

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !price) return
    setAdding(true)
    await fetchApi('/menu-items/', {
      method: 'POST',
      body: JSON.stringify({ category: categoryId, name, price: parseFloat(price) })
    })
    setName('')
    setPrice('')
    setAdding(false)
    onAdded()
  }

  return (
    <form onSubmit={handleAdd} className="mt-2 flex gap-2 items-center text-sm">
      <input
        required
        value={name}
        onChange={e => setName(e.target.value)}
        placeholder="Item name"
        className="flex-1 rounded-lg border border-[#D5E6DA] px-2 py-1 outline-none"
      />
      <input
        required
        type="number"
        value={price}
        onChange={e => setPrice(e.target.value)}
        placeholder="Price"
        className="w-24 rounded-lg border border-[#D5E6DA] px-2 py-1 outline-none"
      />
      <button disabled={adding} type="submit" className="text-[#2F855A] font-bold px-2">Add Item</button>
    </form>
  )
}
