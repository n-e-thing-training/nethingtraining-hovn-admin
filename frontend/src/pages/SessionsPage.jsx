// frontend/src/pages/SessionsPage.jsx
import React, { useEffect, useState } from "react";
import { api } from "../api";
import DataGrid from "../components/DataGrid";

export default function SessionsPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    setLoading(true);
    api
      .sessions(500)
      .then((data) => setRows(data || []))
      .catch((e) => setErr(e.message || String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="h-full">
      <DataGrid
        title="Sessions"
        rows={rows}
        loading={loading}
        error={err}
        primaryKey="id"
      />
    </div>
  );
}