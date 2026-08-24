import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import StudyForm from "./pages/study-form";
import Studies from "./pages/studies";
import Statistics from "./pages/statistics";
import Settings from "./pages/settings";
import { LoginPage, RegisterPage } from "./components/auth/AuthPages";
import DashboardHome from "./components/dashboard/DashboardHome";
import NotFound from "./pages/not-found";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<DashboardHome />} />
        <Route path="/studies" element={<Studies />} />
        <Route path="/studies/new" element={<StudyForm />} />
        <Route path="/studies/:id/edit" element={<StudyForm />} />
        <Route path="/statistics" element={<Statistics />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
