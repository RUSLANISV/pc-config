import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthForm from '../components/AuthForm';
import '../styles/auth.css';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  return (
    <div className="auth-page">
      <h2>{isLogin ? 'Login to PCconfig' : 'Create Account'}</h2>
      <AuthForm isLogin={isLogin} />
      <p>
        {isLogin ? "Don't have an account? " : "Already have an account? "}
        <button 
          onClick={() => setIsLogin(!isLogin)}
          className="switch-mode"
        >
          {isLogin ? 'Register' : 'Login'}
        </button>
      </p>
      <Link to="/" className="home-link">← Back to Home</Link>
    </div>
  );
};

export default AuthPage;