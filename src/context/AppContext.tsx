import {
  createContext,
  useContext,
  useEffect,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";
import { ROLES, workspaces } from "../mockData";

export type PageId = "overview" | "review" | "vendors" | "documents" | "operations";
export type RoleName = keyof typeof ROLES;
export type WorkspaceId = (typeof workspaces)[number]["id"];
export type AuthMode = "login" | "signup" | "admin";

type RoleInfo = (typeof ROLES)[RoleName];
type WorkspaceInfo = (typeof workspaces)[number];

export type PendingUser = {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "pending" | "approved" | "rejected" | "flagged";
  created_at: string;
  workspaceId?: WorkspaceId;
  request_message?: string;
};

const API_BASE = "http://127.0.0.1:8000/api/v1";

type AppContextValue = {
  isAuthenticated: boolean;
  authMode: AuthMode;
  setAuthMode: Dispatch<SetStateAction<AuthMode>>;
  signIn: (email: string, password: string) => Promise<string | null>;
  signOut: () => void;
  page: PageId;
  setPage: Dispatch<SetStateAction<PageId>>;
  role: RoleName;
  roleInfo: RoleInfo;
  workspace: WorkspaceInfo;
  currentUser: PendingUser | null;
  isAdmin: boolean;
  pendingUsers: PendingUser[];
  approveUser: (id: string) => Promise<void>;
  rejectUser: (id: string) => Promise<void>;
  flagUser: (id: string) => Promise<void>;
  deleteUser: (id: string) => Promise<void>;
  submitSignupRequest: (name: string, email: string, role: string, password?: string) => Promise<string | null>;
  setWorkspaceId: (id: WorkspaceId) => void;
  sendContactMessage: (email: string, message: string) => Promise<string | null>;
};

const AppContext = createContext<AppContextValue | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [page, setPage] = useState<PageId>(() => (sessionStorage.getItem("page") as PageId) || "overview");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [isAdmin, setIsAdmin] = useState(() => sessionStorage.getItem("isAdmin") === "true");
  const [currentUser, setCurrentUser] = useState<PendingUser | null>(() => {
    const saved = sessionStorage.getItem("currentUser");
    if (!saved) return null;
    try { return JSON.parse(saved); } catch { return null; }
  });
  const [users, setUsers] = useState<PendingUser[]>([]);

  useEffect(() => { sessionStorage.setItem("page", page); }, [page]);
  useEffect(() => { sessionStorage.setItem("isAdmin", isAdmin.toString()); }, [isAdmin]);
  useEffect(() => {
    if (currentUser) sessionStorage.setItem("currentUser", JSON.stringify(currentUser));
    else sessionStorage.removeItem("currentUser");
  }, [currentUser]);

  // Fetch users if we are an admin
  useEffect(() => {
    if (isAdmin) {
      fetchWithAuth(`${API_BASE}/auth/users`)
        .then(res => res.json())
        .then(data => {
          // map from DB user role to requestedRole alias if needed, or just use role
          setUsers(data);
        })
        .catch(err => console.error("Failed to fetch users", err));
    }
  }, [isAdmin]);

  const isAuthenticated = isAdmin || currentUser !== null;
  const role: RoleName = (currentUser?.role as RoleName) ?? "Auditor";

  async function signIn(email: string, password: string): Promise<string | null> {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) {
        return data.detail || "Login failed";
      }

      if (data.user && data.user.role === "admin") {
        setIsAdmin(true);
        setCurrentUser(null);
      } else if (data.user) {
        setCurrentUser(data.user);
        setIsAdmin(false);
      }

      if (data.access_token) sessionStorage.setItem("access_token", data.access_token);
      if (data.refresh_token) sessionStorage.setItem("refresh_token", data.refresh_token);

      return null;
    } catch (err) {
      return "Network error connecting to backend.";
    }
  }

  function signOut() {
    setCurrentUser(null);
    setIsAdmin(false);
    setAuthMode("login");
    setPage("overview");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
  }

  async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    let token = sessionStorage.getItem("access_token");
    const headers = new Headers(options.headers || {});
    if (token) headers.set("Authorization", `Bearer ${token}`);

    let res = await fetch(url, { ...options, headers });

    if (res.status === 401 || res.status === 403) {
      const refreshToken = sessionStorage.getItem("refresh_token");
      if (refreshToken) {
        const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${refreshToken}` }
        });
        if (refreshRes.ok) {
          const refreshData = await refreshRes.json();
          sessionStorage.setItem("access_token", refreshData.access_token);
          if (refreshData.refresh_token) {
            sessionStorage.setItem("refresh_token", refreshData.refresh_token);
          }
          headers.set("Authorization", `Bearer ${refreshData.access_token}`);
          res = await fetch(url, { ...options, headers });
        } else {
          signOut();
        }
      } else {
        signOut();
      }
    }
    return res;
  }

  async function submitSignupRequest(
    name: string, email: string, role: string, password?: string
  ): Promise<string | null> {
    try {
      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role })
      });
      const data = await res.json();
      if (!res.ok) return data.detail || "Signup failed";
      return null;
    } catch (err) {
      return "Network error connecting to backend.";
    }
  }

  async function approveUser(id: string) {
    try {
      const res = await fetchWithAuth(`${API_BASE}/auth/users/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "approved" })
      });
      if (res.ok) {
        setUsers(prev => prev.map(u => u.id === id ? { ...u, status: "approved" } : u));
      }
    } catch (err) { console.error(err); }
  }

  async function rejectUser(id: string) {
    try {
      const res = await fetchWithAuth(`${API_BASE}/auth/users/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "rejected" })
      });
      if (res.ok) {
        setUsers(prev => prev.map(u => u.id === id ? { ...u, status: "rejected" } : u));
      }
    } catch (err) { console.error(err); }
  }

  async function flagUser(id: string) {
    try {
      // The backend might not support 'flagged' status, but we update locally at least
      await fetchWithAuth(`${API_BASE}/auth/users/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "flagged" })
      });
      // Always update locally for UI consistency even if backend fails
      setUsers(prev => prev.map(u => u.id === id ? { ...u, status: "flagged" } : u));
    } catch (err) { console.error(err); }
  }

  async function deleteUser(id: string) {
    try {
      await fetchWithAuth(`${API_BASE}/auth/users/${id}`, {
        method: "DELETE"
      });
      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (err) { console.error(err); }
  }

  function setWorkspaceId(id: WorkspaceId) {
    if (currentUser) {
      setCurrentUser({ ...currentUser, workspaceId: id });
    }
  }

  async function sendContactMessage(email: string, message: string) {
    try {
      const res = await fetch(`${API_BASE}/auth/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, message })
      });

      const data = await res.json();
      if (!res.ok) {
        return data.detail || "Failed to send message.";
      }

      setUsers((prev) => prev.map((u) => u.email === email ? { ...u, request_message: message } : u))
      console.log(data)
      return null;

    } catch (err) {
      console.log("Error:", err)
      return "Network error connecting to backend."
    }
  }

  const workspace =
    workspaces.find((w) => w.id === (currentUser?.workspaceId ?? workspaces[0].id)) ?? workspaces[0];

  return (
    <AppContext.Provider value={{
      isAuthenticated, authMode, setAuthMode, signIn, signOut,
      page, setPage, role, roleInfo: ROLES[role] || ROLES["Auditor"], workspace,
      currentUser, isAdmin, pendingUsers: users,
      approveUser, rejectUser, flagUser, deleteUser, submitSignupRequest, setWorkspaceId, sendContactMessage
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}