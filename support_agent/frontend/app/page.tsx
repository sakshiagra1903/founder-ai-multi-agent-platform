import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex flex-col flex-1 bg-slate-50 text-slate-900 overflow-hidden relative">
      {/* Decorative Blur Spheres */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-violet-600/10 blur-[120px] pointer-events-none" />

      {/* Navigation Header */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between border-b border-slate-200 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            F
          </div>
          <span className="text-xl font-bold text-slate-900">
            Founder AI
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors px-4 py-2"
          >
            Login
          </Link>
          <Link
            href="/signup"
            className="text-sm font-medium bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white px-5 py-2.5 rounded-xl transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/20 hover:scale-[1.02]"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Main Landing Area */}
      <main className="flex-1 flex flex-col justify-center items-center max-w-7xl mx-auto px-6 py-20 relative z-10">
        <div className="text-center max-w-3xl flex flex-col items-center">
          {/* Tag */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass-panel border border-slate-200 text-xs font-semibold text-indigo-700 mb-8 animate-fade-in">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
            Support Agent Subsystem v1.0
          </div>

          {/* Heading */}
          <h1 className="text-5xl md:text-6xl font-black tracking-tight leading-[1.1] mb-6 text-slate-900 animate-fade-in">
            Your Startup's Knowledge,<br />Powered by <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">Local RAG</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg text-slate-500 leading-relaxed mb-10 max-w-2xl animate-fade-in">
            Store your company's guidelines, product docs, and pitch decks. Query details instantly, check precise source pages, and manage startup intelligence with absolute data privacy.
          </p>

          {/* Call to Actions */}
          <div className="flex flex-col sm:flex-row gap-4 mb-20 animate-fade-in">
            <Link
              href="/signup"
              className="px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-semibold shadow-xl shadow-indigo-500/20 hover:scale-[1.03] transition-all"
            >
              Build Your Knowledge Base
            </Link>
            <Link
              href="/login"
              className="px-8 py-4 rounded-2xl glass-card border border-slate-200 hover:bg-slate-100 font-semibold text-slate-800 transition-all"
            >
              Sign In to Chat
            </Link>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl">
          <div className="glass-card p-8 rounded-2xl text-left">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-600 mb-6 text-xl">
              📂
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Upload PDF Docs</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              Drag-and-drop capability for user PDFs. Automatically extracts, segments, and processes textual information.
            </p>
          </div>

          <div className="glass-card p-8 rounded-2xl text-left">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-600 mb-6 text-xl">
              ⚡
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">High-Precision RAG</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              Fetches relevant information via local FAISS index. Answers strictly on context to guarantee zero hallucinations.
            </p>
          </div>

          <div className="glass-card p-8 rounded-2xl text-left">
            <div className="w-12 h-12 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-600 mb-6 text-xl">
              📍
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Page-Level Citations</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              Provides direct file references and exact page numbers for every answer, giving founders full tracking capabilities.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full max-w-7xl mx-auto px-6 py-8 text-center text-xs text-slate-500 border-t border-slate-200 relative z-10">
        &copy; 2026 Founder AI Assistant. Built for startup operating systems. All rights reserved.
      </footer>
    </div>
  );
}
