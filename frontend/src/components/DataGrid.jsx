// frontend/src/components/DataGrid.jsx
import React, { useMemo, useState } from "react";

export default function DataGrid({
  title,
  rows,
  primaryKey = "id",
  columns, // [{ key, label, width?, render? }]
  loading,
  error,
  onEdit, // (rowId, field, value) => Promise | void
}) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState("asc");
  const [expandedId, setExpandedId] = useState(null);
  const [editing, setEditing] = useState(null); // { id, key }

  const effectiveColumns = useMemo(() => {
    if (columns && columns.length) return columns;
    if (!rows || rows.length === 0) return [];
    const keys = Object.keys(rows[0]);
    return keys.map((k) => ({ key: k, label: k }));
  }, [columns, rows]);

  const filteredRows = useMemo(() => {
    if (!rows) return [];
    let res = rows;

    if (search.trim().length) {
      const s = search.toLowerCase();
      res = res.filter((row) =>
        Object.values(row)
          .join(" ")
          .toLowerCase()
          .includes(s)
      );
    }

    if (sortKey) {
      res = [...res].sort((a, b) => {
        const av = a[sortKey];
        const bv = b[sortKey];
        if (av == null && bv == null) return 0;
        if (av == null) return 1;
        if (bv == null) return -1;
        if (typeof av === "number" && typeof bv === "number") {
          return sortDir === "asc" ? av - bv : bv - av;
        }
        return sortDir === "asc"
          ? String(av).localeCompare(String(bv))
          : String(bv).localeCompare(String(av));
      });
    }

    return res;
  }, [rows, search, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const startEdit = (rowId, key) => {
    setEditing({ id: rowId, key });
  };

  const commitEdit = async (rowId, key, value) => {
    setEditing(null);
    if (!onEdit) return;
    try {
      await onEdit(rowId, key, value);
    } catch (e) {
      console.error("Edit failed", e);
      alert("Update failed: " + (e.message || String(e)));
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold tracking-tight">{title}</h3>
          <p className="text-xs text-slate-500">
            {loading
              ? "Loading…"
              : `${filteredRows.length} of ${rows?.length || 0} records`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            className="text-xs rounded-md border border-slate-300 px-2 py-1 w-56 focus:outline-none focus:ring-1 focus:ring-slate-400"
            placeholder="Search all fields…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="px-4 py-2 text-xs text-red-600 border-b bg-red-50">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="min-w-full text-xs">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="w-6 px-2 py-2 text-left text-slate-400">▾</th>
              {effectiveColumns.map((col) => (
                <th
                  key={col.key}
                  className="px-2 py-2 text-left font-medium text-slate-600 cursor-pointer select-none"
                  style={col.width ? { width: col.width } : undefined}
                  onClick={() => toggleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    <span>{col.label}</span>
                    {sortKey === col.key && (
                      <span className="text-[10px]">
                        {sortDir === "asc" ? "▲" : "▼"}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => {
              const rowId = row[primaryKey];
              const isExpanded = expandedId === rowId;
              return (
                <React.Fragment key={rowId}>
                  <tr
                    className="border-b hover:bg-slate-50 cursor-pointer"
                    onClick={() =>
                      setExpandedId(isExpanded ? null : rowId)
                    }
                  >
                    <td className="px-2 py-1 align-top text-slate-400">
                      {isExpanded ? "▾" : "▸"}
                    </td>
                    {effectiveColumns.map((col) => {
                      const cellKey = col.key;
                      const isEditing =
                        editing &&
                        editing.id === rowId &&
                        editing.key === cellKey;
                      const rawValue = row[cellKey];

                      if (col.render) {
                        return (
                          <td
                            key={cellKey}
                            className="px-2 py-1 align-top"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {col.render(row)}
                          </td>
                        );
                      }

                      if (isEditing) {
                        return (
                          <td
                            key={cellKey}
                            className="px-2 py-1 align-top"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <input
                              autoFocus
                              defaultValue={rawValue ?? ""}
                              className="w-full border border-slate-300 rounded px-1 py-0.5 text-[11px] focus:outline-none focus:ring-1 focus:ring-slate-400"
                              onBlur={(e) =>
                                commitEdit(rowId, cellKey, e.target.value)
                              }
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  e.target.blur();
                                } else if (e.key === "Escape") {
                                  setEditing(null);
                                }
                              }}
                            />
                          </td>
                        );
                      }

                      return (
                        <td
                          key={cellKey}
                          className="px-2 py-1 align-top"
                          onDoubleClick={(e) => {
                            e.stopPropagation();
                            startEdit(rowId, cellKey);
                          }}
                        >
                          {rawValue == null || rawValue === ""
                            ? "—"
                            : String(rawValue)}
                        </td>
                      );
                    })}
                  </tr>
                  {isExpanded && (
                    <tr className="bg-slate-50/60 border-b">
                      <td />
                      <td colSpan={effectiveColumns.length} className="px-3 py-2">
                        <pre className="text-[10px] bg-slate-900 text-slate-50 rounded-md p-2 overflow-auto">
                          {JSON.stringify(row, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
            {!loading && filteredRows.length === 0 && (
              <tr>
                <td
                  colSpan={effectiveColumns.length + 1}
                  className="px-4 py-6 text-center text-slate-400 text-xs"
                >
                  No records found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}