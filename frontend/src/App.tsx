import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ProjectForm } from './components/ProjectForm';
import { DashboardSimple } from './components/DashboardSimple';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectForm />} />
        <Route path="/dashboard" element={<DashboardSimple />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#333',
            color: '#fff',
          },
        }}
      />
    </BrowserRouter>
  );
}

export default App;
