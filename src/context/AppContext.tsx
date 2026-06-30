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
  requestedRole: RoleName;
  workspaceId: WorkspaceId;
  status: "pending" | "approved" | "rejected";
};

// Pre-seeded demo accounts (simulates a backend user registry)
const SEED_USERS: PendingUser[] = [
  { id: "u1", name: "Arjun Mehta",    email: "arjun@procureiq.com",   requestedRole: "Auditor",    workspaceId: "ws-alpha", status: "approved" },
  { id: "u2", name: "Priya Sharma",   email: "priya@procureiq.com",   requestedRole: "Gatekeeper", workspaceId: "ws-alpha", status: "approved" },
  { id: "u3", name: "Ravi Nair",      email: "ravi@procureiq.com",    requestedRole: "Strategist", workspaceId: "ws-beta",  status: "approved" },
  { id: "u4", name: "Sneha Kulkarni", email: "sneha@procureiq.com",   requestedRole: "Auditor",    workspaceId: "ws-beta",  status: "pending"  },
  { id: "u5", name: "Dev Patel",      email: "dev@procureiq.com",     requestedRole: "Gatekeeper", workspaceId: "ws-alpha", status: "pending"  },
];

const ADMIN_EMAIL    = "admin@procureiq.com";
const ADMIN_PASSWORD = "admin123";

type AppContextValue = {
  isAuthenticated: boolean;
  authMode: AuthMode;
  setAuthMode: Dispatch<SetStateAction<AuthMode>>;
  signIn: (email: string, password: string) => string | null;
  signOut: () => void;
  page: PageId;
  setPage: Dispatch<SetStateAction<PageId>>;
  role: RoleName;
  roleInfo: RoleInfo;
  workspace: WorkspaceInfo;
  currentUser: PendingUser | null;
  isAdmin: boolean;
  pendingUsers: PendingUser[];
  approveUser: (id: string) => void;
  rejectUser: (id: string) => void;
  submitSignupRequest: (name: string, email: string, role: RoleName, workspaceId: WorkspaceId) => string | null;
};

const AppContext = createContext<AppContextValue | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [page, setPage]               = useState<PageId>(() => (sessionStorage.getItem("page") as PageId) || "overview");
  const [authMode, setAuthMode]       = useState<AuthMode>("login");
  const [isAdmin, setIsAdmin]         = useState(() => sessionStorage.getItem("isAdmin") === "true");
  const [currentUser, setCurrentUser] = useState<PendingUser | null>(() => {
    const saved = sessionStorage.getItem("currentUser");
    return saved ? JSON.parse(saved) : null;
  });
  const [users, setUsers]             = useState<PendingUser[]>(SEED_USERS);

  useEffect(() => { sessionStorage.setItem("page", page); }, [page]);
  useEffect(() => { sessionStorage.setItem("isAdmin", isAdmin.toString()); }, [isAdmin]);
  useEffect(() => {
    if (currentUser) sessionStorage.setItem("currentUser", JSON.stringify(currentUser));
    else sessionStorage.removeItem("currentUser");
  }, [currentUser]);

  const isAuthenticated = isAdmin || currentUser !== null;
  const role: RoleName  = currentUser?.requestedRole ?? "Auditor";

  function signIn(email: string, password: string): string | null {
    if (email === ADMIN_EMAIL && password === ADMIN_PASSWORD) {
      setIsAdmin(true);
      setCurrentUser(null);
      return null;
    }
    const user = users.find((u) => u.email === email && u.status === "approved");
    if (!user) {
      if (users.find((u) => u.email === email && u.status === "pending"))
        return "Your account is pending admin approval.";
      if (users.find((u) => u.email === email && u.status === "rejected"))
        return "Your account request was rejected. Contact admin.";
      return "No account found. Request access via Signup.";
    }
    setCurrentUser(user);
    setIsAdmin(false);
    return null;
  }

  function signOut() {
    setCurrentUser(null);
    setIsAdmin(false);
    setAuthMode("login");
    setPage("overview");
  }

  function submitSignupRequest(
    name: string, email: string, role: RoleName, workspaceId: WorkspaceId
  ): string | null {
    if (users.find((u) => u.email === email))
      return "An account request already exists for this email.";
    setUsers((prev) => [...prev, {
      id: `u${Date.now()}`, name, email, requestedRole: role, workspaceId, status: "pending",
    }]);
    return null;
  }

  function approveUser(id: string) {
    setUsers((prev) => prev.map((u) => u.id === id ? { ...u, status: "approved" } : u));
  }

  function rejectUser(id: string) {
    setUsers((prev) => prev.map((u) => u.id === id ? { ...u, status: "rejected" } : u));
  }

  const workspace =
    workspaces.find((w) => w.id === (currentUser?.workspaceId ?? workspaces[0].id)) ?? workspaces[0];

  return (
    <AppContext.Provider value={{
      isAuthenticated, authMode, setAuthMode, signIn, signOut,
      page, setPage, role, roleInfo: ROLES[role], workspace,
      currentUser, isAdmin, pendingUsers: users,
      approveUser, rejectUser, submitSignupRequest,
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