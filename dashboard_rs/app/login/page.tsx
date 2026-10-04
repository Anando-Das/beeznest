'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Utensils, Loader2, ArrowRight } from 'lucide-react'
import { fetchApi } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    setErrorMsg('')

    try {
      const user = await fetchApi('/login/', {
        method: 'POST',
        body: JSON.stringify(formData),
      })
      setStatus('success')
      router.push('/')
    } catch (err: any) {
      setStatus('error')
      setErrorMsg(err.message || 'Invalid credentials. Please try again.')
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const [signedUp, setSignedUp] = useState(false)
  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.search.includes('signedup=1')) {
      setSignedUp(true)
    }
  }, [])

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F0FAF3] p-4 text-[#14532D]">
      <div className="w-full max-w-md rounded-2xl border border-[#D5E6DA] bg-white p-6 shadow-[0_4px_24px_rgba(20,83,45,.08)] sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-xl bg-[#94D8AB] text-[#14532D]">
            <Utensils size={24} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Welcome back</h1>
          <p className="mt-2 text-sm text-[#64748b]">
            Log in to manage your restaurant.
          </p>
        </div>

        {status === 'error' && (
          <div className="mb-6 rounded-xl border border-[#F8C9C4] bg-[#fff8f7] p-4 text-sm text-[#92400E]">
            {errorMsg}
          </div>
        )}
        
        {signedUp && status !== 'error' && (
          <div className="mb-6 rounded-xl border border-[#94D8AB] bg-[#F0FAF3] p-4 text-sm text-[#14532D] font-medium">
            Account and restaurant created successfully. Please log in.
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
              <>Log in <ArrowRight size={18} /></>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[#64748b]">
          Don't have an account?{' '}
          <Link href="/signup" className="font-semibold text-[#2F855A] hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}
