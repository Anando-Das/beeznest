'use client'

import { useMemo, useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { fetchApi } from '@/lib/api'
import MenuManager from '@/components/MenuManager'
import LayoutManager from '@/components/LayoutManager'
import SalesManager from '@/components/SalesManager'
import OrdersManager from '@/components/OrdersManager'
import KitchenManager from '@/components/KitchenManager'
import CustomersManager from '@/components/CustomersManager'
import StaffManager from '@/components/StaffManager'
import ExpensesManager from '@/components/ExpensesManager'
import DayCloseManager from '@/components/DayCloseManager'
import ReportsManager from '@/components/ReportsManager'
import ReservationManager from '@/components/ReservationManager'
import LoyaltySettingsManager from '@/components/LoyaltySettingsManager'
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, BookOpen, Boxes, BriefcaseBusiness,
  CalendarDays, Check, ChevronDown, CircleDollarSign, Clock3, Coffee, Contact, CreditCard, Crown,
  FileBarChart, Flame, Grid2X2, HelpCircle, Home, LayoutDashboard, Menu, MessageSquare, MoreHorizontal,
  Package, PanelLeft, Plus, QrCode, ReceiptText, Search, Settings, ShoppingBag, ShoppingCart, Sparkles,
  Store, Table2, Tag, TrendingUp, Users, Utensils, WalletCards, X, Zap, Lock
} from 'lucide-react'

const green = '#2F855A'
const nav: { group: string, items: [string, string, any][] }[] = [
  { group: 'Overview', items: [['Dashboard', '/dashboard', LayoutDashboard], ['Sales', '/sales', ShoppingCart], ['Orders', '/orders', ReceiptText], ['Kitchen', '/kitchen', Utensils]] },
  { group: 'Manage', items: [['Menu', '/menu', Utensils], ['Layout', '/layout', Grid2X2], ['Reservations', '/reservations', CalendarDays], ['Customers', '/customers', Users], ['Staff', '/staff', Contact], ['Loyalty', '/loyalty', Sparkles]] },
  { group: 'Grow', items: [['Marketing', '/marketing', MessageSquare], ['Upsell', '/upsell', Zap], ['QR Ordering', '/qr-ordering', QrCode], ['Website', '/website', Store], ['AI Manager', '/ai', Sparkles]] },
  { group: 'Money', items: [['Reports', '/reports', FileBarChart], ['Expenses', '/expenses', WalletCards], ['Day Close', '/day-close', CircleDollarSign]] },
]
const stats: [string, string, string, any][] = [
  ['Today’s sales', 'BDT 24,500', '+12.8% vs last week', TrendingUp], ['Orders', '38', '+8 orders today', ShoppingBag], ['Avg order', 'BDT 645', '+5.4% vs last week', ReceiptText], ['Open tables', '6 / 20', '4 tables free', Table2]
]
const orders: [string, string, string, string][] = [['#1042', 'Table 5', 'BDT 1,250', 'Paid'], ['#1043', 'Takeaway', 'BDT 480', 'Open'], ['#1044', 'Table 2', 'BDT 890', 'Served'], ['#1045', 'Table 8', 'BDT 1,640', 'Paid'], ['#1046', 'Delivery', 'BDT 720', 'Preparing']]
const items: [string, number, number][] = [['Chicken burger', 12, 75], ['Beef biryani', 9, 58], ['Cold coffee', 8, 44], ['Fries', 7, 36], ['Pasta Alfredo', 5, 28]]
const tables: { id: string, status: string, seats: number, total: string }[] = [{ id: 'T1', status: 'free', seats: 2, total: '-' }, { id: 'T2', status: 'occupied', seats: 4, total: 'BDT 1,240' }, { id: 'T3', status: 'free', seats: 4, total: '-' }, { id: 'T4', status: 'bill', seats: 6, total: 'BDT 2,180' }, { id: 'T5', status: 'occupied', seats: 4, total: 'BDT 1,250' }, { id: 'T6', status: 'reserved', seats: 2, total: '-' }, { id: 'T7', status: 'free', seats: 4, total: '-' }, { id: 'T8', status: 'occupied', seats: 8, total: 'BDT 1,640' }, { id: 'T9', status: 'free', seats: 2, total: '-' }, { id: 'T10', status: 'free', seats: 4, total: '-' }]

