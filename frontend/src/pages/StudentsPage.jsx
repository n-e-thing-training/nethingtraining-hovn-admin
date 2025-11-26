// frontend/src/pages/StudentsPage.jsx
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";

function StudentsPage() {
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchStudents() {
      try {
        setLoading(true);
        setLoadError(null);
        const res = await fetch("/api/students");
        if (!res.ok) {
          throw new Error(`API /api/students failed: ${res.status}`);
        }
        const data = await res.json();
        if (!cancelled) {
          setStudents(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error("Failed to load students", err);
        if (!cancelled) {
          setLoadError(err.message || "Failed to load students");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchStudents();

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return students;
    return students.filter((s) => {
      const name = `${s.first_name || ""} ${s.last_name || ""}`.toLowerCase();
      return (
        name.includes(term) ||
        (s.email || "").toLowerCase().includes(term) ||
        (s.phone || "").toLowerCase().includes(term) ||
        (s.hovn_student_id || "").toLowerCase().includes(term)
      );
    });
  }, [students, search]);

  const handleRowClick = (student) => {
    navigate(`/students/${student.id}`, { state: { student } });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <div>
          <h3 className="text-sm font-semibold">Students</h3>
          <p className="text-xs text-slate-500">
            Airtable-style grid · click a row to open details
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search name, email, phone, ID..."
            className="text-xs px-2 py-1 rounded border border-slate-300 bg-slate-50 focus:outline-none focus:ring-1 focus:ring-slate-400 focus:border-slate-400 min-w-[220px]"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 min-h-0 overflow-auto">
        {loading ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            Loading students…
          </div>
        ) : loadError ? (
          <div className="p-4 text-xs text-red-600">
            Error loading students: {loadError}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-4 text-xs text-slate-500">
            No students found. Try a different search.
          </div>
        ) : (
          <table className="min-w-full text-xs border-t border-slate-200">
            <thead className="bg-slate-50 sticky top-0 z-10">
              <tr>
                <Th>Student</Th>
                <Th>Email</Th>
                <Th>Phone</Th>
                <Th>HOVN ID</Th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr
                  key={s.id}
                  className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
                  onClick={() => handleRowClick(s)}
                >
                  <Td>
                    <div className="font-medium">
                      {s.first_name} {s.last_name}
                    </div>
                  </Td>
                  <Td className="text-slate-700">{s.email}</Td>
                  <Td className="text-slate-700">{s.phone}</Td>
                  <Td className="font-mono text-[10px] text-slate-500">
                    {s.hovn_student_id || "—"}
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Th({ children }) {
  return (
    <th className="px-3 py-2 text-left text-[11px] font-semibold text-slate-500 border-b border-slate-200">
      {children}
    </th>
  );
}

function Td({ children, className = "" }) {
  return (
      <td className={`px-3 py-2 align-middle ${className}`}>
        {children}
      </td>
  );
}

export default StudentsPage;