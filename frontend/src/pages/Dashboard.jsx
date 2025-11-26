// frontend/src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
import { api } from "../api";
import DataGrid from "../components/DataGrid";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentBookings, setRecentBookings] = useState([]);
  const [loadingBookings, setLoadingBookings] = useState(false);
  const [bookingsError, setBookingsError] = useState(null);

  useEffect(() => {
    api
      .stats()
      .then(setStats)
      .catch((err) => {
        console.error("stats error", err);
      });
  }, []);

  useEffect(() => {
    setLoadingBookings(true);
    api
      .bookings(5)
      .then((rows) => setRecentBookings(rows || []))
      .catch((err) => setBookingsError(err.message || String(err)))
      .finally(() => setLoadingBookings(false));
  }, []);

  const statCards = [
    { key: "bookings", label: "Bookings" },
    { key: "students", label: "Students" },
    { key: "sessions", label: "Sessions" },
    { key: "orders", label: "Orders" },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-sm font-semibold text-slate-100">Dashboard</h2>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div
            key={card.key}
            className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3"
          >
            <div className="text-[11px] text-slate-400 uppercase tracking-wide">
              {card.label}
            </div>
            <div className="mt-1 text-2xl font-semibold text-slate-50">
              {stats ? stats[card.key] ?? "—" : "—"}
            </div>
          </div>
        ))}
      </div>

      {/* Recent bookings grid (Airtable-style) */}
      <div className="h-[360px]">
        <DataGrid
          title="Recent bookings"
          rows={recentBookings}
          loading={loadingBookings}
          error={bookingsError}
          primaryKey="id"
        />
      </div>
    </div>
  );
}