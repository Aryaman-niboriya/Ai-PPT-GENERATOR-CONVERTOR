import React from "react";
import { motion } from "framer-motion";
import {
  Users,
  Target,
  Award,
  Heart,
  Globe,
  Zap,
  Star,
  TrendingUp,
  Shield,
  Sparkles,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function About() {
  const stats = [
    { label: "Happy Users", value: "50,000+", icon: Users },
    { label: "Presentations Created", value: "500,000+", icon: Sparkles },
    { label: "Templates Available", value: "500+", icon: Award },
    { label: "Countries Served", value: "120+", icon: Globe },
  ];

  const values = [
    {
      icon: Target,
      title: "Innovation First",
      description:
        "We're constantly pushing the boundaries of what's possible with AI and presentation technology.",
    },
    {
      icon: Heart,
      title: "User-Centric",
      description:
        "Every feature we build is designed with our users' needs and feedback at the center.",
    },
    {
      icon: Shield,
      title: "Trust & Security",
      description:
        "We take data privacy and security seriously, ensuring your content is always protected.",
    },
    {
      icon: Star,
      title: "Excellence",
      description:
        "We strive for excellence in everything we do, from our product to our customer service.",
    },
  ];

  const team = [
    {
      name: "Sarah Johnson",
      role: "Chief Executive Officer",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=sarah",
      description:
        "Former Microsoft executive with 15+ years in product development.",
    },
    {
      name: "Michael Chen",
      role: "Chief Technology Officer",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=michael",
      description:
        "AI researcher and former Google engineer specializing in NLP.",
    },
    {
      name: "Emily Rodriguez",
      role: "Head of Design",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=emily",
      description:
        "Award-winning designer with expertise in user experience and visual design.",
    },
    {
      name: "David Kim",
      role: "Head of Engineering",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=david",
      description:
        "Full-stack engineer with extensive experience in scalable systems.",
    },
  ];

  const fadeInUp = {
    initial: { opacity: 0, y: 60 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  };

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Badge
            variant="secondary"
            className="mb-4 text-blue-600 bg-blue-100 dark:bg-blue-900/20"
          >
            🚀 About Us
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-6">
            Revolutionizing Presentations
            <span className="block">with AI Technology</span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            We're on a mission to democratize professional presentation design
            and make it accessible to everyone through the power of artificial
            intelligence.
          </p>
        </motion.div>

        {/* Stats */}
        <motion.div
          className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-20"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              className="text-center"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 + 0.4 }}
            >
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <stat.icon className="h-8 w-8 text-white" />
              </div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {stat.value}
              </div>
              <div className="text-gray-600 dark:text-gray-400">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Story Section */}
        <motion.div
          className="mb-20"
          variants={fadeInUp}
          initial="initial"
          animate="animate"
        >
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
                Our Story
              </h2>
              <div className="space-y-4 text-gray-600 dark:text-gray-300 text-lg leading-relaxed">
                <p>
                  Founded in 2023, PPT Generator AI was born from a simple
                  observation: creating professional presentations was taking
                  too much time and requiring too much design expertise.
                </p>
                <p>
                  Our founders, coming from backgrounds in AI research and
                  enterprise software, saw an opportunity to leverage artificial
                  intelligence to democratize presentation design and make it
                  accessible to everyone.
                </p>
                <p>
                  Today, we're proud to serve thousands of professionals
                  worldwide, helping them create stunning presentations in
                  minutes instead of hours.
                </p>
              </div>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-indigo-600/20 rounded-3xl transform rotate-3"></div>
              <div className="relative bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 rounded-3xl p-12 h-80 flex items-center justify-center">
                <TrendingUp className="h-24 w-24 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Values */}
        <motion.div
          className="mb-20"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Our Values
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-300">
              The principles that guide everything we do
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {values.map((value, index) => (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 + 0.8 }}
              >
                <Card className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border-0 shadow-lg h-full">
                  <CardContent className="p-8">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                      <value.icon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                      {value.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                      {value.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Team Section */}
        <motion.div
          className="mb-20"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1 }}
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Meet Our Team
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-300">
              The brilliant minds behind our platform
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {team.map((member, index) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 + 1.2 }}
              >
                <Card className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border-0 shadow-lg">
                  <CardContent className="p-6 text-center">
                    <img
                      src={member.avatar}
                      alt={member.name}
                      className="w-24 h-24 rounded-full mx-auto mb-4 group-hover:scale-110 transition-transform duration-300"
                    />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {member.name}
                    </h3>
                    <p className="text-blue-600 dark:text-blue-400 font-medium mb-3">
                      {member.role}
                    </p>
                    <p className="text-gray-600 dark:text-gray-300 text-sm leading-relaxed">
                      {member.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Mission Section */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.4 }}
        >
          <Card className="border-0 shadow-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
            <CardContent className="p-12">
              <Zap className="h-16 w-16 mx-auto mb-6" />
              <h2 className="text-3xl font-bold mb-4">Our Mission</h2>
              <p className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto leading-relaxed">
                To empower every professional with the tools they need to create
                stunning presentations effortlessly, regardless of their design
                background or technical expertise.
              </p>
              <div className="grid md:grid-cols-3 gap-8 text-center">
                <div>
                  <div className="text-3xl font-bold mb-2">10x</div>
                  <div className="text-blue-100">Faster Creation</div>
                </div>
                <div>
                  <div className="text-3xl font-bold mb-2">100%</div>
                  <div className="text-blue-100">Professional Quality</div>
                </div>
                <div>
                  <div className="text-3xl font-bold mb-2">∞</div>
                  <div className="text-blue-100">Creative Possibilities</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

export default About;
