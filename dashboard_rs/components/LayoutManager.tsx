import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, Plus, Edit, Trash2, Power, Move, Combine, ShieldAlert, X, CalendarDays, Store, Square } from 'lucide-react'

export default function LayoutManager({
  onReserveTable,
}: {
  onReserveTable?: (tableId: number) => void
}) {
  const [tables, setTables] = useState<any[]>([])
  const [zones, setZones] = useState<any[]>([])
  const [layoutObjects, setLayoutObjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeZone, setActiveZone] = useState<number | null>(null)

  const [newZoneName, setNewZoneName] = useState('')
  const [newTableName, setNewTableName] = useState('')
  const [newSeats, setNewSeats] = useState(2)
  const [newShape, setNewShape] = useState('RECTANGLE')
  const [draggingTable, setDraggingTable] = useState<any | null>(null)

  // Layout Object state
  const [newLayoutObjectType, setNewLayoutObjectType] = useState('CASH_COUNTER')
  const [newLayoutObjectName, setNewLayoutObjectName] = useState('')
  const [draggingLayoutObject, setDraggingLayoutObject] = useState<any | null>(null)
  const [layoutObjectEditModal, setLayoutObjectEditModal] = useState<any | null>(null)

  // Modals and State
  const [zoneEditModal, setZoneEditModal] = useState<any | null>(null)
  const [tableEditModal, setTableEditModal] = useState<any | null>(null)
  const [confirmModal, setConfirmModal] = useState<{ title: string, message: string, onConfirm: () => void } | null>(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [userRole, setUserRole] = useState('')
  const [selectedLayoutTable, setSelectedLayoutTable] = useState<any | null>(null)

  const loadData = async () => {
    try {
      const [tablesData, zonesData, me, layoutObjectsData] = await Promise.all([
        fetchApi('/tables/'),
        fetchApi('/zones/'),
        fetchApi('/me/'),
        fetchApi('/layout-objects/').catch(() => [])
      ])
      setTables(tablesData)
      setZones(zonesData)
      setLayoutObjects(layoutObjectsData)
      setUserRole(me.role)
      if (zonesData.length > 0 && activeZone === null) {
        setActiveZone(zonesData[0].id)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const canEditConfig = ['OWNER', 'MANAGER'].includes(userRole)

  const showError = (err: any) => {
    if (err && err.detail) setErrorMsg(err.detail)
    else if (typeof err === 'object') setErrorMsg(Object.values(err).join(' '))
    else setErrorMsg(String(err))
    setTimeout(() => setErrorMsg(''), 5000)
  }

  const addZone = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newZoneName.trim()) return
    try {
      const z = await fetchApi('/zones/', {
        method: 'POST',
        body: JSON.stringify({ name: newZoneName }),
      })
      setNewZoneName('')
      setZones([...zones, z])
      setActiveZone(z.id)
    } catch (err: any) {
      showError(err)
    }
  }

  const updateZone = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!zoneEditModal) return
    try {
      await fetchApi(`/zones/${zoneEditModal.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: zoneEditModal.name,
          is_active: zoneEditModal.is_active
        }),
      })
      setZoneEditModal(null)
      loadData()
    } catch (err: any) {
      showError(err)
    }
  }

  const addTable = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTableName.trim() || !activeZone) return
    try {
      await fetchApi('/tables/', {
        method: 'POST',
        body: JSON.stringify({
          name: newTableName,
          seats: newSeats,
          shape: newShape,
          zone: activeZone,
          position_x: 50,
          position_y: 50,
          is_active: true
        }),
      })
      setNewTableName('')
      loadData()
    } catch (err: any) {
      showError(err)
    }
  }

  const updateTable = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!tableEditModal) return
    try {
      await fetchApi(`/tables/${tableEditModal.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: tableEditModal.name,
          seats: tableEditModal.seats,
          shape: tableEditModal.shape,
          zone: tableEditModal.zone,
          is_active: tableEditModal.is_active
        }),
      })
      setTableEditModal(null)
      loadData()
    } catch (err: any) {
      showError(err)
    }
  }

  const setTableActiveState = async (id: number, isActive: boolean) => {
    const act = async () => {
      try {
        await fetchApi(`/tables/${id}/`, {
          method: 'PATCH',
          body: JSON.stringify({ is_active: isActive })
        })
        loadData()
        setConfirmModal(null)
      } catch (err: any) {
        setConfirmModal(null)
        showError(err)
      }
    }

    if (!isActive) {
      setConfirmModal({
        title: 'Deactivate Table?',
        message: 'This table will remain in history but cannot be used for new operations.',
        onConfirm: act
      })
    } else {
      setConfirmModal({
        title: 'Activate Table?',
        message: 'This table will become available for new orders.',
        onConfirm: act
      })
    }
  }

  const addLayoutObject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newLayoutObjectName.trim() || !activeZone) return
    const payload = {
      object_type: newLayoutObjectType,
      name: newLayoutObjectName,
      zone: activeZone,
      position_x: 50,
      position_y: 50,
      is_active: true
    }
    console.log('POST payload:', payload)
    try {
      const response = await fetchApi('/layout-objects/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      console.log('POST response status: success', response)
      setNewLayoutObjectName('')
      await loadData()
    } catch (err: any) {
      console.error('POST error:', err)
      showError(err)
    }
  }

  const updateLayoutObject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!layoutObjectEditModal) return
    try {
      await fetchApi(`/layout-objects/${layoutObjectEditModal.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: layoutObjectEditModal.name,
          zone: layoutObjectEditModal.zone,
          is_active: layoutObjectEditModal.is_active
        }),
      })
      setLayoutObjectEditModal(null)
      loadData()
    } catch (err: any) {
      showError(err)
    }
  }

  const setLayoutObjectActiveState = async (id: number, isActive: boolean) => {
    const act = async () => {
      try {
        await fetchApi(`/layout-objects/${id}/`, {
          method: 'PATCH',
          body: JSON.stringify({ is_active: isActive })
        })
        loadData()
        setConfirmModal(null)
      } catch (err: any) {
        setConfirmModal(null)
        showError(err)
      }
    }

    if (!isActive) {
      setConfirmModal({
        title: 'Deactivate Object?',
        message: 'This object will remain in history but will not be displayed.',
        onConfirm: act
      })
    } else {
      setConfirmModal({
        title: 'Activate Object?',
        message: 'This object will become visible on the layout.',
        onConfirm: act
      })
    }
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (!canEditConfig) return

    const rect = e.currentTarget.getBoundingClientRect()
    let x = e.clientX - rect.left - 40
    let y = e.clientY - rect.top - 40

    x = Math.max(0, Math.min(x, rect.width - 80))
    y = Math.max(0, Math.min(y, rect.height - 80))

    if (draggingTable) {
      const newTables = tables.map(t =>
        t.id === draggingTable.id ? { ...t, position_x: x, position_y: y } : t
      )
      setTables(newTables)

      try {
        await fetchApi(`/tables/${draggingTable.id}/`, {
          method: 'PATCH',
          body: JSON.stringify({ position_x: x, position_y: y })
        })
      } catch (err: any) {
        showError(err)
        loadData()
      }
      setDraggingTable(null)
    } else if (draggingLayoutObject) {
      const newLayoutObjects = layoutObjects.map(obj =>
        obj.id === draggingLayoutObject.id ? { ...obj, position_x: x, position_y: y } : obj
      )
      setLayoutObjects(newLayoutObjects)

      try {
        await fetchApi(`/layout-objects/${draggingLayoutObject.id}/`, {
          method: 'PATCH',
          body: JSON.stringify({ position_x: x, position_y: y })
        })
      } catch (err: any) {
        showError(err)
        loadData()
      }
      setDraggingLayoutObject(null)
    }
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  const currentZone = zones.find(z => z.id === activeZone)
  const currentZoneTables = tables.filter(t => t.zone === activeZone)
  const currentZoneLayoutObjects = layoutObjects.filter(obj => obj.zone === activeZone)

  return (
    <div className="flex flex-col gap-6 relative">
      {errorMsg && (
        <div className="bg-red-50 text-red-800 p-4 rounded-xl flex items-center justify-between border border-red-200 shadow-sm animate-in fade-in slide-in-from-top-2">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg('')}><X size={18} /></button>
        </div>
      )}

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Table & Zone Configuration</h1>
        <div className="flex gap-2">
          <button disabled className="px-4 py-2 bg-gray-100 border border-[#D5E6DA] rounded-xl flex items-center gap-2 text-gray-400 cursor-not-allowed" title="Available when active orders are implemented.">
            <Move size={16} /> Transfer
          </button>
          <button disabled className="px-4 py-2 bg-gray-100 border border-[#D5E6DA] rounded-xl flex items-center gap-2 text-gray-400 cursor-not-allowed" title="Available when active orders are implemented.">
            <Combine size={16} /> Merge
          </button>
        </div>
      </div>

      <div className="flex gap-4 mb-2 overflow-x-auto items-center">
        {zones.map(z => (
          <div key={z.id} className="flex flex-col items-center">
            <div className="flex">
              <button
                onClick={() => setActiveZone(z.id)}
                className={`px-4 py-2 rounded-l-xl font-bold whitespace-nowrap ${activeZone === z.id ? 'bg-[#94D8AB] text-[#14532D]' : 'bg-white border border-r-0 border-[#D5E6DA] text-gray-600'} ${!z.is_active ? 'opacity-60' : ''}`}
              >
                {z.name} {!z.is_active && '(Inactive)'}
              </button>
              {canEditConfig && (
                <button
                  onClick={() => setZoneEditModal(z)}
                  className={`px-3 py-2 rounded-r-xl border border-l-0 ${activeZone === z.id ? 'bg-[#94D8AB] text-[#14532D] border-[#94D8AB]' : 'bg-white border-[#D5E6DA] text-gray-500'} hover:brightness-95 transition-all`}
                  title="Edit Zone"
                >
                  <Edit size={16} />
                </button>
              )}
            </div>
            <span className="text-[10px] text-gray-500 mt-1">{tables.filter(t => t.zone === z.id).length} Tables · {layoutObjects.filter(obj => obj.zone === z.id).length} Objects</span>
          </div>
        ))}
        {canEditConfig && (
          <form onSubmit={addZone} className="flex items-center ml-2 self-start h-10">
            <input
              value={newZoneName}
              onChange={e => setNewZoneName(e.target.value)}
              placeholder="New Zone Name"
              className="rounded-l-xl border border-gray-300 px-3 py-2 text-sm outline-none w-32 h-full"
            />
            <button className="bg-gray-200 px-3 rounded-r-xl border border-l-0 border-gray-300 h-full"><Plus size={18} /></button>
          </form>
        )}
      </div>

      {activeZone && currentZone && (
        <div className="flex flex-col gap-6">
          <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
            {canEditConfig && (
              <div className="mb-6 border-b border-[#D5E6DA] pb-6">
                <h2 className="text-lg font-semibold mb-4">Add Table to {currentZone.name}</h2>
                <form onSubmit={addTable} className="flex gap-2 flex-wrap">
                  <input required value={newTableName} onChange={e => setNewTableName(e.target.value)} placeholder="Table Name/Number" className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm" />
                  <input required type="number" min={1} value={newSeats} onChange={e => setNewSeats(parseInt(e.target.value))} placeholder="Capacity" className="w-24 rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm" />
                  <select value={newShape} onChange={e => setNewShape(e.target.value)} className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm bg-white">
                    <option value="RECTANGLE">Rectangle</option>
                    <option value="SQUARE">Square</option>
                    <option value="CIRCLE">Circle</option>
                    <option value="OVAL">Oval</option>
                  </select>
                  <button type="submit" disabled={!currentZone.is_active} className="bg-[#94D8AB] px-4 py-2 rounded-xl text-sm font-bold text-[#14532D] disabled:opacity-50">
                    Add Table
                  </button>
                  {!currentZone.is_active && <span className="text-xs text-red-500 self-center ml-2">Cannot add tables to an inactive zone.</span>}
                </form>
              </div>
            )}

            {canEditConfig && (
              <div className="mb-6 border-b border-[#D5E6DA] pb-6">
                <h2 className="text-lg font-semibold mb-4">Add Layout Object to {currentZone.name}</h2>
                <form onSubmit={addLayoutObject} className="flex gap-2 flex-wrap">
                  <select value={newLayoutObjectType} onChange={e => setNewLayoutObjectType(e.target.value)} className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm bg-white">
                    <option value="CASH_COUNTER">Cash Counter</option>
                    <option value="WINDOW">Window</option>
                  </select>
                  <input required value={newLayoutObjectName} onChange={e => setNewLayoutObjectName(e.target.value)} placeholder="Object Name" className="rounded-xl border border-[#D5E6DA] px-3 py-2 text-sm" />
                  <button type="submit" disabled={!currentZone.is_active} className="bg-[#94D8AB] px-4 py-2 rounded-xl text-sm font-bold text-[#14532D] disabled:opacity-50">
                    Add Object
                  </button>
                  {!currentZone.is_active && <span className="text-xs text-red-500 self-center ml-2">Cannot add objects to an inactive zone.</span>}
                </form>
              </div>
            )}

            <div
              className="w-full h-[500px] bg-[#F8FAFC] border-2 border-dashed border-[#CBD5E1] rounded-2xl relative overflow-hidden"
              onDragOver={e => { if (canEditConfig) e.preventDefault() }}
              onDrop={handleDrop}
            >
              {currentZoneLayoutObjects.map(obj => (
                <div
                  key={obj.id}
                  draggable={canEditConfig}
                  onDragStart={() => { if (canEditConfig) setDraggingLayoutObject(obj) }}
                  style={{
                    left: obj.position_x,
                    top: obj.position_y,
                    width: obj.object_type === 'CASH_COUNTER' ? 120 : 100,
                    height: 50,
                  }}
                  className={`absolute flex flex-col items-center justify-center ${canEditConfig ? 'cursor-move' : ''} shadow-md border-2 transition-transform active:scale-95 ${!obj.is_active ? 'bg-gray-100 border-gray-400 opacity-60' : obj.object_type === 'CASH_COUNTER' ? 'bg-[#FEF3C7] border-[#F59E0B]' : 'bg-[#DBEAFE] border-[#3B82F6]'}`}
                  onClick={() => canEditConfig && setLayoutObjectEditModal({ ...obj })}
                >
                  <div className="flex items-center gap-1">
                    {obj.object_type === 'CASH_COUNTER' ? <Store size={14} /> : <Square size={14} />}
                    <div className="font-bold text-xs">{obj.name}</div>
                  </div>
                  <div className="text-[9px] font-bold mt-1 uppercase opacity-75">
                    {!obj.is_active ? 'INACTIVE' : obj.object_type === 'CASH_COUNTER' ? 'COUNTER' : 'WINDOW'}
                  </div>
                </div>
              ))}

              {currentZoneTables.map(t => (
                <div
                  key={t.id}
                  draggable={canEditConfig}
                  onDragStart={() => { if (canEditConfig) setDraggingTable(t) }}
                  style={{
                    left: t.position_x, top: t.position_y,
                    width: t.shape === 'RECTANGLE' || t.shape === 'OVAL' ? 100 : 80,
                    height: 80,
                    borderRadius: t.shape === 'CIRCLE' || t.shape === 'OVAL' ? '50%' : '8px'
                  }}
                  className={`absolute flex flex-col items-center justify-center ${canEditConfig ? 'cursor-move' : ''} shadow-md border-2 transition-transform active:scale-95 ${!t.is_active ? 'bg-gray-100 border-gray-400 opacity-60' : t.operational_status === 'occupied' ? 'bg-amber-50 border-amber-400' : t.operational_status === 'reserved' ? 'bg-blue-50 border-blue-400' : 'bg-white border-[#94D8AB]'}`}
                  onClick={() => setSelectedLayoutTable(t)}
                >
                  <div className="font-bold text-sm">{t.name}</div>
                  <div className="text-xs opacity-75">{t.seats} seats</div>
                  <div className="text-[10px] font-bold mt-1 uppercase">
                    {!t.is_active ? 'INACTIVE' : t.operational_status || t.status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
            <h2 className="text-lg font-semibold mb-4">Table Management</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {currentZoneTables.map(t => (
                <div key={t.id} className={`border rounded-xl p-4 ${t.is_active ? 'border-[#94D8AB] bg-[#F0FAF3]' : 'border-gray-300 bg-gray-50'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-bold text-lg">{t.name}</div>
                    <span className={`text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wider ${t.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'}`}>
                      {t.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mb-4 grid grid-cols-2 gap-y-1">
                    <span>Capacity:</span> <span className="font-semibold">{t.seats} seats</span>
                    <span>Shape:</span> <span className="font-semibold">{t.shape}</span>
                    <span>Zone:</span> <span className="font-semibold">{currentZone.name}</span>
                    <span>State:</span> <span className="font-semibold uppercase">{t.operational_status || t.status}</span>
                  </div>
                  {t.current_reservation && (
                    <div className="mb-3 rounded-lg bg-white border border-[#D5E6DA] p-2 text-xs">
                      <div className="font-semibold">{t.current_reservation.customer_name}</div>
                      <div className="text-[#64748b]">{t.current_reservation.status} · {String(t.current_reservation.start_time).slice(0, 5)}</div>
                    </div>
                  )}
                  <div className="flex gap-2 mb-2">
                    {t.is_active && onReserveTable && (
                      <button onClick={() => onReserveTable(t.id)} className="flex-1 py-1.5 rounded bg-white border border-[#94D8AB] text-sm font-semibold text-[#14532D] hover:bg-[#F0FAF3] flex items-center justify-center gap-1">
                        <CalendarDays size={14} /> Reserve
                      </button>
                    )}
                    {t.current_reservation && (
                      <button onClick={() => setSelectedLayoutTable(t)} className="flex-1 py-1.5 rounded bg-white border border-[#D5E6DA] text-sm font-semibold">Details</button>
                    )}
                  </div>
                  {canEditConfig && (
                    <div className="flex gap-2 border-t border-gray-200 pt-3">
                      <button onClick={() => setTableEditModal({ ...t })} className="flex-1 py-1.5 rounded bg-white border border-gray-300 text-sm font-semibold hover:bg-gray-50">Edit</button>
                      {t.is_active ? (
                        <button onClick={() => setTableActiveState(t.id, false)} className="flex-1 py-1.5 rounded bg-red-50 text-red-700 border border-red-200 text-sm font-semibold hover:bg-red-100">Deactivate</button>
                      ) : (
                        <button onClick={() => setTableActiveState(t.id, true)} className="flex-1 py-1.5 rounded bg-green-50 text-green-700 border border-green-200 text-sm font-semibold hover:bg-green-100">Activate</button>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {currentZoneTables.length === 0 && (
                <div className="col-span-full py-8 text-center text-gray-500">No tables in this zone.</div>
              )}
            </div>
          </div>

          {currentZoneLayoutObjects.length > 0 && (
            <div className="bg-white p-5 rounded-2xl border border-[#D5E6DA]">
              <h2 className="text-lg font-semibold mb-4">Layout Objects</h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {currentZoneLayoutObjects.map(obj => (
                  <div key={obj.id} className={`border rounded-xl p-4 ${obj.is_active ? (obj.object_type === 'CASH_COUNTER' ? 'border-[#F59E0B] bg-[#FEF3C7]' : 'border-[#3B82F6] bg-[#DBEAFE]') : 'border-gray-300 bg-gray-50'}`}>
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-bold text-lg flex items-center gap-2">
                        {obj.object_type === 'CASH_COUNTER' ? <Store size={18} /> : <Square size={18} />}
                        {obj.name}
                      </div>
                      <span className={`text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wider ${obj.is_active ? (obj.object_type === 'CASH_COUNTER' ? 'bg-[#F59E0B] text-white' : 'bg-[#3B82F6] text-white') : 'bg-gray-200 text-gray-700'}`}>
                        {obj.is_active ? obj.object_type === 'CASH_COUNTER' ? 'COUNTER' : 'WINDOW' : 'INACTIVE'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 mb-4 grid grid-cols-2 gap-y-1">
                      <span>Type:</span> <span className="font-semibold">{obj.object_type === 'CASH_COUNTER' ? 'Cash Counter' : 'Window'}</span>
                      <span>Zone:</span> <span className="font-semibold">{currentZone.name}</span>
                      <span>Position:</span> <span className="font-semibold">({Math.round(obj.position_x)}, {Math.round(obj.position_y)})</span>
                    </div>
                    {canEditConfig && (
                      <div className="flex gap-2 border-t border-gray-200 pt-3">
                        <button onClick={() => setLayoutObjectEditModal({ ...obj })} className="flex-1 py-1.5 rounded bg-white border border-gray-300 text-sm font-semibold hover:bg-gray-50">Edit</button>
                        {obj.is_active ? (
                          <button onClick={() => setLayoutObjectActiveState(obj.id, false)} className="flex-1 py-1.5 rounded bg-red-50 text-red-700 border border-red-200 text-sm font-semibold hover:bg-red-100">Deactivate</button>
                        ) : (
                          <button onClick={() => setLayoutObjectActiveState(obj.id, true)} className="flex-1 py-1.5 rounded bg-green-50 text-green-700 border border-green-200 text-sm font-semibold hover:bg-green-100">Activate</button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Zone Edit Modal */}
      {zoneEditModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm">
            <h2 className="text-xl font-bold mb-4">Edit Zone</h2>
            <form onSubmit={updateZone} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-semibold mb-1">Zone Name</label>
                <input required value={zoneEditModal.name} onChange={e => setZoneEditModal({ ...zoneEditModal, name: e.target.value })} className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
              </div>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={zoneEditModal.is_active} onChange={e => setZoneEditModal({ ...zoneEditModal, is_active: e.target.checked })} className="rounded text-[#2F855A]" />
                <span className="text-sm font-semibold">Active Zone</span>
              </label>
              <div className="flex justify-end gap-2 mt-4">
                <button type="button" onClick={() => setZoneEditModal(null)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-[#94D8AB] text-[#14532D] rounded-xl font-bold">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Table Edit Modal */}
      {tableEditModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm">
            <h2 className="text-xl font-bold mb-4">Edit Table</h2>
            <form onSubmit={updateTable} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-semibold mb-1">Table Name/Number</label>
                <input required value={tableEditModal.name} onChange={e => setTableEditModal({ ...tableEditModal, name: e.target.value })} className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Capacity</label>
                <input required type="number" min={1} value={tableEditModal.seats} onChange={e => setTableEditModal({ ...tableEditModal, seats: parseInt(e.target.value) })} className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Shape</label>
                <select value={tableEditModal.shape} onChange={e => setTableEditModal({ ...tableEditModal, shape: e.target.value })} className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2">
                  <option value="RECTANGLE">Rectangle</option>
                  <option value="SQUARE">Square</option>
                  <option value="CIRCLE">Circle</option>
                  <option value="OVAL">Oval</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Zone</label>
                <select value={tableEditModal.zone} onChange={e => setTableEditModal({ ...tableEditModal, zone: parseInt(e.target.value) })} className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2">
                  {zones.map(z => <option key={z.id} value={z.id} disabled={!z.is_active && z.id !== tableEditModal.zone}>{z.name} {!z.is_active && '(Inactive)'}</option>)}
                </select>
              </div>
              <div className="flex justify-end gap-2 mt-4">
                <button type="button" onClick={() => setTableEditModal(null)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-[#94D8AB] text-[#14532D] rounded-xl font-bold">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LayoutObject Edit Modal */}
      {layoutObjectEditModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm">
            <h2 className="text-xl font-bold mb-4">Edit {layoutObjectEditModal.object_type === 'CASH_COUNTER' ? 'Cash Counter' : 'Window'}</h2>
            <form onSubmit={updateLayoutObject} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-semibold mb-1">Name</label>
                <input required value={layoutObjectEditModal.name} onChange={e => setLayoutObjectEditModal({ ...layoutObjectEditModal, name: e.target.value })} className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Zone</label>
                <select value={layoutObjectEditModal.zone} onChange={e => setLayoutObjectEditModal({ ...layoutObjectEditModal, zone: parseInt(e.target.value) })} className="w-full rounded-xl border border-[#D5E6DA] px-3 py-2">
                  {zones.map(z => <option key={z.id} value={z.id} disabled={!z.is_active && z.id !== layoutObjectEditModal.zone}>{z.name} {!z.is_active && '(Inactive)'}</option>)}
                </select>
              </div>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={layoutObjectEditModal.is_active} onChange={e => setLayoutObjectEditModal({ ...layoutObjectEditModal, is_active: e.target.checked })} className="rounded text-[#2F855A]" />
                <span className="text-sm font-semibold">Active</span>
              </label>
              <div className="flex justify-end gap-2 mt-4">
                <button type="button" onClick={() => setLayoutObjectEditModal(null)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-[#94D8AB] text-[#14532D] rounded-xl font-bold">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedLayoutTable && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm">
            <div className="flex justify-between items-start mb-3">
              <h2 className="text-xl font-bold">{selectedLayoutTable.name}</h2>
              <button onClick={() => setSelectedLayoutTable(null)}><X size={18} /></button>
            </div>
            <p className="text-sm text-[#64748b] mb-4">
              {selectedLayoutTable.seats} seats · {currentZone?.name} · {selectedLayoutTable.operational_status || selectedLayoutTable.status}
            </p>
            {selectedLayoutTable.current_reservation ? (
              <div className="rounded-xl border border-[#D5E6DA] p-3 text-sm mb-4">
                <div className="font-semibold">{selectedLayoutTable.current_reservation.customer_name}</div>
                <div className="text-[#64748b]">{selectedLayoutTable.current_reservation.status}</div>
                <div className="text-[#64748b]">{String(selectedLayoutTable.current_reservation.start_time).slice(0, 5)} · {selectedLayoutTable.current_reservation.guest_count} guests</div>
              </div>
            ) : (
              <p className="text-sm text-[#64748b] mb-4">No active reservation for today on this table.</p>
            )}
            <div className="flex justify-end gap-2">
              <button onClick={() => setSelectedLayoutTable(null)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Close</button>
              {selectedLayoutTable.is_active && onReserveTable && (
                <button onClick={() => { const id = selectedLayoutTable.id; setSelectedLayoutTable(null); onReserveTable(id) }} className="px-4 py-2 bg-[#94D8AB] text-[#14532D] rounded-xl font-bold">New reservation</button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm text-center">
            <h2 className="text-xl font-bold mb-2">{confirmModal.title}</h2>
            <p className="text-sm text-gray-600 mb-6">{confirmModal.message}</p>
            <div className="flex justify-center gap-3">
              <button onClick={() => setConfirmModal(null)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Cancel</button>
              <button onClick={confirmModal.onConfirm} className="px-4 py-2 bg-[#14532D] text-white rounded-xl font-bold">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