function cn(...classes: (string | false | undefined)[]) { return classes.filter(Boolean).join(' ') }
function money(value: string) { return value.replace('BDT ', '৳') }

export default function Page() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  const [path, setPath] = useState('/dashboard')
  const [role, setRole] = useState('Owner')
  const [prefillTableId, setPrefillTableId] = useState<number | null>(null)
  const [lang, setLang] = useState('EN')
  const [mobileNav, setMobileNav] = useState(false)

  useEffect(() => {
    fetchApi('/me/')
      .then(data => {
        setUser(data)
        setRole(data.role || '')
        setLoading(false)
      })
      .catch(() => {
        router.push('/login')
      })
  }, [router])
  const [selectedTable, setSelectedTable] = useState('T5')
  const [orderOpen, setOrderOpen] = useState(false)
  const current = nav.flatMap((g) => g.items).find((item) => item[1] === path)
  const title = current?.[0] || 'Dashboard'
  const canSee = (label: string) => {
    if (!role) return false;
    const p: Record<string, string[]> = {
      OWNER: ['Dashboard', 'Sales', 'Orders', 'Kitchen', 'Menu', 'Layout', 'Reservations', 'Customers', 'Staff', 'Loyalty', 'Marketing', 'Upsell', 'QR Ordering', 'Website', 'AI Manager', 'Reports', 'Expenses', 'Day Close'],
      MANAGER: ['Dashboard', 'Sales', 'Orders', 'Kitchen', 'Menu', 'Layout', 'Reservations', 'Customers', 'Staff', 'Loyalty', 'Marketing', 'Upsell', 'QR Ordering', 'Website', 'AI Manager', 'Reports', 'Expenses', 'Day Close'],
      CASHIER: ['Dashboard', 'Sales', 'Orders', 'Customers', 'Reservations'],
      WAITER: ['Dashboard', 'Sales', 'Orders', 'Customers', 'Reservations'],
      KITCHEN: ['Dashboard', 'Kitchen', 'Menu']
    };
    return p[role]?.includes(label) || false;
  }
  const go = (next: string) => { setPath(next); setMobileNav(false) }

  if (loading) return <div className="flex h-screen items-center justify-center text-[#14532D]">Loading...</div>

  if (user && (!user.restaurant || !user.role)) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#F0FAF3] p-4 text-center text-[#14532D]">
        <h1 className="text-2xl font-bold tracking-tight">Pending Assignment</h1>
        <p className="mt-2 mb-6 text-sm text-[#64748b]">Your account is waiting to be assigned to a restaurant.</p>
        <button onClick={async () => { await fetchApi('/logout/', { method: 'POST' }); router.push('/login'); }} className="rounded-xl bg-[#14532D] px-6 py-2.5 font-bold text-white hover:bg-[#0f3f22]">
          Log out
        </button>
      </div>
    )
  }

  return <div className="min-h-screen bg-[#fbfefc] text-[#14532D]">
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-[#D5E6DA] bg-[#F0FAF3] lg:flex print:hidden">
      <div className="flex h-20 items-center gap-3 border-b border-[#D5E6DA] px-5"><div className="flex size-10 items-center justify-center rounded-xl bg-[#94D8AB] text-[#14532D]"><Utensils size={20} /></div><div><div className="font-bold tracking-tight">RestoCRM</div><div className="text-xs text-[#475569]">{user?.restaurant ? 'Restaurant ID: ' + user.restaurant : 'No Restaurant'}</div></div></div>
      <div className="flex-1 overflow-y-auto px-3 py-5">{nav.map((group) => <div key={group.group} className="mb-6"><div className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[.16em] text-[#6b8b76]">{group.group}</div><div className="flex flex-col gap-1">{group.items.map(([label, href, Icon]) => {
        const allowed = canSee(label as string);
        return <button key={href as string} onClick={() => { if (allowed) go(href as string); else alert("You don't have permission to access this feature."); }} className={cn('flex min-h-11 items-center gap-3 rounded-xl px-3 text-left text-sm font-medium transition-colors', path === href ? 'bg-[#94D8AB] text-[#14532D]' : allowed ? 'text-[#475569] hover:bg-[#DCF3E3]' : 'text-[#94a3b8] opacity-60')}><Icon size={18} /><span>{label}</span>{!allowed && <Lock size={14} className="ml-auto" />}</button>
      })}</div></div>)}</div>
      <div className="border-t border-[#D5E6DA] p-3"><button className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm text-[#475569] hover:bg-[#DCF3E3]"><Settings size={18} />Settings</button><button className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm text-[#475569] hover:bg-[#DCF3E3]"><HelpCircle size={18} />Help & support</button></div>
    </aside>
    <header className="fixed inset-x-0 top-0 z-20 flex h-16 items-center justify-between border-b border-[#D5E6DA] bg-white/95 px-4 backdrop-blur lg:left-60 lg:px-8 print:hidden"><div className="flex items-center gap-3"><button onClick={() => setMobileNav(true)} className="rounded-xl p-2 hover:bg-[#F0FAF3] lg:hidden"><Menu size={21} /></button><div><div className="text-sm font-semibold">{title}</div><div className="hidden text-xs text-[#64748b] sm:block">{user?.restaurant ? 'Restaurant ID: ' + user.restaurant : 'No Restaurant'} <span className="mx-1">/</span> {title}</div></div></div><div className="hidden max-w-sm flex-1 px-8 md:block"><div className="flex h-10 items-center gap-2 rounded-xl border border-[#D5E6DA] bg-[#fbfefc] px-3 text-sm text-[#94a3b8]"><Search size={17} /> Search orders, customers, menu <kbd className="ml-auto rounded border px-1.5 py-0.5 text-[10px]">/</kbd></div></div><div className="flex items-center gap-2 sm:gap-3"><button onClick={() => setLang(lang === 'EN' ? 'BN' : 'EN')} className="hidden rounded-lg px-2 py-1 text-xs font-bold text-[#2F855A] hover:bg-[#F0FAF3] sm:block">{lang === 'EN' ? 'EN · BN' : 'BN · EN'}</button><div className="hidden items-center gap-2 rounded-full bg-[#DCF3E3] px-3 py-1.5 text-xs font-semibold text-[#2F855A] sm:flex"><span className="size-2 rounded-full bg-[#2F855A]" /> Day open · 10:05</div><button className="relative rounded-xl p-2 hover:bg-[#F0FAF3]"><Bell size={19} /><span className="absolute right-1 top-1 size-2 rounded-full bg-[#B42318]" /></button><button onClick={async () => { await fetchApi('/logout/', { method: 'POST' }); router.push('/login'); }} className="flex size-9 items-center justify-center rounded-full bg-[#14532D] text-sm font-bold text-white" title="Logout">{role[0]}</button></div></header>
    <main className="min-h-screen pt-16 lg:pl-60 print:pt-0 print:pl-0">
      <div className="mx-auto max-w-[1500px] p-4 pb-24 sm:p-6 lg:p-8 print:p-0">
        {path === '/dashboard' && (canSee('Dashboard') ? <Dashboard go={go} user={user} /> : <LockedView />)}
        {path === '/sales' && (canSee('Sales') ? <SalesManager /> : <LockedView />)}
        {path === '/orders' && (canSee('Orders') ? <OrdersManager /> : <LockedView />)}
        {path === '/kitchen' && (canSee('Kitchen') ? <KitchenManager /> : <LockedView />)}
        {path === '/menu' && (canSee('Menu') ? <MenuManager /> : <LockedView />)}
        {path === '/layout' && (canSee('Layout') ? <LayoutManager onReserveTable={(id) => { setPrefillTableId(id); go('/reservations') }} /> : <LockedView />)}
        {path === '/reservations' && (canSee('Reservations') ? <ReservationManager userRole={role} prefillTableId={prefillTableId} onPrefillConsumed={() => setPrefillTableId(null)} /> : <LockedView />)}
        {path === '/customers' && (canSee('Customers') ? <CustomersManager /> : <LockedView />)}
        {path === '/staff' && (canSee('Staff') ? <StaffManager userRole={role} /> : <LockedView />)}
        {path === '/loyalty' && (canSee('Loyalty') ? <LoyaltySettingsManager /> : <LockedView />)}
        {path === '/expenses' && (canSee('Expenses') ? <ExpensesManager /> : <LockedView />)}
        {path === '/day-close' && (canSee('Day Close') ? <DayCloseManager /> : <LockedView />)}
        {path === '/reports' && (canSee('Reports') ? <ReportsManager /> : <LockedView />)}
        {!['/dashboard', '/sales', '/orders', '/kitchen', '/menu', '/layout', '/reservations', '/customers', '/staff', '/loyalty', '/expenses', '/day-close', '/reports'].includes(path) && <Placeholder title={title} path={path} go={go} />}
      </div>
    </main>
    <nav className="fixed inset-x-0 bottom-0 z-20 flex h-16 items-center justify-around border-t border-[#D5E6DA] bg-white lg:hidden print:hidden">{([['Sales', '/sales', ShoppingCart], ['Orders', '/orders', ReceiptText], ['Kitchen', '/kitchen', Utensils], ['Dashboard', '/dashboard', Home], ['More', '/more', MoreHorizontal]] as [string, string, any][]).map(([label, href, Icon]) => {
      const allowed = href === '/more' || canSee(label as string);
      return <button key={label as string} onClick={() => { if (!allowed) { alert("You don't have permission to access this feature."); return; }; href === '/more' ? setMobileNav(true) : go(href as string); }} className={cn('flex min-w-14 flex-col items-center gap-1 text-[10px] font-semibold relative', path === href ? 'text-[#2F855A]' : allowed ? 'text-[#64748b]' : 'text-[#94a3b8] opacity-50')}><Icon size={19} />{label}{!allowed && <Lock size={10} className="absolute top-0 right-2" />}</button>
    })}</nav>
    {mobileNav && <div className="fixed inset-0 z-40 bg-[#14532D]/20 lg:hidden" onClick={() => setMobileNav(false)}><div className="absolute inset-y-0 left-0 w-[86%] max-w-80 overflow-y-auto bg-[#F0FAF3] p-5" onClick={(e) => e.stopPropagation()}><div className="mb-6 flex items-center justify-between"><div className="font-bold">RestoCRM</div><button onClick={() => setMobileNav(false)}><X size={20} /></button></div>{nav.map((group) => <div key={group.group} className="mb-5"><div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#6b8b76]">{group.group}</div>{group.items.map(([label, href, Icon]) => {
      const allowed = canSee(label as string);
      return <button key={href as string} onClick={() => { if (allowed) go(href as string); else alert("You don't have permission to access this feature."); }} className={cn('flex min-h-12 w-full items-center gap-3 rounded-xl px-3 text-sm', path === href && 'bg-[#94D8AB] font-semibold', !allowed && 'opacity-50 text-[#94a3b8]')}><Icon size={18} />{label}{!allowed && <Lock size={14} className="ml-auto" />}</button>
    })}</div>)}</div></div>}
  </div>
}

