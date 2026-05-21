import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import api from "@/utils/axios";
import {
  BarChart3,
  TrendingUp,
  Activity,
  Download,
  Star,
  Clock,
  Target,
  Zap,
  Users,
  FileText,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  BarChart,
  PieChart,
  LineChart,
  Download as DownloadIcon,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  LineChart as RechartsLineChart,
  Line,
  Area,
  AreaChart,
} from "recharts";

interface AnalyticsData {
  overview: {
    total_presentations: number;
    total_ai_generations: number;
    total_conversions: number;
    templates_used: number;
    total_chat_sessions: number;
    total_chat_messages: number;
  };
  performance: {
    avg_presentations_per_day: number;
    ai_generation_rate: number;
    template_usage_rate: number;
    activity_score: number;
  };
  activity_breakdown: Record<string, number>;
  daily_activity: Record<string, number>;
  recent_trends: {
    last_7_days_activity: number;
    last_30_days_activity: number;
    most_active_day: string | null;
  };
}

interface PerformanceData {
  weekly_performance: Array<{
    week: string;
    activities: number;
    ai_generations: number;
    conversions: number;
    template_downloads: number;
  }>;
  monthly_trends: Array<{
    month: string;
    total_activities: number;
    presentations_created: number;
  }>;
  efficiency_metrics: {
    total_activities: number;
    ai_efficiency: number;
    conversion_efficiency: number;
    productivity_score: number;
    consistency_score: number;
  };
  activity_distribution: {
    ai_generations: number;
    conversions: number;
    template_downloads: number;
    other_activities: number;
  };
}

interface UsageData {
  feature_usage: {
    ai_generation: { count: number; percentage: number; last_used: string | null };
    template_conversion: { count: number; percentage: number; last_used: string | null };
    template_downloads: { count: number; percentage: number; last_used: string | null };
    chat_sessions: { count: number; percentage: number; last_used: string | null };
  };
  usage_patterns: {
    hourly: Record<string, number>;
    daily: Record<string, number>;
  };
  recommendations: string[];
  total_usage_count: number;
}

