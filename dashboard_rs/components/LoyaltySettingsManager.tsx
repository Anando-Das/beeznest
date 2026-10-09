import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, X, Sparkles, Info, Save } from 'lucide-react'

export default function LoyaltySettingsManager() {
  const [settings, setSettings] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [form, setForm] = useState({
    enabled: false,
    points_earning_rate: 100,
    points_redemption_rate: 1,
    points_expiry_days: null as number | null
  })

  const loadSettings = async () => {
    try {
      setError(null)
      const data = await fetchApi('/loyalty-settings/my_settings/')
      setSettings(data)
      setForm({
        enabled: data.enabled,
        points_earning_rate: parseFloat(data.points_earning_rate),
        points_redemption_rate: parseFloat(data.points_redemption_rate),
        points_expiry_days: data.points_expiry_days
      })
    } catch (err: any) {
      setError(err.message || 'Failed to load loyalty settings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSettings()
  }, [])

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    setError(null)
    setSuccess(false)

    try {
      await fetchApi(`/loyalty-settings/${settings.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          enabled: form.enabled,
          points_earning_rate: form.points_earning_rate,
          points_redemption_rate: form.points_redemption_rate,
          points_expiry_days: form.points_expiry_days
        })
      })
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
      await loadSettings()
    } catch (err: any) {
      setError(err.message || 'Failed to save loyalty settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold">Loyalty Points Settings</h1>
        <p className="text-sm text-[#64748b]">Configure your restaurant's loyalty program to reward customers and encourage repeat visits.</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold">✕</button>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-2 rounded-lg text-sm flex justify-between">
          <span>Settings saved successfully!</span>
          <button onClick={() => setSuccess(false)} className="font-bold">✕</button>
        </div>
      )}

      <div className="bg-white p-6 rounded-2xl border border-[#D5E6DA]">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex size-10 items-center justify-center rounded-xl bg-[#DCF3E3] text-[#2F855A]">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Program Status</h2>
            <p className="text-xs text-[#64748b]">Enable or disable the loyalty program</p>
          </div>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#94D8AB] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#2F855A]"></div>
          </label>
          <span className="text-sm font-medium">{form.enabled ? 'Enabled' : 'Disabled'}</span>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-[#64748b] mb-2">
              Points Earning Rate
              <div className="flex items-center gap-1 mt-1 text-xs text-[#94a3b8]">
                <Info size={12} />
                <span>Amount of purchase (in currency) required to earn 1 point</span>
              </div>
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              className="w-full rounded-xl border border-[#D5E6DA] px-4 py-2.5 text-sm focus:border-[#94D8AB] focus:outline-none"
              value={form.points_earning_rate}
              onChange={(e) => setForm({ ...form, points_earning_rate: parseFloat(e.target.value) || 0 })}
              disabled={!form.enabled}
            />
            <p className="mt-1 text-xs text-[#64748b]">
              Example: 100 means customers earn 1 point for every 100 spent
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#64748b] mb-2">
              Points Redemption Rate
              <div className="flex items-center gap-1 mt-1 text-xs text-[#94a3b8]">
                <Info size={12} />
                <span>Currency value of 1 point when redeeming</span>
              </div>
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              className="w-full rounded-xl border border-[#D5E6DA] px-4 py-2.5 text-sm focus:border-[#94D8AB] focus:outline-none"
              value={form.points_redemption_rate}
              onChange={(e) => setForm({ ...form, points_redemption_rate: parseFloat(e.target.value) || 0 })}
              disabled={!form.enabled}
            />
            <p className="mt-1 text-xs text-[#64748b]">
              Example: 1 means 1 point = 1 currency discount
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#64748b] mb-2">
              Points Expiry (Days)
              <div className="flex items-center gap-1 mt-1 text-xs text-[#94a3b8]">
                <Info size={12} />
                <span>Number of days before points expire. Leave empty for no expiry.</span>
              </div>
            </label>
            <input
              type="number"
              min="1"
              className="w-full rounded-xl border border-[#D5E6DA] px-4 py-2.5 text-sm focus:border-[#94D8AB] focus:outline-none"
              value={form.points_expiry_days || ''}
              onChange={(e) => setForm({ ...form, points_expiry_days: e.target.value ? parseInt(e.target.value) : null })}
              disabled={!form.enabled}
              placeholder="No expiry"
            />
            <p className="mt-1 text-xs text-[#64748b]">
              Example: 365 means points expire after 1 year
            </p>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-[#D5E6DA]">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-xl bg-[#94D8AB] px-6 py-2.5 text-sm font-bold text-[#14532D] hover:bg-[#7EC796] disabled:opacity-50"
          >
            <Save size={16} />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>

      <div className="bg-[#DCF3E3] p-6 rounded-2xl border border-[#94D8AB]">
        <h3 className="font-semibold text-[#14532D] mb-2">How it works</h3>
        <ul className="text-sm text-[#2f5d43] space-y-2">
          <li>• Customers earn points when they pay for orders</li>
          <li>• Points can be redeemed for discounts on future orders</li>
          <li>• Points are automatically reversed if orders are cancelled</li>
          <li>• Point expiry runs automatically (if configured)</li>
          <li>• All transactions are tracked for audit purposes</li>
        </ul>
      </div>
    </div>
  )
}
