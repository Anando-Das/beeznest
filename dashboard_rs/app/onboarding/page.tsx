'use client'

import { useState } from 'react'
import { Store, MapPin, Loader2, CheckCircle2, ArrowRight } from 'lucide-react'
import { fetchApi } from '@/lib/api'

export default function OnboardingPage() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [formData, setFormData] = useState({ name: '', address: '' })
  const [errors, setErrors] = useState({ name: '', address: '' })

  const validate = () => {
    let isValid = true
    const newErrors = { name: '', address: '' }
    if (!formData.name.trim()) {
      newErrors.name = 'Restaurant name is required.'
      isValid = false
    }
    if (!formData.address.trim()) {
      newErrors.address = 'Address is required.'
      isValid = false
    }
    setErrors(newErrors)
    return isValid
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    setStatus('loading')
    try {
      await fetchApi('/restaurant/onboarding/', {
        method: 'POST',
        body: JSON.stringify(formData),
      })
      setStatus('success')
    } catch (err) {
      setStatus('error')
    }
  }

  if (status === 'success') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F0FAF3] p-4 text-[#14532D]">
        <div className="w-full max-w-md rounded-2xl border border-[#D5E6DA] bg-white p-8 text-center shadow-[0_4px_24px_rgba(20,83,45,.08)]">
          <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-full bg-[#DCF3E3] text-[#2F855A]">
            <CheckCircle2 size={32} />
          </div>
          <h2 className="mb-2 text-2xl font-bold tracking-tight">You're all set!</h2>
          <p className="mb-8 text-sm text-[#64748b]">
            Your restaurant <strong>{formData.name}</strong> has been created successfully.
          </p>
          <button
            onClick={() => window.location.href = '/'}
            className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#94D8AB] px-4 font-bold text-[#14532D] transition-colors hover:bg-[#6BC48C]"
          >
            Go to Dashboard <ArrowRight size={18} />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F0FAF3] p-4 text-[#14532D]">
      <div className="w-full max-w-md rounded-2xl border border-[#D5E6DA] bg-white p-6 shadow-[0_4px_24px_rgba(20,83,45,.08)] sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-xl bg-[#94D8AB] text-[#14532D]">
            <Store size={24} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Set up your restaurant</h1>
          <p className="mt-2 text-sm text-[#64748b]">
            Let's get started by adding your restaurant's basic details.
          </p>
        </div>

        {status === 'error' && (
          <div className="mb-6 rounded-xl border border-[#F8C9C4] bg-[#fff8f7] p-4 text-sm text-[#92400E]">
            Something went wrong while saving your restaurant. Please try again.
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label htmlFor="name" className="mb-1.5 block text-sm font-semibold text-[#14532D]">
              Restaurant Name
            </label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#94a3b8]">
                <Store size={18} />
              </div>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value })
                  if (errors.name) setErrors({ ...errors, name: '' })
                }}
                className={`block w-full rounded-xl border ${errors.name ? 'border-[#F8C9C4] focus:border-[#F8C9C4]' : 'border-[#D5E6DA] focus:border-[#94D8AB]'} bg-[#fbfefc] py-2.5 pl-10 pr-3 text-sm text-[#14532D] outline-none transition-colors focus:ring-4 focus:ring-[#94D8AB]/20`}
                placeholder="e.g. Green Leaf Kitchen"
              />
            </div>
            {errors.name && <p className="mt-1.5 text-xs font-medium text-[#B42318]">{errors.name}</p>}
          </div>

          <div>
            <label htmlFor="address" className="mb-1.5 block text-sm font-semibold text-[#14532D]">
              Address
            </label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#94a3b8]">
                <MapPin size={18} />
              </div>
              <textarea
                id="address"
                rows={3}
                value={formData.address}
                onChange={(e) => {
                  setFormData({ ...formData, address: e.target.value })
                  if (errors.address) setErrors({ ...errors, address: '' })
                }}
                className={`block w-full resize-none rounded-xl border ${errors.address ? 'border-[#F8C9C4] focus:border-[#F8C9C4]' : 'border-[#D5E6DA] focus:border-[#94D8AB]'} bg-[#fbfefc] py-2.5 pl-10 pr-3 text-sm text-[#14532D] outline-none transition-colors focus:ring-4 focus:ring-[#94D8AB]/20`}
                placeholder="Full street address"
              />
            </div>
            {errors.address && <p className="mt-1.5 text-xs font-medium text-[#B42318]">{errors.address}</p>}
          </div>

          <button
            type="submit"
            disabled={status === 'loading'}
            className="mt-2 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#14532D] px-4 font-bold text-white transition-colors hover:bg-[#0f3f22] disabled:opacity-70"
          >
            {status === 'loading' ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Saving...
              </>
            ) : (
              'Complete Setup'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
