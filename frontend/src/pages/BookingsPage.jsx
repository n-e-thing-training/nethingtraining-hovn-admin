// frontend/src/pages/BookingsPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import DataGrid from "../components/DataGrid";

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([api.bookings(500), api.students(500)])
      .then(([b, s]) => {
        setBookings(b || []);
        setStudents(s || []);
      })
      .catch((e) => setErr(e.message || String(e)))
      .finally(() => setLoading(false));
  }, []);

  const rows = useMemo(() => {
    const byId = {};
    for (const s of students) byId[s.id] = s;

    return bookings.map((b) => {
      const stu = byId[b.student_id];
      return {
        id: b.id,
        hovn_booking_ref: b.hovn_booking_ref,
        student_id: b.student_id,
        order_id: b.order_id,
        session_id: b.session_id,
        student_name: stu ? `${stu.first_name} ${stu.last_name}` : "—",
        student_email: stu?.email ?? "—",
        student_phone: stu?.phone ?? "—",
        _raw_booking: b,
        _raw_student: stu,
      };
    });
  }, [bookings, students]);

  const columns = [
    { key: "id", label: "ID", width: 40 },
    { key: "hovn_booking_ref", label: "Booking ref", width: 160 },
    { key: "student_name", label: "Student", width: 150 },
    { key: "student_email", label: "Student email", width: 200 },
    { key: "student_phone", label: "Student phone", width: 140 },
    { key: "session_id", label: "Session ID", width: 80 },
    { key: "order_id", label: "Order ID", width: 80 },
  ];

  return (
    <div className="h-full">
      <DataGrid
        title="Bookings"
        rows={rows}
        loading={loading}
        error={err}
        primaryKey="id"
        columns={columns}
      />
    </div>
  );
}