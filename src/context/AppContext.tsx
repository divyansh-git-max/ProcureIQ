import { createContext, useContext, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import { ROLES } from "../mockData";

export type PageId = "overview" | "review" | "vendors" | "documents" | "operations";
export type RoleName = keyof typeof ROLES;

type RoleInfo = (typeof ROLES)[RoleName];

type AppContextValue = {
  page: PageId;
  setPage: Dispatch<SetStateAction<PageId>>;
  role: RoleName;
  setRole: Dispatch<SetStateAction<RoleName>>;
  roleInfo: RoleInfo;
};

const AppContext = createContext<AppContextValue | undefined>(undefined);

type AppProviderProps = {
  children: ReactNode;
};

export function AppProvider({ children }: AppProviderProps) {
  const [page, setPage] = useState<PageId>("overview");
  const [role, setRole] = useState<RoleName>("Auditor");

  const value = {
    page,
    setPage,
    role,
    setRole,
    roleInfo: ROLES[role],
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}