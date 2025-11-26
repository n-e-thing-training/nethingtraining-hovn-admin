// frontend/src/pages/DashboardPage.jsx
import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api
      .stats()
      .then(setStats)
      .catch((e) => setErr(e.message || String(e)));
  }, []);

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Overview</h2>
        {err && (
          <span className="text-xs text-red-600">Stats error: {err}</span>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <StatCard label="Students" value={stats?.students_count} />
        <StatCard label="Bookings" value={stats?.bookings_count} />
        <StatCard label="Sessions" value={stats?.sessions_count} />
        <StatCard label="Orders" value={stats?.orders_count} />
      </div>
      <p className="text-xs text-slate-500 mt-2">
        This panel is a GUI over your Postgres DB. All data is coming from
        the HOVN pipeline tables.
      </p>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-3 flex flex-col gap-1">
      <span className="text-[11px] text-slate-500">{label}</span>
      <span className="text-base font-semibold">
        {value == null ? "—" : value}
      </span>
    </div>
  );
}