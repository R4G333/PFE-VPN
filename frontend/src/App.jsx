import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import ErrorBoundary from "./components/ErrorBoundary";

import Login from "./pages/Login";
import VpnRequestForm from "./pages/VpnRequestForm";
import Dashboard from "./pages/Dashboard";
import RequestsList from "./pages/RequestsList";
import VpnUsers from "./pages/VpnUsers";
import Alerts from "./pages/Alerts";
import BlockedDevices from "./pages/BlockedDevices";
import UserManagement from "./pages/UserManagement";
import AuditLogs from "./pages/AuditLogs";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/" element={<VpnRequestForm />} />
          <Route path="/login" element={<Login />} />

          {/* Authenticated console */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/blocked-devices" element={<BlockedDevices />} />
            <Route path="/audit-logs" element={<AuditLogs />} />

            <Route
              path="/requests"
              element={
                <ProtectedRoute roles={["ADMIN", "SECURITY_ANALYST"]}>
                  <RequestsList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/vpn-users"
              element={
                <ProtectedRoute roles={["ADMIN", "SECURITY_ANALYST"]}>
                  <VpnUsers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute roles={["ADMIN"]}>
                  <UserManagement />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}
