import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Home, ArrowLeft, Search, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="border-0 shadow-2xl">
            <CardContent className="p-12">
              {/* 404 Animation */}
              <motion.div
                className="relative mb-8"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <div className="text-8xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  404
                </div>
                <motion.div
                  className="absolute -top-4 -right-4"
                  animate={{
                    rotate: [0, 10, -10, 0],
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    repeatType: "reverse",
                  }}
                >
                  <FileText className="h-12 w-12 text-blue-400" />
                </motion.div>
              </motion.div>

              <motion.h1
                className="text-3xl font-bold text-gray-900 dark:text-white mb-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                Page Not Found
              </motion.h1>

              <motion.p
                className="text-lg text-gray-600 dark:text-gray-300 mb-8 max-w-md mx-auto"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
              >
                Oops! The page you're looking for seems to have disappeared.
                Don't worry, let's get you back on track.
              </motion.p>

              <motion.div
                className="flex flex-col sm:flex-row gap-4 justify-center"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.8 }}
              >
                <Link to="/">
                  <Button
                    size="lg"
                    className="group bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300"
                  >
                    <Home className="h-5 w-5 mr-2" />
                    Go Home
                  </Button>
                </Link>

                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => window.history.back()}
                  className="group border-2 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <ArrowLeft className="h-5 w-5 mr-2 group-hover:-translate-x-1 transition-transform duration-300" />
                  Go Back
                </Button>
              </motion.div>

              {/* Additional helpful links */}
              <motion.div
                className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 1 }}
              >
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  Or explore these popular pages:
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <Link to="/features">
                    <Button variant="ghost" size="sm">
                      Features
                    </Button>
                  </Link>
                  <Link to="/about">
                    <Button variant="ghost" size="sm">
                      About
                    </Button>
                  </Link>
                  <Link to="/generate">
                    <Button variant="ghost" size="sm">
                      Generate PPT
                    </Button>
                  </Link>
                  <Link to="/convert">
                    <Button variant="ghost" size="sm">
                      Convert PPT
                    </Button>
                  </Link>
                </div>
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
