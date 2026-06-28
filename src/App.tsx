import { AppProvider, useApp } from "./context/AppContext";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import CommandCenter from "./components/CommandCenter";
import ReviewQueue from "./components/ReviewQueue";
import VendorIntelligence from "./components/VendorIntelligence";
import DocumentControl from "./components/DocumentControl";
import Operations from "./components/Operations";

function Shell() {
  const { page } = useApp();

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-shell">
        <Topbar />
        <div className="page-frame">
          {page === "overview" && <CommandCenter />}
          {page === "review" && <ReviewQueue />}
          {page === "vendors" && <VendorIntelligence />}
          {page === "documents" && <DocumentControl />}
          {page === "operations" && <Operations />}
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}