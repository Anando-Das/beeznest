import { useState, useEffect } from 'react'
import { fetchApi, BACKEND_URL } from '@/lib/api'
import { Plus, Edit, Trash, Loader2, Image as ImageIcon, History, ChevronDown, ChevronUp } from 'lucide-react'

function cn(...classes: (string | false | undefined)[]) { return classes.filter(Boolean).join(' ') }

const getImageUrl = (image: string | null) => {
  if (!image) return null;
  if (image.startsWith('http') || image.startsWith('data:')) return image;
  return `${BACKEND_URL}${image.startsWith('/') ? '' : '/'}${image}`;
}

export default function MenuManager() {
  const [categories, setCategories] = useState<any[]>([])
  const [role, setRole] = useState('')
  const [loading, setLoading] = useState(true)
  const [newCatName, setNewCatName] = useState('')

  const loadData = async () => {
    try {
      const [me, data] = await Promise.all([
        fetchApi('/me/'),
        fetchApi('/categories/')
      ])
      setRole(me.role)
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

  const toggleCategoryActive = async (id: number, current: boolean) => {
    await fetchApi(`/categories/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !current })
    })
    loadData()
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  const isManagerOrOwner = role === 'OWNER' || role === 'MANAGER'
  const isKitchen = role === 'KITCHEN'

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Menu Management</h1>
      </div>
      
      <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
        <h2 className="text-lg font-semibold mb-4">Categories</h2>
        
        {isManagerOrOwner && (
          <form onSubmit={addCategory} className="flex gap-2 mb-6">
            <input
              value={newCatName}
              onChange={e => setNewCatName(e.target.value)}
              placeholder="New category name"
              className="flex-1 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm outline-none focus:border-[#94D8AB]"
            />
            <button type="submit" className="bg-[#94D8AB] px-4 py-2 rounded-xl text-sm font-bold text-[#14532D]">Add</button>
          </form>
        )}

        <div className="flex flex-col gap-4">
          {categories.map(cat => (
            <div key={cat.id} className={cn("border rounded-xl p-4 transition-opacity", cat.is_active ? "border-[#D5E6DA]" : "border-gray-200 opacity-60")}>
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-3">
                  <h3 className="font-bold text-lg">{cat.name}</h3>
                  {isManagerOrOwner && (
                    <button 
                      onClick={() => toggleCategoryActive(cat.id, cat.is_active)}
                      className={cn("text-xs px-2 py-1 rounded-full border font-semibold", cat.is_active ? "border-green-200 bg-green-50 text-green-700" : "border-gray-200 bg-gray-50 text-gray-500")}
                    >
                      {cat.is_active ? 'Active' : 'Inactive'}
                    </button>
                  )}
                  {!isManagerOrOwner && !cat.is_active && (
                    <span className="text-xs px-2 py-1 rounded-full border border-gray-200 bg-gray-50 text-gray-500 font-semibold">Inactive</span>
                  )}
                </div>
                {isManagerOrOwner && (
                  <button onClick={() => deleteCategory(cat.id)} className="text-red-500 hover:bg-red-50 p-2 rounded-lg"><Trash size={16} /></button>
                )}
              </div>
              <div className="pl-4 border-l-2 border-[#D5E6DA] flex flex-col gap-3">
                {cat.items?.map((item: any) => (
                  <MenuItemRow key={item.id} item={item} role={role} onUpdated={loadData} />
                ))}
                {isManagerOrOwner && (
                  <AddItemForm categoryId={cat.id} onAdded={loadData} />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MenuItemRow({ item, role, onUpdated }: { item: any, role: string, onUpdated: () => void }) {
  const [editing, setEditing] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState<any[]>([])
  
  const isManagerOrOwner = role === 'OWNER' || role === 'MANAGER'

  const toggleAvailability = async () => {
    await fetchApi(`/menu-items/${item.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_available: !item.is_available })
    })
    onUpdated()
  }

  const loadHistory = async () => {
    if (!historyOpen) {
      const res = await fetchApi(`/menu-item-price-history/?menu_item=${item.id}`)
      setHistory(res)
    }
    setHistoryOpen(!historyOpen)
  }

  if (editing && isManagerOrOwner) {
    return <EditItemForm item={item} onCancel={() => setEditing(false)} onSaved={() => { setEditing(false); onUpdated(); }} />
  }

  return (
    <div className={cn("flex flex-col gap-2 p-3 rounded-lg border", item.is_available ? "border-transparent hover:bg-[#F0FAF3]" : "border-gray-200 bg-gray-50 opacity-70")}>
      <div className="flex justify-between items-start">
        <div className="flex items-start gap-3">
          {item.image && (
            <img 
              src={getImageUrl(item.image)!} 
              alt={item.name} 
              className="w-12 h-12 rounded-lg object-cover bg-gray-100" 
              onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling?.classList.remove('hidden') }} 
            />
          )}
          <div className={cn("w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center text-gray-400", item.image ? "hidden" : "")}>
            <ImageIcon size={20} />
          </div>
          <div>
            <div className="font-semibold text-sm flex items-center gap-2">
              {item.name}
              {!item.is_available && <span className="text-[10px] uppercase tracking-wider font-bold bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">Unavailable</span>}
            </div>
            {item.description && <div className="text-xs text-[#64748b] mt-0.5 line-clamp-1">{item.description}</div>}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="font-bold text-sm">৳{item.price}</div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={toggleAvailability}
              className={cn("text-xs px-2 py-1 rounded border font-semibold", item.is_available ? "border-[#94D8AB] text-[#14532D] bg-[#D5E6DA]" : "border-gray-300 text-gray-600 bg-white")}
            >
              {item.is_available ? 'Available' : 'Make Avail'}
            </button>

            {isManagerOrOwner && (
              <>
                <button onClick={() => setEditing(true)} className="p-1.5 text-[#64748b] hover:bg-white rounded"><Edit size={14} /></button>
                <button onClick={loadHistory} className="p-1.5 text-[#64748b] hover:bg-white rounded" title="Price History"><History size={14} /></button>
              </>
            )}
          </div>
        </div>
      </div>
      
      {historyOpen && isManagerOrOwner && (
        <div className="mt-2 text-xs bg-white border border-[#D5E6DA] p-3 rounded-lg">
          <div className="font-bold mb-2">Price History</div>
          {history.length === 0 ? <div className="text-gray-500">No price changes recorded.</div> : (
            <div className="flex flex-col gap-1">
              {history.map(h => (
                <div key={h.id} className="flex justify-between border-b last:border-0 border-gray-100 pb-1">
                  <span>৳{h.old_price} → ৳{h.new_price}</span>
                  <span className="text-gray-500">{new Date(h.changed_at).toLocaleString()} by {h.changed_by_name || 'System'}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function AddItemForm({ categoryId, onAdded }: { categoryId: number, onAdded: () => void }) {
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [description, setDescription] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('Image must be less than 5MB')
        return
      }
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        alert('Only JPG, PNG and WebP are allowed')
        return
      }
      setImageFile(file)
      setImagePreview(URL.createObjectURL(file))
    }
  }

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !price) return
    setAdding(true)
    
    const formData = new FormData()
    formData.append('category', categoryId.toString())
    formData.append('name', name)
    formData.append('description', description)
    formData.append('price', parseFloat(price).toString())
    if (imageFile) {
      formData.append('image', imageFile)
    }

    try {
      await fetchApi('/menu-items/', {
        method: 'POST',
        body: formData
      })
      setName('')
      setPrice('')
      setDescription('')
      setImageFile(null)
      setImagePreview(null)
      onAdded()
    } catch (err: any) {
      alert(err.message || 'Failed to add item')
    } finally {
      setAdding(false)
    }
  }

  return (
    <form onSubmit={handleAdd} className="mt-2 flex flex-col gap-2 text-sm bg-[#F0FAF3] p-3 rounded-xl border border-[#D5E6DA]">
      <div className="font-semibold text-xs text-[#2F855A] mb-1">Add New Item</div>
      <div className="flex gap-2">
        <input required value={name} onChange={e => setName(e.target.value)} placeholder="Item name" className="flex-1 rounded-lg border border-[#D5E6DA] px-2 py-1.5 outline-none" />
        <input required type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} placeholder="Price" className="w-24 rounded-lg border border-[#D5E6DA] px-2 py-1.5 outline-none" />
      </div>
      <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Description (optional)" className="rounded-lg border border-[#D5E6DA] px-2 py-1.5 outline-none" />
      <div className="flex items-center gap-2">
        <label className="cursor-pointer bg-white px-3 py-1.5 border border-[#D5E6DA] rounded-lg text-xs font-semibold hover:bg-gray-50 text-gray-600">
          {imageFile ? 'Change Image' : 'Upload Image'}
          <input type="file" accept="image/jpeg, image/png, image/webp" className="hidden" onChange={handleImageChange} />
        </label>
        {imagePreview && <img src={imagePreview} alt="Preview" className="h-8 w-8 rounded object-cover" />}
      </div>
      <button disabled={adding} type="submit" className="bg-[#94D8AB] text-[#14532D] font-bold py-1.5 rounded-lg mt-1">Add Item</button>
    </form>
  )
}

function EditItemForm({ item, onCancel, onSaved }: { item: any, onCancel: () => void, onSaved: () => void }) {
  const [name, setName] = useState(item.name)
  const [price, setPrice] = useState(item.price)
  const [description, setDescription] = useState(item.description || '')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(getImageUrl(item.image))
  const [saving, setSaving] = useState(false)

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('Image must be less than 5MB')
        return
      }
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        alert('Only JPG, PNG and WebP are allowed')
        return
      }
      setImageFile(file)
      setImagePreview(URL.createObjectURL(file))
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !price) return
    setSaving(true)

    const formData = new FormData()
    formData.append('name', name)
    formData.append('description', description)
    formData.append('price', parseFloat(price).toString())
    if (imageFile) {
      formData.append('image', imageFile)
    }

    try {
      await fetchApi(`/menu-items/${item.id}/`, {
        method: 'PATCH',
        body: formData
      })
      onSaved()
    } catch (err: any) {
      alert(err.message || 'Failed to update item')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Delete this item?')) return
    await fetchApi(`/menu-items/${item.id}/`, { method: 'DELETE' })
    onSaved()
  }

  return (
    <form onSubmit={handleSave} className="flex flex-col gap-2 text-sm bg-white p-3 rounded-xl border border-[#94D8AB] shadow-sm my-2">
      <div className="flex justify-between items-center mb-1">
        <div className="font-semibold text-xs text-[#2F855A]">Edit Item</div>
        <button type="button" onClick={handleDelete} className="text-red-500 text-xs font-bold hover:underline">Delete Item</button>
      </div>
      <div className="flex gap-2">
        <input required value={name} onChange={e => setName(e.target.value)} placeholder="Item name" className="flex-1 rounded-lg border border-[#D5E6DA] px-2 py-1.5 outline-none focus:border-[#94D8AB]" />
        <input required type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} placeholder="Price" className="w-24 rounded-lg border border-[#D5E6DA] px-2 py-1.5 outline-none focus:border-[#94D8AB]" />
      </div>

      <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Description (optional)" className="rounded-lg border border-[#D5E6DA] px-2 py-1.5 outline-none focus:border-[#94D8AB]" />
      <div className="flex items-center gap-2">
        <label className="cursor-pointer bg-gray-50 px-3 py-1.5 border border-[#D5E6DA] rounded-lg text-xs font-semibold hover:bg-gray-100 text-gray-700">
          {imagePreview ? 'Change Image' : 'Upload Image'}
          <input type="file" accept="image/jpeg, image/png, image/webp" className="hidden" onChange={handleImageChange} />
        </label>
        {imagePreview && <img src={imagePreview} alt="Preview" className="h-8 w-8 rounded object-cover" />}
      </div>
      <div className="flex gap-2 mt-1">
        <button type="button" onClick={onCancel} className="flex-1 bg-gray-100 text-gray-700 font-bold py-1.5 rounded-lg">Cancel</button>
        <button disabled={saving} type="submit" className="flex-1 bg-[#94D8AB] text-[#14532D] font-bold py-1.5 rounded-lg">{saving ? 'Saving...' : 'Save Changes'}</button>
      </div>
    </form>
  )
}
