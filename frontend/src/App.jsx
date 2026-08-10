import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import StudyForm from "./pages/study-form";
import Studies from "./pages/studies";
import Statistics from "./pages/statistics";
import Settings from "./pages/settings";
import { LoginPage, RegisterPage } from "./components/auth/AuthPages";
import DashboardHome from "./components/dashboard/DashboardHome";
import LearnHome from "./pages/education/LearnHome";
import LevelPage from "./pages/education/LevelPage";
import GradePage from "./pages/education/GradePage";
import SubjectPage from "./pages/education/SubjectPage";
import TopicPage from "./pages/education/TopicPage";
import LessonPage from "./pages/education/LessonPage";
import DiagnosticPage from "./pages/education/DiagnosticPage";
import ReviewPage from "./pages/review/ReviewPage";
import ErrorNotebookPage from "./pages/review/ErrorNotebookPage";
import ChildrenPage from "./pages/children/ChildrenPage";
import ChildPage from "./pages/children/ChildPage";
import SupportPage from "./pages/children/SupportPage";
import SupportLessonPage from "./pages/children/SupportLessonPage";
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<DashboardHome />} />
        <Route path="/studies" element={<Studies />} />
        <Route path="/studies/new" element={<StudyForm />} />
        <Route path="/studies/:id/edit" element={<StudyForm />} />
        <Route path="/learn" element={<LearnHome />} />
        <Route path="/learn/level/:levelId" element={<LevelPage />} />
        <Route path="/learn/grade/:gradeId" element={<GradePage />} />
        <Route path="/learn/subject/:gradeSubjectId" element={<SubjectPage />} />
        <Route path="/learn/topic/:topicId" element={<TopicPage />} />
        <Route path="/learn/lesson/:lessonId" element={<LessonPage />} />
        <Route path="/learn/topic/:topicId/diagnostic" element={<DiagnosticPage />} />
        <Route path="/classes" element={<Navigate to="/children" replace />} />
        <Route path="/classes/:id" element={<Navigate to="/children" replace />} />
        <Route path="/children" element={<ChildrenPage />} />
        <Route path="/children/:id" element={<ChildPage />} />
        <Route path="/questions" element={<Navigate to="/learn" replace />} />
        <Route path="/activities" element={<Navigate to="/learn" replace />} />
        <Route path="/activities/:id" element={<Navigate to="/learn" replace />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/review/errors" element={<ErrorNotebookPage />} />
        <Route path="/teaching" element={<Navigate to="/support" replace />} />
        <Route path="/support" element={<SupportPage />} />
        <Route path="/support/:topicId" element={<SupportLessonPage />} />
        <Route path="/statistics" element={<Statistics />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
}