function Dashboard({ go, user }: { go: (path: string) => void, user?: any }) {
  const [metric, setMetric] = useState('Sales')
  return <div className="flex flex-col gap-6"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="mb-1 text-sm text-[#64748b]">Tuesday, October 4, 2026</p><h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Good morning, {user?.first_name || 'Owner'}</h1><p className="mt-1 text-sm text-[#64748b]">Here’s what’s happening at your restaurant today.</p></div><div className="flex gap-2"><button className="flex min-h-11 items-center gap-2 rounded-xl border border-[#94D8AB] bg-white px-3 text-sm font-semibold"><CalendarDays size={16} /> Today <ChevronDown size={15} /></button><button onClick={() => go('/sales')} className="flex min-h-11 items-center gap-2 rounded-xl bg-[#94D8AB] px-4 text-sm font-bold text-[#14532D] shadow-sm hover:bg-[#6BC48C]"><Plus size={18} /> New order</button></div></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{stats.map(([label, value, trend, Icon], i) => <div key={label as string} className="rounded-2xl border border-[#D5E6DA] bg-white p-5 shadow-[0_4px_16px_rgba(20,83,45,.04)]"><div className="flex items-start justify-between"><p className="text-sm font-medium text-[#64748b]">{label}</p><div className="flex size-10 items-center justify-center rounded-xl bg-[#DCF3E3] text-[#2F855A]"><Icon size={19} /></div></div><p className="mt-3 text-[28px] font-semibold tracking-tight">{value}</p><p className={cn('mt-1 flex items-center gap-1 text-xs font-semibold', i === 3 ? 'text-[#64748b]' : 'text-[#2F855A]')}>{i !== 3 && <ArrowUpRight size={13} />} {trend}</p></div>)}</div>
    <div className="grid gap-6 xl:grid-cols-[1.7fr_1fr]"><section className="rounded-2xl border border-[#D5E6DA] bg-white p-5"><div className="mb-5 flex items-center justify-between"><div><h2 className="text-lg font-semibold">Sales this week</h2><p className="text-xs text-[#64748b]">Performance across the last 7 days</p></div><div className="flex rounded-xl bg-[#F0FAF3] p-1">{['Sales', 'Orders'].map((tab) => <button key={tab} onClick={() => setMetric(tab)} className={cn('rounded-lg px-3 py-1.5 text-xs font-semibold', metric === tab ? 'bg-white text-[#14532D] shadow-sm' : 'text-[#64748b]')}>{tab}</button>)}</div></div><div className="flex h-56 items-end gap-2 border-b border-[#D5E6DA] px-2 sm:gap-5">{[54, 62, 48, 76, 68, 88, 70].map((height, i) => <div key={i} className="flex flex-1 flex-col items-center gap-2"><div className="w-full max-w-12 rounded-t-lg bg-[#94D8AB] transition-all hover:bg-[#2F855A]" style={{ height: `${height}%` }} title={`${metric}: ${height * 300}`} /><span className="text-[11px] text-[#64748b]">{['Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', 'Tue'][i]}</span></div>)}</div><div className="mt-4 flex items-center justify-between text-xs text-[#64748b]"><span>BDT 0</span><span>BDT 30,000</span></div></section><section className="rounded-2xl border border-[#D5E6DA] bg-[#DCF3E3] p-5"><div className="flex items-start justify-between"><div className="flex size-10 items-center justify-center rounded-xl bg-white text-[#2F855A]"><Sparkles size={20} /></div><span className="rounded-full bg-white/70 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-[#2F855A]">AI insight</span></div><h2 className="mt-5 text-lg font-semibold">A useful tip for Tuesday</h2><p className="mt-2 text-sm leading-6 text-[#2f5d43]">Tuesday is slow between 3–6 pm. Try a combo offer with a cold drink to lift afternoon orders.</p><div className="mt-5 flex gap-2"><button className="min-h-10 rounded-xl bg-[#94D8AB] px-4 text-sm font-bold text-[#14532D]">Ask AI</button><button className="min-h-10 rounded-xl px-4 text-sm font-semibold text-[#2F855A] hover:bg-white/60">Dismiss</button></div></section></div>
    <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3"><Card title="Top items today" action="See profit per item"><div className="flex flex-col gap-4">{items.map(([name, count, width]) => <div key={name as string}><div className="mb-1 flex justify-between text-sm"><span>{name}</span><span className="font-semibold">×{count}</span></div><div className="h-2 rounded-full bg-[#F0FAF3]"><div className="h-2 rounded-full bg-[#6BC48C]" style={{ width: `${width}%` }} /></div></div>)}</div></Card><Card title="Recent orders" action="View all"><div className="flex flex-col">{orders.slice(0, 5).map(([id, table, amount, status]) => <div key={id} className="flex min-h-12 items-center justify-between border-b border-[#F0FAF3] last:border-0"><div><div className="text-sm font-semibold">{id}</div><div className="text-xs text-[#64748b]">{table}</div></div><div className="text-right"><div className="text-sm font-semibold">{money(amount)}</div><Status text={status} /></div></div>)}</div></Card><Card title="Alerts"><div className="flex flex-col gap-3">{([['3 items low in stock', Package, 'warn'], ['2 customers to win back', Users, 'info'], ['Cash mismatch: yesterday', AlertTriangle, 'danger'], ['4 QR orders waiting', QrCode, 'success']] as [string, any, string][]).map(([text, Icon, type]) => <div key={text as string} className="flex items-center gap-3 rounded-xl bg-[#fbfefc] p-2.5"><div className="text-[#2F855A]"><Icon size={18} /></div><span className="text-sm">{text}</span><ChevronDown size={15} className="ml-auto -rotate-90 text-[#94a3b8]" /></div>)}</div></Card></div>
    <div className="grid gap-6 lg:grid-cols-2"><Card title="Busiest hours" action="Today"><div className="flex h-40 items-end gap-3 border-b border-[#D5E6DA] px-2">{[20, 38, 55, 80, 65, 42, 34, 50, 72, 48].map((h, i) => <div key={i} className="flex flex-1 flex-col items-center gap-2"><div className="w-full rounded-t bg-[#BDE8CB]" style={{ height: `${h}%` }} /><span className="text-[10px] text-[#64748b]">{i + 11}</span></div>)}</div></Card><Card title="Payment methods"><div className="flex items-center gap-8"><div className="relative flex size-36 shrink-0 items-center justify-center rounded-full" style={{ background: 'conic-gradient(#2F855A 0 45%, #6BC48C 45% 70%, #BDE8CB 70% 88%, #DCF3E3 88% 100%)' }}><div className="flex size-24 items-center justify-center rounded-full bg-white text-center"><div><div className="text-lg font-bold">৳24.5k</div><div className="text-[10px] text-[#64748b]">total paid</div></div></div></div><div className="grid gap-3 text-sm">{([['Cash', '#2F855A', '45%'], ['bKash', '#6BC48C', '25%'], ['Nagad', '#BDE8CB', '18%'], ['Card', '#DCF3E3', '12%']] as [string, string, string][]).map(([name, color, value]) => <div key={name} className="flex items-center gap-2"><span className="size-2.5 rounded-full" style={{ background: color }} /><span>{name}</span><b className="ml-auto">{value}</b></div>)}</div></div></Card></div>
  </div>
}
function Card({ title, action, children }: { title: string, action?: string, children: React.ReactNode }) { return <section className="rounded-2xl border border-[#D5E6DA] bg-white p-5"><div className="mb-5 flex items-center justify-between"><h2 className="text-lg font-semibold">{title}</h2>{action && <button className="text-xs font-bold text-[#2F855A]">{action}</button>}</div>{children}</section> }
function Status({ text }: { text: string }) { const type = text === 'Paid' || text === 'Served' ? 'success' : text === 'Open' ? 'warn' : 'info'; return <span className={cn('inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold', type === 'success' && 'bg-[#DCF3E3] text-[#2F855A]', type === 'warn' && 'bg-[#FBE3B5] text-[#92400E]', type === 'info' && 'bg-[#CFE0F7] text-[#1E40AF]')}>{text}</span> }

function Placeholder({ title, path, go }: { title: string; path: string; go: (p: string) => void }) { const meta: Record<string, [string, string]> = { '/orders': ['Review every order, payment and refund in one place.', 'Filter by status, order type, payment method and staff member.'], '/kitchen': ['Live kitchen tickets', 'Keep service moving with clear New, Preparing and Ready lanes.'], '/menu': ['Menu management', 'Manage categories, pricing, costs and availability.'], '/customers': ['Customers', 'Build loyalty with visit history, points and useful segments.'], '/reports': ['Reports', 'Sales, profit per item, hours and customer insights.'], '/layout': ['Layout designer', 'Create a floor plan that powers table service and QR ordering.'], '/ai': ['AI Manager', 'Ask plain-language questions about your restaurant.'], '/expenses': ['Expenses & day close', 'Track expenses and reconcile today’s cash.'] }; const [heading, description] = meta[path] || [title, 'Everything you need to run Green Leaf Kitchen with clarity.']; return <div className="flex min-h-[70vh] flex-col items-center justify-center rounded-2xl border border-dashed border-[#BDE8CB] bg-white p-8 text-center"><div className="mb-5 flex size-16 items-center justify-center rounded-2xl bg-[#DCF3E3] text-[#2F855A]"><Sparkles size={28} /></div><h1 className="text-2xl font-semibold">{heading}</h1><p className="mt-2 max-w-md text-sm leading-6 text-[#64748b]">{description}</p><button onClick={() => go('/dashboard')} className="mt-6 min-h-11 rounded-xl bg-[#94D8AB] px-5 text-sm font-bold text-[#14532D]">Back to dashboard</button></div> }

function LockedView() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center rounded-2xl border border-[#D5E6DA] bg-white p-8 text-center text-[#14532D]">
      <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-[#f1f5f9] text-[#64748b]">
        <Lock size={32} />
      </div>
      <h2 className="text-xl font-semibold">Access Restricted</h2>
      <p className="mt-2 text-sm text-[#64748b]">You don't have permission to access this feature.</p>
    </div>
  )
}
