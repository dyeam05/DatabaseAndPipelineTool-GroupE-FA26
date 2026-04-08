import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";

import AppLayout from "./layouts/AppLayout";
import RouteDashboard from "./pages/RouteDashboard";
import RouteDetail from "./pages/RouteDetail";
import SegmentViewer from "./pages/SegmentViewer";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirect / → /routes */}
        <Route path="/" element={<Navigate to="/routes" replace />} />

        {/* All pages share the AppLayout (topbar + content wrapper) */}
        <Route element={<AppLayout />}>
          <Route path="/routes" element={<RouteDashboard />} />
          <Route path="/routes/:routeId" element={<RouteDetail />} />
          <Route path="/routes/:routeId/segments/:segmentId" element={<SegmentViewer />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
