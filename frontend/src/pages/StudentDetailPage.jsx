import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

function StudentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [student, setStudent] = useState(location.state?.student || null);
  const [loadingStudent, setLoadingStudent] = useState(!location.state?.student);
  const [studentError, setStudentError] = useState(null);

  const [certs, setCerts] = useState([]);
  const [loadingCerts, setLoadingCerts] = useState(false);
  const [certError, setCertError] = useState(null);

  useEffect(() => {
    if (student) return;

    let cancelled = false;

    async function fetchStudent() {
      try {
        setLoadingStudent(true);
        setStudentError(null);

        const res = await fetch("/api/students");
        if (!res.ok) throw new Error(`API /api/students failed: ${res.status}`);

        const all = await res.json();
        const numericId = Number(id);

        const found = Array.isArray(all)
          ? all.find((s) => s.id === numericId)
          : null;

        if (!cancelled) {
          if (!found) throw new Error("Student not found");
          setStudent(found);
        }
      } catch (err) {
        console.error("Failed to load student", err);
        if (!cancelled) setStudentError(err.message || "Failed to load student");
      } finally {
        if (!cancelled) setLoadingStudent(false);
      }
    }

    fetchStudent();
    return () => {
      cancelled = true;
    };
  }, [id, student]);

  useEffect(() => {
    if (student && certs.length === 0 && !loadingCerts) {
      handleLookupCerts();
    }
  }, [student]);

  const handleLookupCerts = async () => {
    if (!student?.email) return;

    try {
      setLoadingCerts(true);
      setCertError(null);
      setCerts([]);

      const url = `/api/certs/lookup?email=${encodeURIComponent(student.email)}`;
      const res = await fetch(url, { method: "POST" });
      if (!res.ok) throw new Error(`API /api/certs/lookup failed: ${res.status}`);

      const data = await res.json();
      const list = Array.isArray(data) ? data : data.certs || [];

      setCerts(list);
    } catch (err) {
      console.error("Failed to lookup certs", err);
      setCertError(err.message || "Failed to lookup certs");
    } finally {
      setLoadingCerts(false);
    }
  };

  const { netCerts, externalCerts } = useMemo(() => {
    const net = [];
    const ext = [];

    for (const c of certs || []) {
      const org = (c.issuer_org || c.agency_org_name || c.org_name || "").toLowerCase();

      const isNet =
        c.is_issued_by_net ??
        (org.includes("n.e. thing training") ? true : false);

      if (isNet) net.push(c);
      else ext.push(c);
    }

    return { netCerts: net, externalCerts: ext };
  }, [certs]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between border-b px-4 py-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate("/students")}
            className="text-xs text-slate-500 hover:text-slate-800"
          >
            ← Back to Students
          </button>
          <span className="text-xs text-slate-400">/</span>

          <div>
            <h3 className="text-sm font-semibold">
              {student
                ? `${student.first_name} ${student.last_name}`
                : "Student"}
            </h3>
            <p className="text-xs text-slate-500">
              Detail view · Red Cross live cert lookup
            </p>
          </div>
        </div>

        {student?.email && (
          <button
            onClick={handleLookupCerts}
            disabled={loadingCerts}
            className="text-xs px-3 py-1 rounded-md bg-slate-900 text-slate-50 hover:bg-slate-800 disabled:opacity-60"
          >
            {loadingCerts ? "Looking up…" : "Lookup certs from Red Cross"}
          </button>
        )}
      </div>

      <div className="flex-1 min-h-0 overflow-auto p-4 space-y-4">
        <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
          <h4 className="text-xs font-semibold text-slate-600 mb-2">Student Info</h4>

          {loadingStudent ? (
            <p className="text-xs text-slate-500">Loading student…</p>
          ) : studentError ? (
            <p className="text-xs text-red-600">{studentError}</p>
          ) : !student ? (
            <p className="text-xs text-slate-500">No student loaded.</p>
          ) : (
            <><div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2 text-xs">
                                      <Field label="First Name">
                                          <input
                                              className="border rounded px-1 py-[2px] text-xs w-full"
                                              value={student.first_name || ""}
                                              onChange={(e) => setStudent({ ...student, first_name: e.target.value })} />
                                      </Field>

                                      <Field label="Last Name">
                                          <input
                                              className="border rounded px-1 py-[2px] text-xs w-full"
                                              value={student.last_name || ""}
                                              onChange={(e) => setStudent({ ...student, last_name: e.target.value })} />
                                      </Field>

                                      <Field label="Email">
                                          <input
                                              className="border rounded px-1 py-[2px] text-xs w-full"
                                              value={student.email || ""}
                                              onChange={(e) => setStudent({ ...student, email: e.target.value })} />
                                      </Field>

                                      <Field label="Phone">
                                          <input
                                              className="border rounded px-1 py-[2px] text-xs w-full"
                                              value={student.phone || ""}
                                              onChange={(e) => setStudent({ ...student, phone: e.target.value })} />
                                      </Field>

                                      <Field label="HOVN Student ID">
                                          <input
                                              className="border rounded px-1 py-[2px] text-xs w-full font-mono"
                                              value={student.hovn_student_id || ""}
                                              onChange={(e) => setStudent({ ...student, hovn_student_id: e.target.value })} />
                                      </Field>
                                  </div><div className="mt-3">
                                          <button
                                              className="px-3 py-1 text-xs bg-slate-900 text-white rounded hover:bg-slate-800"
                                              onClick={async () => {
                                                  await fetch(`/api/students/${student.id}`, {
                                                      method: "PATCH",
                                                      headers: { "Content-Type": "application/json" },
                                                      body: JSON.stringify(student),
                                                  });
                                                  alert("Student updated!");
                                              } }
                                          >
                                              Save Changes
                                          </button>
                                      </div></>
          )}
        </div>

        <div className="border border-slate-200 rounded-lg p-3 bg-white">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-slate-600">Red Cross Certifications</h4>
            <p className="text-[11px] text-slate-400">
              First lookup hits Red Cross, then results are cached in the DB.
            </p>
          </div>

          {certError && (
            <p className="text-xs text-red-600 mb-2">{certError}</p>
          )}

          {!loadingCerts && certs.length === 0 ? (
            <p className="text-xs text-slate-500">
              Click &quot;Lookup certs…&quot; to load results.
            </p>
          ) : loadingCerts ? (
            <p className="text-xs text-slate-500">Loading certificates…</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CertColumn
                title="n.e. thing training issued"
                certs={netCerts}
                emptyMsg="No n.e. thing training certs found."
              />
              <CertColumn
                title="External certs"
                certs={externalCerts}
                emptyMsg="No external certs found."
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="text-xs text-slate-800">{children}</div>
    </div>
  );
}

