// frontend/src/App.jsx
import React from "react";
import { NavLink, Route, Routes, Navigate } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import StudentsPage from "./pages/StudentsPage";
import BookingsPage from "./pages/BookingsPage";
import SessionsPage from "./pages/SessionsPage";
import OrdersPage from "./pages/OrdersPage";
import StudentDetailPage from "./pages/StudentDetailPage"; // ⬅️ NEW
import CertLookupPage from "./pages/CertLookupPage";
import CertDatabasePage from "./pages/CertDatabasePage";

function App() {
  return (
    <div className="h-screen w-screen flex bg-slate-100 text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col">
        <div className="px-4 py-4 border-b border-slate-800">
          <h1 className="text-lg font-semibold tracking-tight">
            n.e. thing training
          </h1>
          <p className="text-xs text-slate-400">
            HOVN Admin · Airtable-style grid
          </p>
        </div>
        <nav className="flex-1 px-2 py-4 space-y-1 text-sm">
          <NavItem to="/dashboard" label="Dashboard" />
          <NavItem to="/students" label="Students" />
          <NavItem to="/bookings" label="Bookings" />
          <NavItem to="/sessions" label="Sessions" />
          <NavItem to="/orders" label="Orders" />

          {/* --- NEW CERT LINKS --- */}
          <div className="pt-4 border-t border-slate-800/50" />

          <NavItem to="/cert-lookup" label="Cert Lookup" />
          <NavItem to="/cert-database" label="Certification Database" />
        </nav>
        <div className="px-4 py-3 border-t border-slate-800 text-xs text-slate-500">
          <p>DB GUI · Local admin panel</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 flex flex-col">
        <header className="h-14 px-6 flex items-center border-b bg-white">
          <h2 className="text-base font-semibold tracking-tight">
            HOVN Pipeline Admin
          </h2>
        </header>

        <section className="flex-1 min-h-0 overflow-hidden p-4">
          <div className="h-full rounded-xl bg-white shadow-sm border border-slate-200 overflow-hidden flex flex-col">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* Airtable-style students grid */}
              <Route path="/students" element={<StudentsPage />} />

              {/* NEW: per-student detail view */}
              <Route path="/students/:id" element={<StudentDetailPage />} />

              <Route path="/bookings" element={<BookingsPage />} />
              <Route path="/sessions" element={<SessionsPage />} />
              <Route path="/orders" element={<OrdersPage />} />
              <Route path="/cert-lookup" element={<CertLookupPage />} />
              <Route path="/cert-database" element={<CertDatabasePage />} />

              <Route path="/students/:id" element={<StudentDetailPage />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </section>
      </main>
    </div>
  );
}

function NavItem({ to, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "flex items-center px-3 py-2 rounded-md transition-colors",
          isActive
            ? "bg-slate-800 text-white"
            : "text-slate-300 hover:bg-slate-800/60 hover:text-white",
        ].join(" ")
      }
    >
      <span className="truncate">{label}</span>
    </NavLink>
  );
}

export default App;