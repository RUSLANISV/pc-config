import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import SearchPage from './pages/SearchPage';
import ProfilePage from './pages/ProfilePage';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import BuildsPage from './pages/BuildsPage';
import EditBuildPage from './pages/EditBuildPage';
import AIChat from './components/AIChat';
import './App.css';

const AppContent = () => {
  const location = useLocation();
  const showChat = ['/', '/search', '/profile'].includes(location.pathname);

  return (
    <>
      <Header />
      <Routes>
        <Route path="/builds/edit" element={
          <ProtectedRoute>
            <EditBuildPage />
          </ProtectedRoute>
        }/>
        <Route path="/builds" element={
          <ProtectedRoute>
            <BuildsPage />
          </ProtectedRoute>
        }/>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/profile" element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }/>
        <Route path="/favorites" element={<div>Избранное</div>} />
      </Routes>
      
      {showChat && <AIChat />}
    </>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;