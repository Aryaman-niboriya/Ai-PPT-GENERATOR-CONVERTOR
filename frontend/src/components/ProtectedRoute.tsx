import React from "react";
import { useAuth } from "../contexts/AuthContext";
import AuthModal from "./auth/AuthModal";
import { useNavigate } from "react-router-dom";

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const [showModal, setShowModal] = React.useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    if (!loading && !isAuthenticated) setShowModal(true);
    else setShowModal(false);
  }, [isAuthenticated, loading]);

  if (loading) return null; // or a spinner

  if (!isAuthenticated) {
    return (
      <AuthModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          navigate("/"); // Home page redirect
        }}
      />
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute; 