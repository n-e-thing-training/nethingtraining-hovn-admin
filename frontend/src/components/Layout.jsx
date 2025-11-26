// frontend/src/components/Layout.jsx
import React from "react";
import { NavLink } from "react-router-dom";

const navLinkBase =
  "block px-4 py-2 rounded-md text-sm font-medium transition-colors";
const navLinkActive = "bg-sky-500/20 text-sky-300";
const navLinkInactive = "text-slate-300 hover:bg-slate-700/60";

function Layout({ children }) {
  return (
    <div className="h-screen bg-slate-950 text-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="px-4 py-4 border-b border-slate-800">
          <div className="text-xs uppercase tracking-wide text-sky-400 font-semibold">
            n.e. thing training
          </div>
          <div className="text-[11px] text-slate-400">HOVN Admin Dashboard</div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `${navLinkBase} ${isActive ? navLinkActive : navLinkInactive}`
            }
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/bookings"
            className={({ isActive }) =>
              `${navLinkBase} ${isActive ? navLinkActive : navLinkInactive}`
            }
          >
            Bookings
          </NavLink>

          <NavLink
            to="/students"
            className={({ isActive }) =>
              `${navLinkBase} ${isActive ? navLinkActive : navLinkInactive}`
            }
          >
            Students
          </NavLink>

          {/* 🔥 NEW LINKS HERE */}
          <NavLink
            to="/cert-lookup"
            className={({ isActive }) =>
              `${navLinkBase} ${isActive ? navLinkActive : navLinkInactive}`
            }
          >
            Cert Lookup
          </NavLink>

          <NavLink
            to="/cert-database"
            className={({ isActive }) =>
              `${navLinkBase} ${isActive ? navLinkActive : navLinkInactive}`
            }
          >
            Certification Database
          </NavLink>
        </nav>

        <div className="px-4 py-3 border-t border-slate-800 text-[10px] text-slate-500">
          DB-backed · Auto-synced
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col">
        <header className="h-12 flex items-center justify-between border-b border-slate-800 px-6 bg-slate-950/80">
          <h1 className="text-sm font-semibold">Dashboard</h1>
          <span className="text-[11px] text-emerald-400">Up to date</span>
        </header>

        <div className="flex-1 overflow-auto px-6 py-4">{children}</div>
      </main>
    </div>
  );
}

export default Layout;