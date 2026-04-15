import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "@/components/common/ProtectedRoute";
import MainLayout from "@/components/layout/MainLayout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import DomainsPage from "@/pages/DomainsPage";
import CampaignCreatePage from "@/pages/CampaignCreatePage";
import CampaignHistoryPage from "@/pages/CampaignHistoryPage";
import CampaignMonitorPage from "@/pages/CampaignMonitorPage";
import CampaignDetailPage from "@/pages/CampaignDetailPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/domains" element={<DomainsPage />} />
        <Route path="/campaigns/new" element={<CampaignCreatePage />} />
        <Route path="/campaigns" element={<CampaignHistoryPage />} />
        <Route path="/campaigns/:id/monitor" element={<CampaignMonitorPage />} />
        <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
