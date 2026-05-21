import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  RefreshCw,
  Upload,
  Download,
  Loader,
  FileText,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { toast } from "react-hot-toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import api from "@/utils/axios";

function ConvertPPT() {
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [contentFile, setContentFile] = useState<File | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [convertedResult, setConvertedResult] = useState<string | null>(null);
  const [refinedResult, setRefinedResult] = useState<string | null>(null);
  const [isRefining, setIsRefining] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [refineProgress, setRefineProgress] = useState("");

  const handleTemplateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (
        file.type !==
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      ) {
        toast.error("Please upload a valid PowerPoint file (.pptx)");
        return;
      }
      setTemplateFile(file);
      toast.success("Template uploaded successfully");
    }
  };

  const handleContentChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (
        file.type !==
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      ) {
        toast.error("Please upload a valid PowerPoint file (.pptx)");
        return;
      }
      setContentFile(file);
      toast.success("Content file uploaded successfully");
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!templateFile) {
      toast.error("Please upload a template file");
      return;
    }
    if (!contentFile) {
      toast.error("Please upload a content file");
      return;
    }
    setIsConverting(true);
    try {
      const formData = new FormData();
      formData.append("template", templateFile);
      formData.append("content", contentFile);
      const token = sessionStorage.getItem("authToken");
      const response = await api.post(
        "/upload",
        formData,
        {
          responseType: "blob",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      // Download PPT
      const url = window.URL.createObjectURL(response.data);
      setConvertedResult(url);
      toast.success("🎉 PPT converted successfully!");
    } catch (error) {
      toast.error("❌ Failed to convert. Please try again.");
    } finally {
      setIsConverting(false);
    }
  };

  const handleRefine = async () => {
    if (!convertedResult || !contentFile) {
      toast.error("Please ensure you have a converted file and content file to refine");
      return;
    }
    setIsRefining(true);
    setRefinedResult(null);
    setRefineProgress("Analyzing slide backgrounds...");
    try {
      // Fetch the converted file blob
      const convertedBlob = await fetch(convertedResult).then(res => res.blob());
      const convertedFileObj = new File([convertedBlob], "converted.pptx", { type: convertedBlob.type });
      const formData = new FormData();
      formData.append("converted", convertedFileObj);
      formData.append("content", contentFile);
      setRefineProgress("Optimizing text positioning and formatting...");
      const token = sessionStorage.getItem("authToken");
      const headers = { Authorization: `Bearer ${token}` };
      const response = await api.post(
        "/refine",
        formData,
        { 
          responseType: "blob",
          headers: headers
        }
      );
      // Download refined PPT
      const url = window.URL.createObjectURL(response.data);
      setRefinedResult(url);
      toast.success("🎉 AI-enhanced PPT ready! Layout optimized with smart positioning and formatting.");
    } catch (err) {
      toast.error("Refinement failed");
    } finally {
      setIsRefining(false);
      setRefineProgress("");
    }
  };

  const handleDrop = (e: React.DragEvent, type: "template" | "content") => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (type === "template") {
      handleTemplateChange({ target: { files: [file] } } as any);
    } else {
      handleContentChange({ target: { files: [file] } } as any);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 relative">
      {/* Floating Refresh Button - top right */}
      <button
        onClick={() => window.location.reload()}
        className="fixed top-24 right-6 z-50 flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-full shadow-2xl border-2 border-white/40 hover:scale-105 hover:shadow-blue-400/60 hover:from-purple-600 hover:to-blue-600 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-blue-300 shadow-pulse"
        title="Refresh this page (reset all uploads)"
      >
        <RefreshCw className="h-5 w-5 animate-spin-slow" />
        Refresh
      </button>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Badge
            variant="secondary"
            className="mb-4 text-orange-600 bg-orange-100 dark:bg-orange-900/20"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Smart Conversion
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent mb-4">
            Convert Existing Presentation
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Transform your existing presentations with new templates while
            preserving your content structure and formatting.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="shadow-xl border-0">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-amber-600 rounded-xl flex items-center justify-center">
                    <Upload className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">
                      File Upload
                    </CardTitle>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Upload your template and content files
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="template">Template PPT *</Label>
                    <div
                      className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all duration-300 ${
                        isDragOver
                          ? "border-orange-500 bg-orange-50 dark:bg-orange-900/20"
                          : templateFile
                            ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                            : "border-gray-300 hover:border-gray-400"
                      }`}
                      onDrop={(e) => handleDrop(e, "template")}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                    >
                      {templateFile ? (
                        <div className="space-y-2">
                          <CheckCircle className="h-8 w-8 text-green-500 mx-auto" />
                          <p className="text-green-800 dark:text-green-200 font-medium">
                            {templateFile.name}
                          </p>
                          <p className="text-green-600 dark:text-green-400 text-sm">
                            {(templateFile.size / (1024 * 1024)).toFixed(2)} MB
                          </p>
                          <button
                            type="button"
                            onClick={() => setTemplateFile(null)}
                            className="text-red-500 hover:text-red-700 text-sm font-medium"
                          >
                            Remove file
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <Upload className="h-8 w-8 text-gray-400 mx-auto" />
                          <p className="text-gray-600 dark:text-gray-300 font-medium">
                            Drop template here or click to browse
                          </p>
                          <p className="text-gray-500 dark:text-gray-400 text-sm">
                            PowerPoint template (.pptx)
                          </p>
                          <Input
                            id="template"
                            type="file"
                            accept=".pptx"
                            onChange={handleTemplateChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            required
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="content">Content File *</Label>
                    <div
                      className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all duration-300 ${
                        isDragOver
                          ? "border-orange-500 bg-orange-50 dark:bg-orange-900/20"
                          : contentFile
                            ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                            : "border-gray-300 hover:border-gray-400"
                      }`}
                      onDrop={(e) => handleDrop(e, "content")}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                    >
                      {contentFile ? (
                        <div className="space-y-2">
                          <CheckCircle className="h-8 w-8 text-green-500 mx-auto" />
                          <p className="text-green-800 dark:text-green-200 font-medium">
                            {contentFile.name}
                          </p>
                          <p className="text-green-600 dark:text-green-400 text-sm">
                            {(contentFile.size / (1024 * 1024)).toFixed(2)} MB
                          </p>
                          <button
                            type="button"
                            onClick={() => setContentFile(null)}
                            className="text-red-500 hover:text-red-700 text-sm font-medium"
                          >
                            Remove file
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <Upload className="h-8 w-8 text-gray-400 mx-auto" />
                          <p className="text-gray-600 dark:text-gray-300 font-medium">
                            Drop content file here or click to browse
                          </p>
                          <p className="text-gray-500 dark:text-gray-400 text-sm">
                            Existing presentation (.pptx)
                          </p>
                          <Input
                            id="content"
                            type="file"
                            accept=".pptx"
                            onChange={handleContentChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            required
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                      <div className="text-sm text-amber-800 dark:text-amber-200">
                        <p className="font-medium mb-1">How it works:</p>
                        <ul className="space-y-1 text-xs">
                          <li>
                            • Template file provides the design and styling
                          </li>
                          <li>
                            • Content file provides the text and structure
                          </li>
                          <li>
                            • Our AI merges them intelligently while preserving
                            your content
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <Button
                    type="submit"
                    disabled={isConverting || !templateFile || !contentFile}
                    className="w-full bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white shadow-lg hover:shadow-xl transition-all duration-300"
                    size="lg"
                  >
                    {isConverting ? (
                      <>
                        <Loader className="h-5 w-5 mr-2 animate-spin" />
                        Converting Presentation...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-5 w-5 mr-2" />
                        Convert Presentation
                      </>
                    )}
                  </Button>
                </form>

                {isConverting && (
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
                    <div className="flex items-center space-x-3">
                      <Loader className="w-5 h-5 text-blue-500 animate-spin" />
                      <div>
                        <p className="text-blue-800 dark:text-blue-200 font-medium">
                          Converting your presentation...
                        </p>
                        <p className="text-blue-700 dark:text-blue-300 text-sm">
                          Applying new template while preserving content
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Result Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Card className="shadow-xl border-0">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                    <FileText className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">
                      Converted Presentation
                    </CardTitle>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Your converted presentation will appear here
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {convertedResult ? (
                  <div className="space-y-4">
                    <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl text-center">
                      <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-2">
                        Conversion Completed Successfully!
                      </h3>
                      <p className="text-green-700 dark:text-green-300 mb-4">
                        Your presentation has been converted with the new
                        template.
                      </p>
                      <Button className="bg-green-600 hover:bg-green-700 text-white" onClick={() => {
  if (convertedResult) {
    const a = document.createElement("a");
    a.href = convertedResult;
    a.download = "converted_presentation.pptx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(convertedResult);
  }
}} disabled={!convertedResult}>
                        <Download className="h-4 w-4 mr-2" />
                        Download Converted PPT
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400">
                      Your converted presentation will appear here
                    </p>
                  </div>
                )}
                {convertedResult && (
                  <Button
                    className="bg-purple-600 hover:bg-purple-700 text-white mt-4"
                    onClick={handleRefine}
                    disabled={isRefining}
                  >
                    {isRefining ? (
                      <>
                        <Loader className="h-4 w-4 mr-2 animate-spin" />
                        Refining with AI...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refine with AI
                      </>
                    )}
                  </Button>
                )}
                {refinedResult && (
                  <Button className="bg-purple-600 hover:bg-purple-700 text-white mt-4" onClick={() => {
                    const a = document.createElement("a");
                    a.href = refinedResult;
                    a.download = "refined_presentation.pptx";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(refinedResult);
                  }}>
                    <Download className="h-4 w-4 mr-2" />
                    Download Refined PPT
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Info Cards */}
        <motion.div
          className="grid md:grid-cols-3 gap-6 mt-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <Card className="text-center shadow-lg border-0">
            <CardContent className="p-6">
              <RefreshCw className="h-8 w-8 text-orange-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Smart Conversion
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Intelligently merge template design with your existing content
              </p>
            </CardContent>
          </Card>
          <Card className="text-center shadow-lg border-0">
            <CardContent className="p-6">
              <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Content Preservation
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Keep all your text, images, and structure intact during
                conversion
              </p>
            </CardContent>
          </Card>
          <Card className="text-center shadow-lg border-0">
            <CardContent className="p-6">
              <Download className="h-8 w-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Professional Results
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Get polished presentations with consistent professional styling
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

export default ConvertPPT;
