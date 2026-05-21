import React, { createContext, useContext, useState, useEffect } from "react";
import { toast } from "react-hot-toast";
import api from "@/utils/axios";

interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  preferences?: any;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string) => Promise<void>;
  loginWithGoogle: (accessToken: string) => Promise<void>;
  logout: () => void;
  updateProfile: (profileData: Partial<User>) => void;
  updateAvatar: (avatarUrl: string) => Promise<User | undefined>;
}

const AuthContext = createContext<AuthContextType & { setUser: React.Dispatch<React.SetStateAction<User | null>> } | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session from backend
    const checkAuth = async () => {
      try {
        const token = sessionStorage.getItem("authToken");
        const userData = sessionStorage.getItem("userData");
        
        console.log("DEBUG AUTH: Checking session", { token: !!token, userData: !!userData });
        
        if (token && userData) {
          // First try to load from sessionStorage for faster loading
          const parsedUser = JSON.parse(userData);
          console.log("DEBUG AUTH: Loading from sessionStorage", parsedUser);
          setUser(parsedUser);
          
          // Then verify with backend
          try {
            console.log("DEBUG AUTH: Verifying with backend...");
            const response = await api.get("/api/auth/me", {
            headers: { Authorization: `Bearer ${token}` },
          });
            console.log("DEBUG AUTH: Backend response", response.data);
          setUser(response.data);
            sessionStorage.setItem("userData", JSON.stringify(response.data));
          } catch (backendError: any) {
            console.error("DEBUG AUTH: Backend verification failed", backendError);
            if (backendError.response && backendError.response.status === 401) {
              setUser(null);
              sessionStorage.removeItem("authToken");
              sessionStorage.removeItem("userData");
              toast.error("Session expired. Please login again.");
            }
        }
        } else {
          console.log("DEBUG AUTH: No token or userData found");
        }
      } catch (error: any) {
        console.error("DEBUG AUTH: Session check error", error);
        setUser(null);
        sessionStorage.removeItem("authToken");
        sessionStorage.removeItem("userData");
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await api.post("/api/auth/login", { email, password });
      const { token, user: userData } = response.data;
      console.log("DEBUG AUTH: Login successful", { email, userData });
      setUser(userData);
      sessionStorage.setItem("authToken", token);
      sessionStorage.setItem("userData", JSON.stringify(userData));
      toast.success("🎉 Welcome back!");
    } catch (error: any) {
      console.error("DEBUG AUTH: Login failed", error);
      toast.error(error.response?.data?.error || "Login failed. Please try again.");
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (username: string, email: string, password: string) => {
    setLoading(true);
    try {
      const response = await api.post("/api/auth/signup", { username, email, password });
      const { token, user: userData } = response.data;
      setUser(userData);
      sessionStorage.setItem("authToken", token);
      sessionStorage.setItem("userData", JSON.stringify(userData));
      toast.success("🎉 Account created successfully!");
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Signup failed. Please try again.");
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (accessToken: string) => {
    setLoading(true);
    try {
      const response = await api.post("/api/auth/google", { access_token: accessToken });
      const { token, user: userData } = response.data;
      console.log("DEBUG AUTH: Google login successful", userData);
      setUser(userData);
      sessionStorage.setItem("authToken", token);
      sessionStorage.setItem("userData", JSON.stringify(userData));
      toast.success("🎉 Welcome! Logged in with Google.");
    } catch (error: any) {
      console.error("DEBUG AUTH: Google login failed", error);
      toast.error(error.response?.data?.error || "Google login failed. Please try again.");
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    sessionStorage.removeItem("authToken");
    sessionStorage.removeItem("userData");
    toast.success("👋 Logged out successfully");
  };

  const updateProfile = async (profileData: Partial<User>) => {
    const token = sessionStorage.getItem("authToken");
    if (user && token) {
      try {
        const response = await api.put(
          "/api/auth/profile",
          profileData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        const userObj = response.data.user || response.data;
        setUser(userObj);
        sessionStorage.setItem("userData", JSON.stringify(userObj));
        toast.success("Profile updated!");
      } catch (error: any) {
        toast.error(error.response?.data?.error || "Profile update failed.");
      }
    }
  };

  const updateAvatar = async (avatarUrl: string) => {
    const token = sessionStorage.getItem("authToken");
    if (user && token) {
      try {
        const response = await api.post(
          "/api/auth/avatar",
          { avatar_url: avatarUrl },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        const userObj = response.data.user;
        setUser(userObj);
        sessionStorage.setItem("userData", JSON.stringify(userObj));
        toast.success("Avatar updated!");
        return userObj;
      } catch (error: any) {
        toast.error(error.response?.data?.error || "Avatar update failed.");
        throw error;
      }
    }
  };

  const value: AuthContextType & { setUser: typeof setUser } = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    signup,
    loginWithGoogle,
    logout,
    updateProfile,
    updateAvatar,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
