import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Download,
  Clock,
  TrendingUp,
  Zap,
  Star,
  Calendar,
  BarChart3,
  Upload,
  Plus,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import api from "@/utils/axios";

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const token = sessionStorage.getItem("authToken");
        
        // Fetch dashboard stats
        const statsResponse = await api.get("/api/dashboard/stats", {
          headers: { Authorization: `Bearer ${token}` },
        });
        console.log("Dashboard stats:", statsResponse.data);
        setStats(statsResponse.data.stats);
        

        
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        // Set default stats if API fails
        setStats({
          total_presentations: 0,
          total_conversions: 0,
          total_ai_generations: 0,
          templates_used: 0
        });

      }
    };
    fetchDashboard();
  }, []);

  const templates = [
    {
      id: 1,
      name: "Modern Business",
      thumbnail:
        "https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
      downloads: 245,
      rating: 4.8,
    },
    {
      id: 2,
      name: "Creative Portfolio",
      thumbnail:
        "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
      downloads: 189,
      rating: 4.9,
    },
    {
      id: 3,
      name: "Data Analytics",
      thumbnail:
        "https://images.pexels.com/photos/590022/pexels-photo-590022.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
      downloads: 156,
      rating: 4.7,
    },
  ];

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Welcome back, {user?.username || user?.name || user?.email?.split("@")[0] || "User"}
              ! 👋
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Here's what's happening with your presentations today.
            </p>
            <div className="mt-4 text-sm text-gray-500">
              Current user: <span className="font-medium">{user?.username || user?.name}</span> (
              {user?.email})
            </div>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Link to="/generate">
            <Card className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer border-0 shadow-lg bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">
                      Generate New PPT
                    </h3>
                    <p className="text-blue-100">
                      Create presentations with AI
                    </p>
                  </div>
                  <Zap className="h-8 w-8 group-hover:scale-110 transition-transform duration-300" />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link to="/convert">
            <Card className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer border-0 shadow-lg bg-gradient-to-r from-orange-500 to-amber-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">
                      Convert Template
                    </h3>
                    <p className="text-orange-100">Transform existing slides</p>
                  </div>
                  <Upload className="h-8 w-8 group-hover:scale-110 transition-transform duration-300" />
                </div>
              </CardContent>
            </Card>
          </Link>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            key="total_presentations"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      Total Presentations
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats?.total_presentations || 0}
                    </p>
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                      AI + Converted PPTs
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/20">
                    <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          
          <motion.div
            key="total_conversions"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      PPT Conversions
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats?.total_conversions || 0}
                    </p>
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                      Templates converted
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-green-100 dark:bg-green-900/20">
                    <Download className="h-6 w-6 text-green-600 dark:text-green-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          
          <motion.div
            key="total_ai_generations"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      AI Generations
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats?.total_ai_generations || 0}
                    </p>
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                      AI-powered PPTs
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-purple-100 dark:bg-purple-900/20">
                    <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          
          <motion.div
            key="templates_used"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      Templates Used
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats?.templates_used || 0}
                    </p>
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                      Different templates
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/20">
                    <Star className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Popular Templates */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">
                  Popular Templates
                </CardTitle>
                <Link to="/templates">
                  <Button variant="ghost" size="sm">
                    Browse all
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="flex items-center space-x-4"
                  >
                    <img
                      src={template.thumbnail}
                      alt={template.name}
                      className="w-16 h-12 object-cover rounded-lg shadow-md"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {template.name}
                      </p>
                      <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                        <Download className="h-3 w-3" />
                        <span>{template.downloads}</span>
                        <Star className="h-3 w-3 text-yellow-400 fill-current" />
                        <span>{template.rating}</span>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Use
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Analytics Section */}
        <motion.div
          className="mt-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                <BarChart3 className="h-5 w-5 mr-2" />
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Link to="/generate">
                  <Button
                    variant="outline"
                    size="lg"
                    className="w-full justify-start hover:bg-blue-50 dark:hover:bg-blue-900/20"
                  >
                    <Zap className="h-5 w-5 mr-2" />
                    Generate New PPT
                  </Button>
                </Link>
                <Link to="/convert">
                  <Button
                    variant="outline"
                    size="lg"
                    className="w-full justify-start hover:bg-orange-50 dark:hover:bg-orange-900/20"
                  >
                    <Upload className="h-5 w-5 mr-2" />
                    Convert Template
                  </Button>
                </Link>
                <Link to="/analytics">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full justify-start hover:bg-green-50 dark:hover:bg-green-900/20"
                >
                  <BarChart3 className="h-5 w-5 mr-2" />
                  View Analytics
                </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
