import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Presentation,
  Sparkles,
  RefreshCw,
  LayoutDashboard,
  Menu,
  X,
  Sun,
  Moon,
  Monitor,
  User,
  LogOut,
  Settings,
  HelpCircle,
  MessageCircle,
} from "lucide-react";
import { TbRobot, TbBrain, TbSparkles, TbMessageCircle, TbZap } from 'react-icons/tb';
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import AuthModal from "./auth/AuthModal";
import ProfileModal from "./profile/ProfileModal";
import HelpModal from "./help/HelpModal";

function Navbar() {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  // Comprehensive cleanup function for modals
  const handleModalClose = (modalType: 'profile' | 'help') => {
    // Close the specific modal
    if (modalType === 'profile') {
      setIsProfileModalOpen(false);
    } else if (modalType === 'help') {
      setIsHelpModalOpen(false);
    }
  };

  const navigationItems = [
    {
      path: "/dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      authRequired: true,
    },
    {
      path: "/generate",
      label: "Generate",
      icon: Sparkles,
      authRequired: true,
    },
    {
      path: "/convert",
      label: "Convert",
      icon: RefreshCw,
      authRequired: true,
    },
    {
      path: "/templates",
      label: "Templates",
      icon: null,
      authRequired: false,
    },
    { path: "/features", label: "Features", icon: null, authRequired: false },
    { path: "/about", label: "About", icon: null, authRequired: false },
  ];

  const filteredNavItems = navigationItems.filter(
    (item) => !item.authRequired || isAuthenticated,
  );

  const themeIcons = {
    light: Sun,
    dark: Moon,
    system: Monitor,
  };

  const ThemeIcon = themeIcons[theme];

  // Listen for footer events
  useEffect(() => {
    const handleOpenHelp = () => setIsHelpModalOpen(true);
    const handleOpenFeedback = () => setIsHelpModalOpen(true);

    window.addEventListener("openHelp", handleOpenHelp);
    window.addEventListener("openFeedback", handleOpenFeedback);

    return () => {
      window.removeEventListener("openHelp", handleOpenHelp);
      window.removeEventListener("openFeedback", handleOpenFeedback);
    };
  }, []);

  return (
    <>
      <nav className="sticky top-0 z-50 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-b border-gradient-to-r from-blue-400/30 via-indigo-400/30 to-purple-400/30 dark:border-blue-700/30 shadow-lg shadow-blue-500/10">
        <div className="w-full px-6 sm:px-8 lg:px-12">
          <div className="flex justify-between items-center h-18">
            <Link to="/" className="flex items-center space-x-4 group">
              <div className="p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-105">
                <Presentation className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-gray-100 dark:to-gray-400 bg-clip-text text-transparent">
                  PPT Generator AI
                </h1>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-3 flex-1 justify-center">
              {filteredNavItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`group flex items-center space-x-3 px-6 py-3 rounded-xl font-semibold transition-all duration-300 relative overflow-hidden
                ${
                  isActive(item.path)
                    ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-xl shadow-blue-500/25 scale-105 ring-2 ring-blue-400/40"
                    : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gradient-to-r hover:from-blue-100/60 hover:to-indigo-100/60 dark:hover:from-blue-900/40 dark:hover:to-indigo-900/40"
                }`}
                  style={{ transition: "all 0.25s cubic-bezier(.4,2,.6,1)" }}
                >
                  <span
                    className={`absolute left-0 bottom-0 h-1 w-full bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 rounded-full scale-x-0 group-hover:scale-x-100 transition-transform duration-300 ${
                      isActive(item.path) ? "scale-x-100" : ""
                    }`}
                  ></span>
                  {item.icon && <item.icon className="h-5 w-5 z-10" />}
                  <span className="z-10">{item.label}</span>
                </Link>
              ))}
            </div>

            {/* User Section */}
            <div className="flex items-center space-x-4 ml-auto">
              {/* AI Chatbot Button */}
              <Button
                variant="ghost"
                size="sm"
                className="relative p-3 rounded-xl transition-all duration-300 group overflow-hidden"
                onClick={() => {
                  if (!isAuthenticated) {
                    setIsAuthModalOpen(true);
                  } else {
                  window.dispatchEvent(new CustomEvent('openChatbot'));
                  }
                }}
                style={{
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%)',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                }}
              >
                {/* Main content */}
                <div className="relative z-10 flex items-center space-x-2">
                  <div className="relative">
                    <TbMessageCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-all duration-300" />
                    
                    {/* AI indicator dot */}
                    <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full group-hover:bg-yellow-500 transition-colors duration-300"></div>
                  </div>
                  
                  {/* Text label */}
                  <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 group-hover:text-purple-700 dark:group-hover:text-purple-300 transition-colors duration-300">
                    AI Chat
                  </span>
                </div>
                
                {/* Simple hover effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-purple-400/10 to-blue-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"></div>
              </Button>

              {/* Theme Toggle */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="relative p-3 rounded-xl hover:bg-gradient-to-r hover:from-blue-100/80 hover:to-indigo-100/80 dark:hover:from-blue-900/60 dark:hover:to-indigo-900/60 transition-all duration-500 group overflow-hidden"
                    style={{
                      background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%)',
                      border: '1px solid rgba(59, 130, 246, 0.1)',
                    }}
                  >
                    {/* Animated background */}
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 via-indigo-400/20 to-blue-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                    
                    {/* Icon */}
                    <div className="relative z-10">
                      <ThemeIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform duration-500 drop-shadow-lg" />
                    </div>
                    
                    {/* Ripple effect */}
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-400/0 via-white/10 to-blue-400/0 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {(["light", "dark", "system"] as const).map((themeOption) => {
                    const Icon = themeIcons[themeOption];
                    const labels = {
                      light: "Light",
                      dark: "Dark",
                      system: "System",
                    };
                    return (
                      <DropdownMenuItem
                        key={themeOption}
                        onClick={() => setTheme(themeOption)}
                        className={
                          theme === themeOption
                            ? "bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400"
                            : ""
                        }
                      >
                        <Icon className="h-4 w-4 mr-2" />
                        {labels[themeOption]}
                      </DropdownMenuItem>
                    );
                  })}
                </DropdownMenuContent>
              </DropdownMenu>

              {isAuthenticated ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="relative h-8 w-8 rounded-full ring-2 ring-blue-400/40 hover:ring-4 hover:ring-indigo-400/40 transition-all duration-300 shadow-lg"
                    >
                      <Avatar className="h-8 w-8">
                        <AvatarImage
                          src={user?.avatar ? `http://localhost:5050/api/auth/avatar?${Date.now()}&user=${user?.email}` : undefined}
                          alt={user?.username || user?.email}
                        />
                        <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                          {user?.username?.charAt(0).toUpperCase() ||
                            user?.email?.charAt(0).toUpperCase() ||
                            "U"}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56" align="end" forceMount>
                    <div className="flex items-center justify-start gap-2 p-2">
                      <div className="flex flex-col space-y-1 leading-none">
                        <p className="font-medium">
                          {user?.username || user?.email?.split("@")[0] || "User"}
                        </p>
                        <p className="w-[200px] truncate text-sm text-muted-foreground">
                          {user?.email}
                        </p>
                      </div>
                    </div>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => setIsProfileModalOpen(true)}
                    >
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setIsProfileModalOpen(true)}
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      Settings
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setIsHelpModalOpen(true)}>
                      <HelpCircle className="mr-2 h-4 w-4" />
                      Help & Support
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout}>
                      <LogOut className="mr-2 h-4 w-4" />
                      Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <div className="hidden md:block">
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => setIsAuthModalOpen(true)}
                    className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg"
                  >
                    Sign In
                  </Button>
                </div>
              )}

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                {isMobileMenuOpen ? (
                  <X className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                ) : (
                  <Menu className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {isMobileMenuOpen && (
            <div className="md:hidden border-t border-gray-200/50 dark:border-gray-700/50 py-6">
              <div className="space-y-3">
                {filteredNavItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-3 px-5 py-3 rounded-xl font-medium transition-all duration-300 ${
                      isActive(item.path)
                        ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/25"
                        : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100/80 dark:hover:bg-gray-800/80"
                    }`}
                  >
                    {item.icon && <item.icon className="h-4 w-4" />}
                    <span>{item.label}</span>
                  </Link>
                ))}

                {!isAuthenticated && (
                  <div className="pt-2">
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => {
                        setIsAuthModalOpen(true);
                        setIsMobileMenuOpen(false);
                      }}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg"
                    >
                      Sign In
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </nav>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => handleModalClose('profile')}
      />

      <HelpModal
        isOpen={isHelpModalOpen}
        onClose={() => handleModalClose('help')}
      />
    </>
  );
}

export default Navbar;
