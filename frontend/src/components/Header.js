import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">PCconfig</Link>
        <nav className="nav">
          <Link to="/search" className="nav-link">Search</Link>
          <Link to="/profile" className="nav-link">Profile</Link>
          <Link to="/auth" className="nav-link">Войти</Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;