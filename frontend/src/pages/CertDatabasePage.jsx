// frontend/src/pages/CertDatabasePage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function CertDatabasePage() {
  const navigate = useNavigate();

  const [certs, setCerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [provider, setProvider] = useState("");
  const [format, setFormat] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/certs/all");
        const json = await res.json();
        setCerts(json);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = certs.filter((c) => {
    const now = new Date();
    const exp = c.expiry_date ? new Date(c.expiry_date) : null;

    if (search && !c.course_name.toLowerCase().includes(search.toLowerCase()))
      return false;

    if (provider && c.issuer_org !== provider) return false;

    if (format && c.format !== format) return false;

    if (status === "active" && exp && exp < now) return false;
    if (status === "expired" && exp && exp >= now) return false;

    return true;
  });

  const uniqueProviders = [
    ...new Set(certs.map((c) => c.issuer_org).filter(Boolean)),
  ];
  const uniqueFormats = [
    ...new Set(certs.map((c) => c.format).filter(Boolean)),
  ];

  return (
    // 🔑 fill available height inside Layout, but let Layout control the viewport
    <div className="flex flex-col h-full">
      {/* Breadcrumb */}
      <div
        className="text-xs text-slate-500 mb-1 cursor-pointer"
        onClick={() => navigate("/dashboard")}
      >
        ← Dashboard / Certification Database
      </div>

      <h1 className="text-lg font-semibold mb-2">Certification Database</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end mb-3">
        <div>
          <div className="text-[10px] uppercase text-slate-500">Search</div>
          <input
            className="border px-2 py-1 text-sm rounded w-60"
            placeholder="Course name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div>
          <div className="text-[10px] uppercase text-slate-500">Provider</div>
          <select
            className="border text-sm px-2 py-1 rounded"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="">All</option>
            {uniqueProviders.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="text-[10px] uppercase text-slate-500">Format</div>
          <select
            className="border text-sm px-2 py-1 rounded"
            value={format}
            onChange={(e) => setFormat(e.target.value)}
          >
            <option value="">All</option>
            {uniqueFormats.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="text-[10px] uppercase text-slate-500">Status</div>
          <select
            className="border text-sm px-2 py-1 rounded"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All</option>
            <option value="active">Active only</option>
            <option value="expired">Expired only</option>
          </select>
        </div>
      </div>

      {/* 🔑 Make the table area flex-1 + scrollable */}
      <div className="flex-1 min-h-0">
        {loading ? (
          <p className="text-sm text-slate-500">Loading database…</p>
        ) : (
          <div className="h-full border rounded bg-white overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-[11px] uppercase text-slate-500 sticky top-0">
                <tr>
                  <th className="px-2 py-1 text-left">Course</th>
                  <th className="px-2 py-1 text-left">Provider</th>
                  <th className="px-2 py-1">Format</th>
                  <th className="px-2 py-1">Issued</th>
                  <th className="px-2 py-1">Expires</th>
                  <th className="px-2 py-1">Student</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr
                    key={c.cert_id}
                    className="border-b last:border-b-0 hover:bg-slate-50"
                  >
                    <td className="px-2 py-1">{c.course_name}</td>
                    <td className="px-2 py-1">{c.issuer_org}</td>
                    <td className="px-2 py-1 text-center">{c.format}</td>
                    <td className="px-2 py-1 text-center">{c.issue_date}</td>
                    <td className="px-2 py-1 text-center">{c.expiry_date}</td>
                    <td
                      className="px-2 py-1 text-blue-700 cursor-pointer"
                      onClick={() =>
                        c.student_id && navigate(`/students/${c.student_id}`)
                      }
                    >
                      {c.student_name || "—"}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-3 py-4 text-center text-sm text-slate-500"
                    >
                      No certifications match the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
