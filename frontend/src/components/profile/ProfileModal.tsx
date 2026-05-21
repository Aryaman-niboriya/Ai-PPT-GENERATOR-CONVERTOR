import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  User,
  Mail,
  Camera,
  Save,
  X,
  Upload,
  Settings,
  Shield,
  Bell,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "react-hot-toast";
import api from "@/utils/axios";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose }) => {
  const { user, setUser, updateAvatar } = useAuth();
  const [formData, setFormData] = useState({
    username: user?.username || "",
    email: user?.email || "",
    avatar: user?.avatar || "",
  });
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: false,
    marketingEmails: false,
    twoFactorAuth: false,
  });

  // Reset form data when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        username: user?.username || "",
        email: user?.email || "",
        avatar: user?.avatar || "",
      });
    }
  }, [isOpen, user]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleAvatarChange = async (file: File) => {
    setLoading(true);
    try {
      console.log('Uploading avatar file:', file);
      const token = sessionStorage.getItem("authToken");
      const formDataObj = new FormData();
      formDataObj.append("avatar", file);
      const response = await api.post(
        "/api/auth/avatar",
        formDataObj,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      console.log('Avatar upload response:', response.data);
      setUser(response.data.user);
      sessionStorage.setItem("userData", JSON.stringify(response.data.user));
      toast.success("Avatar updated!");
    } catch (error) {
      toast.error("Failed to update avatar");
    } finally {
      setLoading(false);
    }
  };

  const handleSetAvatarFromUrl = async (avatarUrl: string) => {
    setLoading(true);
    try {
      await updateAvatar(avatarUrl);
      // Force refresh avatar by updating timestamp
      setFormData(prev => ({ ...prev, avatar: avatarUrl }));
    } catch (error) {
      console.error("Avatar update failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem("authToken");
      const response = await api.put(
        "/api/auth/profile",
        { username: formData.username, email: formData.email },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const userObj = response.data.user || response.data;
      setUser(userObj);
      sessionStorage.setItem("userData", JSON.stringify(userObj));
      toast.success("Profile updated successfully!");
      handleClose();
    } catch (error) {
      toast.error("Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handlePreferencesSave = async (preferences: typeof settings) => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem("authToken");
      const response = await api.put(
        "/api/auth/preferences",
        preferences,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setUser(response.data.user);
      sessionStorage.setItem("userData", JSON.stringify(response.data.user));
      toast.success("Preferences updated!");
    } catch (error) {
      toast.error("Failed to update preferences");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    // Reset body styles
    document.body.style.overflow = 'auto';
    document.body.style.pointerEvents = 'auto';
    onClose();
  };

  const avatarOptions = [
    `https://api.dicebear.com/7.x/avataaars/svg?seed=user1`,
    `https://api.dicebear.com/7.x/avataaars/svg?seed=user2`,
    `https://api.dicebear.com/7.x/avataaars/svg?seed=user3`,
    `https://api.dicebear.com/7.x/avataaars/svg?seed=user4`,
    `https://api.dicebear.com/7.x/avataaars/svg?seed=user5`,
    `https://api.dicebear.com/7.x/avataaars/svg?seed=user6`,
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={handleClose}
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="relative bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold">Profile Settings</h2>
              <button
                onClick={handleClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              <Tabs defaultValue="profile" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="profile">Profile</TabsTrigger>
                  <TabsTrigger value="avatar">Avatar</TabsTrigger>
                  <TabsTrigger value="preferences">Preferences</TabsTrigger>
                </TabsList>

                {/* Profile Tab */}
                <TabsContent value="profile" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <User className="h-5 w-5" />
                        Personal Information
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center space-x-4">
                        <Avatar className="h-20 w-20">
                          <AvatarImage
                            src={user?.avatar ? `http://localhost:5050/api/auth/avatar?${Date.now()}&user=${user?.email}` : undefined}
                            alt={user?.username}
                          />
                          <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-lg">
                            {formData.username?.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <h3 className="text-lg font-semibold">{formData.username}</h3>
                          <p className="text-gray-600 dark:text-gray-400">
                            {formData.email}
                          </p>
                        </div>
                      </div>

                      <Separator />

                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="username">Username</Label>
                          <Input
                            id="username"
                            name="username"
                            type="text"
                            value={formData.username}
                            onChange={handleInputChange}
                            placeholder="Enter your username"
                            className="pl-10"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="email">Email</Label>
                          <Input
                            id="email"
                            name="email"
                            type="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            placeholder="Enter your email"
                            className="pl-10"
                            required
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Avatar Tab */}
                <TabsContent value="avatar" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Camera className="h-5 w-5" />
                        Choose Your Avatar
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="text-center">
                        <Avatar className="h-24 w-24 mx-auto mb-4">
                          <AvatarImage
                            src={user?.avatar ? `http://localhost:5050/api/auth/avatar?${Date.now()}&user=${user?.email}` : undefined}
                            alt={user?.username}
                          />
                          <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-xl">
                            {formData.username?.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <Button
                          onClick={() => {
                            const input = document.createElement('input');
                            input.type = 'file';
                            input.accept = 'image/*';
                            input.onchange = (event: Event) => {
                              const target = event.target as HTMLInputElement | null;
                              const files = target?.files;
                              if (files && files.length > 0) {
                                handleAvatarChange(files[0]);
                              }
                            };
                            input.click();
                          }}
                          variant="outline"
                          className="mb-4"
                        >
                          <Upload className="h-4 w-4 mr-2" />
                          Upload New Avatar
                        </Button>
                        <Button
                          onClick={() => {
                            const newSeed = Math.random().toString(36).substring(7);
                            const newAvatar = `https://api.dicebear.com/7.x/avataaars/svg?seed=${newSeed}`;
                            handleSetAvatarFromUrl(newAvatar);
                          }}
                          variant="outline"
                          className="mb-4"
                        >
                          <Camera className="h-4 w-4 mr-2" />
                          Generate Random Avatar
                        </Button>
                      </div>

                      <Separator />

                      <div>
                        <h4 className="font-medium mb-3">Choose from presets:</h4>
                        <div className="grid grid-cols-6 gap-3">
                          {avatarOptions.map((avatar, index) => (
                            <button
                              key={index}
                              onClick={() => handleSetAvatarFromUrl(avatar)}
                              className={`p-1 rounded-lg transition-all duration-200 ${
                                formData.avatar === avatar
                                  ? "ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20"
                                  : "hover:bg-gray-100 dark:hover:bg-gray-800"
                              }`}
                            >
                              <Avatar className="h-12 w-12">
                                <AvatarImage
                                  src={avatar}
                                  alt={`Avatar ${index + 1}`}
                                />
                                <AvatarFallback>A{index + 1}</AvatarFallback>
                              </Avatar>
                            </button>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Preferences Tab */}
                <TabsContent value="preferences" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Settings className="h-5 w-5" />
                        Notification Preferences
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="email-notifications">
                            Email Notifications
                          </Label>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Receive email updates about your presentations
                          </p>
                        </div>
                        <Switch
                          id="email-notifications"
                          checked={settings.emailNotifications}
                          onCheckedChange={(checked) =>
                            setSettings((prev) => ({
                              ...prev,
                              emailNotifications: checked,
                            }))
                          }
                        />
                      </div>

                      <Separator />

                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="push-notifications">
                            Push Notifications
                          </Label>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Get notified when your presentations are ready
                          </p>
                        </div>
                        <Switch
                          id="push-notifications"
                          checked={settings.pushNotifications}
                          onCheckedChange={(checked) =>
                            setSettings((prev) => ({
                              ...prev,
                              pushNotifications: checked,
                            }))
                          }
                        />
                      </div>

                      <Separator />

                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="marketing-emails">Marketing Emails</Label>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Receive updates about new features and templates
                          </p>
                        </div>
                        <Switch
                          id="marketing-emails"
                          checked={settings.marketingEmails}
                          onCheckedChange={(checked) =>
                            setSettings((prev) => ({
                              ...prev,
                              marketingEmails: checked,
                            }))
                          }
                        />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Security Settings
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="two-factor">
                            Two-Factor Authentication
                          </Label>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Add an extra layer of security to your account
                          </p>
                        </div>
                        <Switch
                          id="two-factor"
                          checked={settings.twoFactorAuth}
                          onCheckedChange={(checked) =>
                            setSettings((prev) => ({
                              ...prev,
                              twoFactorAuth: checked,
                            }))
                          }
                        />
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>

            {/* Footer */}
            <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={loading}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ProfileModal;