function getBadgeColor(days) {
  if (days === null) return "bg-slate-300 text-slate-800";
  if (days > 90) return "bg-green-100 text-green-700";
  if (days >= 0 && days <= 90) return "bg-yellow-100 text-yellow-700";
  if (days < 0 && days >= -90) return "bg-red-100 text-red-700";
  if (days < -90) return "bg-blue-100 text-blue-700";
  return "bg-slate-300 text-slate-800";
}

function CertColumn({ title, certs, emptyMsg }) {
  return (
    <div className="border border-slate-200 rounded-md p-2 bg-slate-50">
      <div className="flex items-center justify-between mb-1">
        <h5 className="text-[11px] font-semibold text-slate-600">{title}</h5>
        <span className="text-[10px] text-slate-400">
          {certs.length} cert{certs.length === 1 ? "" : "s"}
        </span>
      </div>

      {certs.length === 0 ? (
        <p className="text-[11px] text-slate-500">{emptyMsg}</p>
      ) : (
        <div className="space-y-1 max-h-60 overflow-auto pr-1">
          {certs.map((c, idx) => {
            let days = null;
            try {
              let exp = null;

              if (c.expiry_date) {
                exp = new Date(c.expiry_date);
              } else if (c.issue_date) {
                const issued = new Date(c.issue_date);
                exp = new Date(issued);
                exp.setFullYear(exp.getFullYear() + 2);
              }

              if (exp) {
                const now = new Date();
                days = Math.floor((exp - now) / (1000 * 60 * 60 * 24));
              }
            } catch (e) {
              days = null;
            }

            const badgeColor = getBadgeColor(days);

            return (
              <div
                key={`${c.cert_id || idx}`}
                className={`border rounded px-2 py-1 ${
                  days === null
                    ? "bg-white border-slate-200"
                    : days >= 0
                      ? days > 90
                        ? "bg-white border-slate-200"
                        : "bg-yellow-50 border-yellow-200"
                      : days >= -90
                        ? "bg-red-50 border-red-200"
                        : "bg-blue-50 border-blue-200"
                }`}
              >
                <div className="flex justify-between">
                  <div className="text-[11px] font-semibold text-slate-800">
                    {c.course_name || "Unknown course"}
                  </div>

                  <span
                    className={`text-[9px] px-1 py-[1px] rounded font-semibold ${badgeColor}`}
                  >
                    {days === null
                      ? "—"
                      : days >= 0
                      ? `${days}d left`
                      : `${Math.abs(days)}d expired`}
                  </span>
                </div>

                <div className="text-[10px] text-slate-500 flex flex-wrap gap-x-2">
                  {c.cert_id && (
                    <span className="font-mono">
                      ID: <span className="font-normal">{c.cert_id}</span>
                    </span>
                  )}

                  {c.course_code && (
                    <span className="font-mono">
                      Code: <span className="font-normal">{c.course_code}</span>
                      {c.format && (
                        <span
                          className={`ml-1 px-1 rounded text-[9px] font-semibold ${
                            c.format === "Blended"
                              ? "bg-blue-100 text-blue-700"
                              : c.format === "Online"
                              ? "bg-purple-100 text-purple-700"
                              : "bg-green-100 text-green-700"
                          }`}
                        >
                          {c.format}
                        </span>
                      )}
                    </span>
                  )}
                </div>

                <div className="text-[10px] text-slate-500 mt-0.5 flex flex-wrap gap-x-3">
                  {c.issue_date && (
                    <span>
                      Issued: <span className="font-medium">{c.issue_date}</span>
                    </span>
                  )}
                  {c.expiry_date && (
                    <span>
                      Expires: <span className="font-medium">{c.expiry_date}</span>
                    </span>
                  )}
                </div>

                {c.issuer_org && (
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Provider: {c.issuer_org}
                  </div>
                )}

                {c.instructor_name && (
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Instructor: {c.instructor_name}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default StudentDetailPage;