import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText, User, Home, Edit, LogOut, Menu, X, CreditCard } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Navigation = () => {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Define navigation items based on authentication status
  const getNavItems = () => {
    const items = [
      { path: '/', label: 'Home', icon: Home },
    ];
    
    if (isAuthenticated) {
      items.push(
        { path: '/app', label: 'Generate CV', icon: FileText },
        { path: '/edit', label: 'My CVs', icon: Edit },
        { path: '/subscription', label: 'Subscription', icon: CreditCard }
      );
    } else {
      items.push(
        { path: '/login', label: 'Login', icon: User }
      );
    }
    
    return items;
  };
  
  const navItems = getNavItems();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };
  
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };
  
  const handleLogout = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await logout();
      // Navigate is handled automatically by the auth context
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-effect">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 gradient-button rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-black" />
            </div>
            <span className="text-xl font-bold gradient-text">MorphCV</span>
          </Link>

          {/* Navigation Links - Desktop */}
          <div className="hidden md:flex items-center space-x-6">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`nav-link flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-300 ${
                  isActive(path)
                    ? 'text-white bg-white/10'
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{label}</span>
              </Link>
            ))}
            
            {/* User Profile / Logout */}
            {isAuthenticated && user && (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-white/90">
                  {user.profile_pic ? (
                    <img 
                      src={user.profile_pic} 
                      alt={user.name} 
                      className="w-8 h-8 rounded-full border border-white/20"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
                      <User className="w-4 h-4 text-white/80" />
                    </div>
                  )}
                  <span className="font-medium text-sm">{user.name}</span>
                </div>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-white/70 hover:text-white bg-white/5 hover:bg-white/10 px-3 py-2 rounded-lg transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="font-medium text-sm">Logout</span>
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button 
              onClick={toggleMobileMenu}
              className="text-white/70 hover:text-white transition-colors p-2"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-effect border-t border-white/10 animate-fade-in">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                onClick={() => setMobileMenuOpen(false)}
                className={`nav-link flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-300 ${
                  isActive(path)
                    ? 'text-white bg-white/10'
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{label}</span>
              </Link>
            ))}
            
            {/* User Profile / Logout - Mobile */}
            {isAuthenticated && user && (
              <div className="pt-2 mt-2 border-t border-white/10">
                <div className="flex items-center space-x-2 px-3 py-2 text-white/90">
                  {user.profile_pic ? (
                    <img 
                      src={user.profile_pic} 
                      alt={user.name} 
                      className="w-8 h-8 rounded-full border border-white/20"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
                      <User className="w-4 h-4 text-white/80" />
                    </div>
                  )}
                  <span className="font-medium">{user.name}</span>
                </div>
                
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-2 px-3 py-2 mt-2 text-white/70 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="font-medium">Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
