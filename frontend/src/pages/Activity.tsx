import React, { useEffect, useState } from "react";
import api from "@/utils/axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, Upload } from "lucide-react";

const Activity: React.FC = () => {
  const [recent, setRecent] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const token = localStorage.getItem("authToken");
        const response = await api.get("/api/dashboard", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setRecent(response.data.recent_activity || []);
      } catch (err) {
        setRecent([]);
      } finally {
        setLoading(false);
      }
    };
    fetchActivity();
  }, []);

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-gray-900 dark:text-white">
              All Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p>Loading...</p>
            ) : recent.length === 0 ? (
              <p className="text-gray-500">No activity found.</p>
            ) : (
              <div className="space-y-4">
                {recent.map((activity, idx) => (
                  <div
                    key={idx}
                    className="flex items-center space-x-4 border-b pb-3 last:border-b-0"
                  >
                    <div
                      className={`p-2 rounded-lg ${
                        activity.type === "created"
                          ? "bg-emerald-100 dark:bg-emerald-900/20"
                          : "bg-orange-100 dark:bg-orange-900/20"
                      }`}
                    >
                      {activity.type === "created" ? (
                        <Zap className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                      ) : (
                        <Upload className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {activity.filename}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {activity.date ? new Date(activity.date).toLocaleString() : ""}
                      </p>
                    </div>
                    <Badge
                      variant="secondary"
                      className={
                        activity.type === "created"
                          ? "bg-emerald-100 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400"
                          : "bg-orange-100 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400"
                      }
                    >
                      {activity.type === "created" ? "Created" : "Converted"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Activity; 