const Analytics: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const token = sessionStorage.getItem("authToken");
      const headers = { Authorization: `Bearer ${token}` };

      // Fetch all analytics data
      const [overviewRes, performanceRes, usageRes] = await Promise.all([
        api.get("/api/analytics/overview", { headers }),
        api.get("/api/analytics/performance", { headers }),
        api.get("/api/analytics/usage", { headers }),
      ]);

      setAnalyticsData(overviewRes.data);
      setPerformanceData(performanceRes.data);
      setUsageData(usageRes.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000) return (num / 1000).toFixed(1) + "k";
    return num.toString();
  };

  const getPercentageChange = (current: number, previous: number) => {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  };

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"];

  if (loading) {
    return (
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Analytics Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Track your presentation creation performance and usage patterns
              </p>
            </div>
            <Button onClick={fetchAnalyticsData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </motion.div>

        {/* Analytics Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="usage">Usage Patterns</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {analyticsData && (
              <>
                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <Card className="border-0 shadow-lg">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                              Total Presentations
                            </p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {formatNumber(analyticsData.overview.total_presentations)}
                            </p>
                            <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                              <ArrowUpRight className="h-3 w-3 inline mr-1" />
                              {analyticsData.performance.avg_presentations_per_day} per day
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
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <Card className="border-0 shadow-lg">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                              AI Generations
                            </p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {formatNumber(analyticsData.overview.total_ai_generations)}
                            </p>
                            <p className="text-sm text-purple-600 dark:text-purple-400 mt-1">
                              {analyticsData.performance.ai_generation_rate}% of total
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
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <Card className="border-0 shadow-lg">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                              Templates Used
                            </p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {formatNumber(analyticsData.overview.templates_used)}
                            </p>
                            <p className="text-sm text-orange-600 dark:text-orange-400 mt-1">
                              {analyticsData.performance.template_usage_rate}% usage rate
                            </p>
                          </div>
                          <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/20">
                            <Download className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                  >
                    <Card className="border-0 shadow-lg">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                              Activity Score
                            </p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {analyticsData.performance.activity_score}
                            </p>
                            <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                              Last 30 days
                            </p>
                          </div>
                          <div className="p-3 rounded-xl bg-green-100 dark:bg-green-900/20">
                            <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Activity Breakdown */}
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 }}
                  >
                    <Card className="border-0 shadow-lg">
                      <CardHeader>
                        <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                          Activity Breakdown
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <RechartsPieChart>
                              <Pie
                                data={Object.entries(analyticsData.activity_breakdown).map(([key, value]) => ({
                                  name: key.replace('_', ' ').toUpperCase(),
                                  value,
                                }))}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                              >
                                {Object.entries(analyticsData.activity_breakdown).map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Daily Activity */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 }}
                  >
                    <Card className="border-0 shadow-lg">
                      <CardHeader>
                        <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                          Daily Activity (Last 7 Days)
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <RechartsBarChart
                              data={Object.entries(analyticsData.daily_activity).map(([date, count]) => ({
                                date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                                activities: count,
                              }))}
                            >
                              <XAxis dataKey="date" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="activities" fill="#3b82f6" />
                            </RechartsBarChart>
                          </ResponsiveContainer>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                </div>
              </>
            )}
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6">
            {performanceData && (
              <>
                {/* Efficiency Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card className="border-0 shadow-lg">
                    <CardContent className="p-6">
                      <div className="text-center">
                        <Target className="h-8 w-8 text-blue-600 dark:text-blue-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Productivity Score</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {performanceData.efficiency_metrics.productivity_score}
                        </p>
                        <Badge variant="secondary" className="mt-2">
                          / 100
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-0 shadow-lg">
                    <CardContent className="p-6">
                      <div className="text-center">
                        <TrendingUp className="h-8 w-8 text-green-600 dark:text-green-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">AI Efficiency</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {performanceData.efficiency_metrics.ai_efficiency}%
                        </p>
                        <Badge variant="secondary" className="mt-2">
                          AI Usage
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-0 shadow-lg">
                    <CardContent className="p-6">
                      <div className="text-center">
                        <RefreshCw className="h-8 w-8 text-orange-600 dark:text-orange-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Conversion Rate</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {performanceData.efficiency_metrics.conversion_efficiency}%
                        </p>
                        <Badge variant="secondary" className="mt-2">
                          Template Usage
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-0 shadow-lg">
                    <CardContent className="p-6">
                      <div className="text-center">
                        <Clock className="h-8 w-8 text-purple-600 dark:text-purple-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Consistency</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {performanceData.efficiency_metrics.consistency_score}
                        </p>
                        <Badge variant="secondary" className="mt-2">
                          Weekly Score
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Weekly Performance Chart */}
                <Card className="border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                      Weekly Performance Trends
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsBarChart data={performanceData.weekly_performance}>
                          <XAxis dataKey="week" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="ai_generations" fill="#8b5cf6" name="AI Generations" />
                          <Bar dataKey="conversions" fill="#f59e0b" name="Conversions" />
                          <Bar dataKey="template_downloads" fill="#10b981" name="Template Downloads" />
                        </RechartsBarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Usage Patterns Tab */}
          <TabsContent value="usage" className="space-y-6">
            {usageData && (
              <>
                {/* Feature Usage */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {Object.entries(usageData.feature_usage).map(([feature, data], index) => (
                    <motion.div
                      key={feature}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Card className="border-0 shadow-lg">
                        <CardContent className="p-6">
                          <div className="text-center">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 mx-auto mb-3 flex items-center justify-center">
                              <span className="text-white font-bold text-lg">
                                {feature.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                              {feature.replace('_', ' ').toUpperCase()}
                            </p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {data.count}
                            </p>
                            <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                              {data.percentage}% of total usage
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>

                {/* Usage Patterns Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Hourly Usage Pattern */}
                  <Card className="border-0 shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                        Hourly Usage Pattern (Last 7 Days)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart
                            width={500}
                            height={250}
                            data={Object.entries(usageData.usage_patterns.hourly).map(([hour, count]) => ({
                              hour: `${hour}:00`,
                              activities: count,
                            }))}
                          >
                            <XAxis dataKey="hour" />
                            <YAxis />
                            <Tooltip />
                            <Area type="monotone" dataKey="activities" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Daily Usage Pattern */}
                  <Card className="border-0 shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                        Daily Usage Pattern (Last 30 Days)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <RechartsLineChart
                            data={Object.entries(usageData.usage_patterns.daily).map(([date, count]) => ({
                              date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                              activities: count,
                            }))}
                          >
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip />
                            <Line type="monotone" dataKey="activities" stroke="#10b981" strokeWidth={2} />
                          </RechartsLineChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            )}
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recommendations */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                    Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {usageData?.recommendations && usageData.recommendations.length > 0 ? (
                    <div className="space-y-3">
                      {usageData.recommendations.map((recommendation, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <Star className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                          <p className="text-sm text-gray-700 dark:text-gray-300">{recommendation}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                      Great job! You're using all features effectively.
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                    Quick Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analyticsData && (
                      <>
                        <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">Most Active Day</p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {analyticsData.recent_trends.most_active_day || 'No data'}
                            </p>
                          </div>
                          <Calendar className="h-5 w-5 text-green-600 dark:text-green-400" />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">7-Day Activity</p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {analyticsData.recent_trends.last_7_days_activity} activities
                            </p>
                          </div>
                          <Activity className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">Total Usage</p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {usageData?.total_usage_count || 0} interactions
                            </p>
                          </div>
                          <Users className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                        </div>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Analytics; 