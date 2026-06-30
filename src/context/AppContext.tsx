import { createContext, useContext, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import { ROLES, workspaces } from "../mockData";

export type PageId = "overview" | "review" | "vendors" | "documents" | "operations";
export type RoleName = keyof typeof ROLES;
export type WorkspaceId = (typeof workspaces)[number]["id"];

type RoleInfo = (typeof ROLES)[RoleName];
type WorkspaceInfo = (typeof workspaces)[number];

type AppContextValue = {
  page: PageId;
  setPage: Dispatch<SetStateAction<PageId>>;
  role: RoleName;
  setRole: Dispatch<SetStateAction<RoleName>>;
  roleInfo: RoleInfo;
  workspace: WorkspaceInfo;
  setWorkspaceId: Dispatch<SetStateAction<WorkspaceId>>;
};

const AppContext = createContext<AppContextValue | undefined>(undefined);

type AppProviderProps = {
  children: ReactNode;
};

export function AppProvider({ children }: AppProviderProps) {
  const [page, setPage] = useState<PageId>("overview");
  const [role, setRole] = useState<RoleName>("Auditor");
  const [workspaceId, setWorkspaceId] = useState<WorkspaceId>(workspaces[0].id);

  const value = {
    page,
    setPage,
    role,
    setRole,
    roleInfo: ROLES[role],
    workspace: workspaces.find((item) => item.id === workspaceId) ?? workspaces[0],
    setWorkspaceId,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}