// frontend/src/pages/OrdersPage.jsx
import React, { useEffect, useState } from "react";
import { api } from "../api";
import DataGrid from "../components/DataGrid";

export default function OrdersPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    setLoading(true);
    api
      .orders(500)
      .then((data) => setRows(data || []))
      .catch((e) => setErr(e.message || String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="h-full">
      <DataGrid
        title="Orders"
        rows={rows}
        loading={loading}
        error={err}
        primaryKey="id"
      />
    </div>
  );
}