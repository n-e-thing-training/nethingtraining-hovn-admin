import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";

export default function CertLookupPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  async function lookup() {
    if (!email.trim()) return;

    setErr(null);
    setLoading(true);
    setResults([]);

    try {
      const res = await fetch(
        `/api/certs/lookup?email=${encodeURIComponent(email.trim())}`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error("Lookup failed");

      const json = await res.json();
      setResults(Array.isArray(json) ? json : []);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  const { netCerts, externalCerts } = useMemo(() => {
    const net = [];
    const ext = [];

    for (const c of results) {
      const org = (c.issuer_org || "").toLowerCase();
      const isNet = org.includes("n.e. thing training");

      if (isNet) net.push(c);
      else ext.push(c);
    }
    return { netCerts: net, externalCerts: ext };
  }, [results]);

  return (
    <div className="p-4 space-y-4">
      {/* Breadcrumb */}
      <div className="text-xs text-slate-500 mb-1 cursor-pointer"
           onClick={() => navigate("/")}>
        ← Dashboard / Cert Lookup
      </div>

      <h1 className="text-lg font-semibold">Lookup Certification by Email</h1>

      <div className="flex gap-2">
        <input
          className="border px-2 py-1 text-sm rounded w-64"
          placeholder="email@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button
          onClick={lookup}
          disabled={loading}
          className="px-3 py-1 bg-slate-900 text-white text-sm rounded disabled:opacity-50"
        >
          {loading ? "Looking…" : "Lookup"}
        </button>
      </div>

      {err && <p className="text-red-600 text-sm">{err}</p>}

      {!loading && results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CertColumn
            title="n.e. thing training issued"
            certs={netCerts}
            onStudentClick={(id) => navigate(`/students/${id}`)}
          />
          <CertColumn
            title="External certs"
            certs={externalCerts}
            onStudentClick={(id) => navigate(`/students/${id}`)}
          />
        </div>
      )}
    </div>
  );
}

function CertColumn({ title, certs, onStudentClick }) {
  return (
    <div className="border rounded-md p-2 bg-slate-50">
      <div className="flex justify-between mb-1">
        <h2 className="text-sm font-semibold">{title}</h2>
        <span className="text-[10px] text-slate-400">
          {certs.length} cert{certs.length !== 1 ? "s" : ""}
        </span>
      </div>

      {certs.length === 0 ? (
        <p className="text-xs text-slate-500">None found.</p>
      ) : (
        <div className="space-y-1 max-h-60 overflow-auto">
          {certs.map((c) => (
            <div
              key={c.cert_id}
              className="border rounded px-2 py-1 bg-white cursor-pointer hover:bg-slate-100"
              onClick={() => c.student_id && onStudentClick(c.student_id)}
            >
              <div className="text-[11px] font-semibold">{c.course_name}</div>

              <div className="text-[10px] text-slate-500">
                ID: {c.cert_id}
              </div>

              <div className="text-[10px] text-slate-500">
                {c.issue_date} → {c.expiry_date}
              </div>

              <div className="text-[10px] text-slate-500">
                Provider: {c.issuer_org || "—"}
              </div>

              {!c.student_id && (
                <span className="text-[9px] mt-1 px-1 bg-yellow-100 rounded text-yellow-800">
                  Unassigned (no student)
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}