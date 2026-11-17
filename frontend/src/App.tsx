import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import WorkspacesPage from "./pages/WorkspacesPage";
import WorkspaceDetailPage from "./pages/WorkspaceDetailPage";
import JobDetailPage from "./pages/JobDetailPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<WorkspacesPage />} />
        <Route path="/workspaces/:id" element={<WorkspaceDetailPage />} />
        <Route path="/jobs/:id" element={<JobDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
