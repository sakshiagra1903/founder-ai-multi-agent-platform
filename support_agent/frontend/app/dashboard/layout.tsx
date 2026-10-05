'use client';

import { useAuth } from '@/hooks/use-auth';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout, isLoading } = useAuth();
  const pathname = usePathname();

  if (isLoading) {
    return (
      <div className="flex flex-1 min-h-screen items-center justify-center bg-slate-50 text-slate-800">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          <p className="text-xs text-slate-500">Loading Founder OS...</p>
        </div>
      </div>
    );
  }

  // Active navigation helper
  const isActive = (path: string) => pathname === path;

  return (
    <div className="flex flex-1 min-h-screen bg-slate-50 text-slate-900 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col z-20 shrink-0">
        {/* Brand */}
        <div className="p-6 border-b border-slate-200 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-md">
            F
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-sm text-slate-900 leading-tight">Founder AI</span>
            <span className="text-[10px] text-indigo-600 font-semibold tracking-wider uppercase">Support OS</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-1.5">
          <Link
            href="/dashboard/chat"
            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
              isActive('/dashboard/chat')
                ? 'bg-indigo-50 text-indigo-700 border-l-2 border-indigo-500'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span className="text-base">💬</span>
            Chat Assistant
          </Link>
          <Link
            href="/dashboard/documents"
            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
              isActive('/dashboard/documents')
                ? 'bg-indigo-50 text-indigo-700 border-l-2 border-indigo-500'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span className="text-base">📂</span>
            Knowledge Base
          </Link>
        </nav>

        {/* User Footer Profile */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center font-bold text-slate-800 text-sm border border-slate-200">
              {user?.name ? user.name[0].toUpperCase() : 'U'}
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-semibold text-slate-800 truncate">{user?.name}</span>
              <span className="text-[10px] text-slate-500 truncate">{user?.email}</span>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full text-left py-2 px-3 hover:bg-red-500/10 rounded-lg text-xs font-medium text-red-600 hover:text-red-700 transition-colors flex items-center gap-2 cursor-pointer"
          >
            <span>🚪</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md px-6 flex items-center justify-between z-10">
          <h1 className="font-bold text-base text-slate-900">
            {isActive('/dashboard/chat') ? 'AI Assistant' : 'Knowledge Base'}
          </h1>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Agent Online
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto relative flex flex-col bg-slate-50">
          {children}
        </main>
      </div>
    </div>
  );
}
