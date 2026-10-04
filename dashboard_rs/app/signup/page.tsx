'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Utensils, Loader2, ArrowRight } from 'lucide-react'
import { fetchApi } from '@/lib/api'

export default function SignupPage() {
  const router = useRouter()
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    restaurant_name: '',
    restaurant_address: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    setErrorMsg('')

    try {
      await fetchApi('/signup/', {
        method: 'POST',
        body: JSON.stringify(formData),
      })
      setStatus('success')
      router.push('/login?signedup=1')
    } catch (err: any) {
      setStatus('error')
      setErrorMsg(err.message || 'Something went wrong. Please try again.')
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F0FAF3] p-4 text-[#14532D]">
      <div className="w-full max-w-md rounded-2xl border border-[#D5E6DA] bg-white p-6 shadow-[0_4px_24px_rgba(20,83,45,.08)] sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-xl bg-[#94D8AB] text-[#14532D]">
            <Utensils size={24} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Create your account</h1>
          <p className="mt-2 text-sm text-[#64748b]">
            Start managing your restaurant with RestoCRM.
          </p>
        </div>

        {status === 'error' && (
          <div className="mb-6 rounded-xl border border-[#F8C9C4] bg-[#fff8f7] p-4 text-sm text-[#92400E]">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#14532D]">First Name</label>
              <input
                required
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="block w-full rounded-xl border border-[#D5E6DA] bg-[#fbfefc] py-2.5 px-3 text-sm text-[#14532D] outline-none focus:border-[#94D8AB] focus:ring-4 focus:ring-[#94D8AB]/20 transition-colors"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#14532D]">Last Name</label>
              <input
                required
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="block w-full rounded-xl border border-[#D5E6DA] bg-[#fbfefc] py-2.5 px-3 text-sm text-[#14532D] outline-none focus:border-[#94D8AB] focus:ring-4 focus:ring-[#94D8AB]/20 transition-colors"
              />
            </div>
          </div>
          
          <div>
            <label className="mb-1.5 block text-sm font-semibold text-[#14532D]">Username</label>
            <input
              required
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="block w-full rounded-xl border border-[#D5E6DA] bg-[#fbfefc] py-2.5 px-3 text-sm text-[#14532D] outline-none focus:border-[#94D8AB] focus:ring-4 focus:ring-[#94D8AB]/20 transition-colors"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-semibold text-[#14532D]">Email</label>
            <input
              required
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="block w-full rounded-xl border border-[#D5E6DA] bg-[#fbfefc] py-2.5 px-3 text-sm text-[#14532D] outline-none focus:border-[#94D8AB] focus:ring-4 focus:ring-[#94D8AB]/20 transition-colors"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#14532D]">Restaurant Name</label>
              <input
                required
                name="restaurant_name"
                value={formData.restaurant_name}
                onChange={handleChange}
                placeholder="e.g. Green Leaf Kitchen"
                className="block w-full rounded-xl border border-[#D5E6DA] bg-[#fbfefc] py-2.5 px-3 text-sm text-[#14532D] outline-none focus:border-[#94D8AB] focus:ring-4 focus:ring-[#94D8AB]/20 transition-colors"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#14532D]">Restaurant Address</label>
              <input
                name="restaurant_address"
                value={formData.restaurant_address}
                onChange={handleChange}
                placeholder="Street address"
                className="block w-full rounded-xl border border-[#D5E6DA] bg-[#fbfefc] py-2.5 px-3 text-sm text-[#14532D] outline-none focus:border-[#94D8AB] focus:ring-4 focus:ring-[#94D8AB]/20 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-semibold text-[#14532D]">Password</label>
            <input
              required
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="block w-full rounded-xl border border-[#D5E6DA] bg-[#fbfefc] py-2.5 px-3 text-sm text-[#14532D] outline-none focus:border-[#94D8AB] focus:ring-4 focus:ring-[#94D8AB]/20 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={status === 'loading'}
            className="mt-2 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#14532D] px-4 font-bold text-white transition-colors hover:bg-[#0f3f22] disabled:opacity-70"
          >
            {status === 'loading' ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <>Create account <ArrowRight size={18} /></>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[#64748b]">
          Already have an account?{' '}
          <Link href="/login" className="font-semibold text-[#2F855A] hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
