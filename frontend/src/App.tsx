// src/App.tsx
import React, {JSX} from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import ProblemListPage from './features/problems/ProblemListPage';
import ProblemDetailPage from './features/problems/ProblemDetailPage';
import SubmissionsPage from './features/submissions/SubmissionsPage';
import ProfilePage from './features/profile/ProfilePage';

export default function App(): JSX.Element {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/problems" element={<ProblemListPage />} />
      <Route path="/problems/:id" element={<ProblemDetailPage />} />
      <Route path="/submissions" element={<SubmissionsPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="*" element={<Navigate to="/problems" replace />} />
    </Routes>
  );
}