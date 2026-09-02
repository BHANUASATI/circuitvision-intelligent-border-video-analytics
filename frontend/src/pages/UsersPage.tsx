import { useEffect, useState } from "react";
import { Plus, ShieldCheck, UserX } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { usersApi } from "@/api/endpoints";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { addToast } from "@/store/slices/uiSlice";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { User, UserCreate } from "@/types";

const EMPTY: UserCreate = { username: "", email: "", full_name: "", password: "" };

export default function UsersPage() {
  const dispatch   = useAppDispatch();
  const currentUser = useAppSelector((s) => s.auth.user);
  const [users,    setUsers]    = useState<User[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form,     setForm]     = useState<UserCreate>(EMPTY);

  if (!currentUser?.is_superuser) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-500 gap-3">
        <ShieldCheck size={32} />
        <p className="text-sm">Superuser access required</p>
      </div>
    );
  }

  const load = async () => {
    setLoading(true);
    try { setUsers(await usersApi.list()); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    try {
      await usersApi.create(form);
      dispatch(addToast({ type: "success", message: `User created: ${form.username}` }));
      setShowForm(false);
      setForm(EMPTY);
      load();
    } catch {
      dispatch(addToast({ type: "error", message: "Failed to create user" }));
    }
  };

  const handleDeactivate = async (id: string) => {
    try {
      await usersApi.update(id, { is_active: false } as Partial<User>);
      dispatch(addToast({ type: "info", message: "User deactivated" }));
      load();
    } catch {
      dispatch(addToast({ type: "error", message: "Failed" }));
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Users</h1>
          <p className="text-sm text-slate-500">{users.length} registered accounts</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(true)}>
          <Plus size={15} /> Add User
        </button>
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border">
                {["Name","Username","Email","Role","Status","Last Login","Actions"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-slate-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-surface-border hover:bg-surface/50">
                  <td className="px-4 py-3 text-sm text-slate-200">{u.full_name || "—"}</td>
                  <td className="px-4 py-3 text-xs font-mono text-slate-300">{u.username}</td>
                  <td className="px-4 py-3 text-xs text-slate-400">{u.email}</td>
                  <td className="px-4 py-3 text-xs text-slate-500">{u.is_superuser ? "Superuser" : "User"}</td>
                  <td className="px-4 py-3">
                    <span className={`badge text-[10px] ${u.is_active ? "status-new" : "status-acknowledged"}`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {u.last_login ? formatDistanceToNow(new Date(u.last_login), { addSuffix: true }) : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    {u.is_active && u.id !== currentUser.id && (
                      <button onClick={() => handleDeactivate(u.id)} className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1">
                        <UserX size={12} /> Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-40 p-4">
          <div className="card w-full max-w-sm space-y-4">
            <h2 className="text-base font-bold text-slate-100">Add User</h2>
            {(["full_name","username","email","password"] as const).map((k) => (
              <div key={k}>
                <label className="block text-xs text-slate-400 mb-1 capitalize">{k.replace("_"," ")}</label>
                <input
                  className="input"
                  type={k === "password" ? "password" : "text"}
                  value={form[k]}
                  onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                />
              </div>
            ))}
            <div className="flex gap-2">
              <button className="btn-primary flex-1" onClick={handleCreate}>Create</button>
              <button className="btn-ghost flex-1" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
