import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Sparkles,
  Upload,
  Download,
  Loader,
  FileText,
  Brain,
  Wand2,
  CheckCircle,
  AlertCircle,
  Settings,
  Image,
  Layout,
} from "lucide-react";
import { toast } from "react-hot-toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import api from "@/utils/axios";

function GeneratePPT() {
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [numSlides, setNumSlides] = useState([5]); // Default 5 slides
  const [layoutPreference, setLayoutPreference] = useState("auto");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResult, setGeneratedResult] = useState<string | null>(null);
  const [templates, setTemplates] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  React.useEffect(() => {
    // Fetch templates from backend
    const fetchTemplates = async () => {
      try {
        const response = await api.get("/get-templates");
        setTemplates(response.data.templates);
      } catch (error) {
        toast.error("Failed to fetch templates");
      }
    };
    fetchTemplates();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!topic.trim()) {
      toast.error("Please enter a topic");
      return;
    }

    if (!templateFile && !selectedTemplate) {
      toast.error("Please select or upload a template");
      return;
    }

    setIsGenerating(true);

    try {
      const formData = new FormData();
      formData.append("topic", topic);
      if (description.trim()) {
        formData.append("prompt_description", description.trim());
      }
      formData.append("num_slides", numSlides[0].toString());
      formData.append("layout_preference", layoutPreference);
      
      if (templateFile) {
        formData.append("template", templateFile);
      } else if (selectedTemplate) {
        formData.append("template_name", selectedTemplate);
      }
      
      const token = sessionStorage.getItem("authToken");
      const response = await api.post(
        "/generate-ppt-ai-enhanced",
        formData,
        {
          responseType: "blob",
          timeout: 180000,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      // Download PPT
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "Enhanced_AI_PPT.pptx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setGeneratedResult("Enhanced_AI_PPT.pptx");
      toast.success("✅ Enhanced PPT Generated and Downloaded!");
    } catch (error) {
      toast.error("Failed to generate PPT");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
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
      toast.success("✅ Template uploaded successfully");
    }
  };

  const layoutOptions = [
    { value: "auto", label: "Auto (AI decides best)", icon: "🤖" },
    { value: "title-content", label: "Title & Content", icon: "📝" },
    { value: "image-left", label: "Image Left, Text Right", icon: "🖼️" },
    { value: "image-right", label: "Image Right, Text Left", icon: "📄" },
    { value: "full-image", label: "Full Image Background", icon: "🎨" },
    { value: "two-column", label: "Two Column Layout", icon: "📊" },
  ];

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
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
            className="mb-4 text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Enhanced AI-Powered Generation
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent mb-4">
            Generate Enhanced PPT with AI
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Create professional presentations with custom layouts, slide counts, and perfect content fitting.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="shadow-xl border-0">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
                    <Sparkles className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">
                      Enhanced AI Content Generation
                    </CardTitle>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Customize your presentation with advanced options
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="topic">Presentation Topic *</Label>
                    <div className="relative">
                      <Input
                        id="topic"
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="e.g., Digital Marketing Strategy, AI in Healthcare"
                        className="pl-10"
                        required
                      />
                      <Brain className="absolute left-3 top-3 h-4 w-4 text-emerald-500" />
                    </div>
                    <p className="text-xs text-gray-500">
                      Be specific for better AI-generated content
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">Detailed Description / Instructions (Optional)</Label>
                    <div className="relative">
                      <Textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="e.g., Target audience is beginners. Focus on step-by-step concepts, avoid complex jargon..."
                        className="pl-10 min-h-[100px]"
                      />
                      <FileText className="absolute left-3 top-3 h-4 w-4 text-emerald-500" />
                    </div>
                    <p className="text-xs text-gray-500">
                      Provide specific instructions for the AI on how to write the content
                    </p>
                  </div>

                  {/* Number of Slides */}
                  <div className="space-y-2">
                    <Label>Number of Slides: {numSlides[0]}</Label>
                    <div className="px-2">
                      <Slider
                        value={numSlides}
                        onValueChange={setNumSlides}
                        max={20}
                        min={1}
                        step={1}
                        className="w-full"
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>1 slide</span>
                      <span>20 slides</span>
                    </div>
                    <p className="text-xs text-gray-500">
                      Choose how many slides you want in your presentation
                    </p>
                  </div>

                  {/* Layout Preference */}
                  <div className="space-y-2">
                    <Label>Layout Preference</Label>
                    <Select
                      value={layoutPreference}
                      onValueChange={setLayoutPreference}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choose layout style" />
                      </SelectTrigger>
                      <SelectContent>
                        {layoutOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            <div className="flex items-center space-x-2">
                              <span>{option.icon}</span>
                              <span>{option.label}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500">
                      Select how content should be arranged on slides
                    </p>
                  </div>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-white dark:bg-gray-900 text-gray-500 font-medium">
                        Template Selection
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Select Template</Label>
                    <Select
                      value={selectedTemplate}
                      onValueChange={setSelectedTemplate}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choose from available templates" />
                      </SelectTrigger>
                      <SelectContent>
                        {templates.map((template) => (
                          <SelectItem key={template} value={template}>
                            {template}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500">
                      Select from our curated template collection
                    </p>
                  </div>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-white dark:bg-gray-900 text-gray-500 font-medium">
                        OR
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="template">Upload Custom Template</Label>
                    <div className="relative">
                      <Input
                        id="template"
                        type="file"
                        accept=".pptx"
                        onChange={handleFileChange}
                        className="cursor-pointer"
                      />
                      {templateFile && (
                        <div className="absolute right-3 top-3">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-gray-500">
                      Upload your own PowerPoint template (.pptx)
                    </p>
                  </div>

                  {templateFile && (
                    <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl">
                      <div className="flex items-center space-x-3">
                        <CheckCircle className="h-5 w-5 text-emerald-600" />
                        <div>
                          <p className="text-emerald-800 dark:text-emerald-200 font-medium">
                            Template uploaded: {templateFile.name}
                          </p>
                          <p className="text-emerald-700 dark:text-emerald-300 text-sm">
                            Ready for enhanced AI content generation
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <Button
                    type="submit"
                    disabled={isGenerating || !topic.trim()}
                    className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white shadow-lg hover:shadow-xl transition-all duration-300"
                    size="lg"
                  >
                    {isGenerating ? (
                      <>
                        <Loader className="h-5 w-5 mr-2 animate-spin" />
                        Generating Enhanced AI Content...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-5 w-5 mr-2" />
                        Generate Enhanced AI Content
                      </>
                    )}
                  </Button>
                </form>

                {isGenerating && (
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
                    <div className="flex items-center space-x-3">
                      <Loader className="w-5 h-5 text-blue-500 animate-spin" />
                      <div>
                        <p className="text-blue-800 dark:text-blue-200 font-medium">
                          AI is creating your enhanced presentation...
                        </p>
                        <p className="text-blue-700 dark:text-blue-300 text-sm">
                          Generating {numSlides[0]} slides with {layoutPreference} layout
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
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                    <FileText className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">
                      Enhanced Presentation
                    </CardTitle>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Your AI-generated presentation with custom layout
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {generatedResult ? (
                  <div className="space-y-4">
                    <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl text-center">
                      <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-2">
                        Enhanced Presentation Generated!
                      </h3>
                      <p className="text-green-700 dark:text-green-300 mb-4">
                        Your AI-powered presentation with custom layout is ready.
                      </p>
                      <div className="text-sm text-green-600 dark:text-green-400 mb-4">
                        <p>• {numSlides[0]} slides generated</p>
                        <p>• {layoutPreference} layout applied</p>
                        <p>• Perfect content fitting</p>
                        <p>• Auto-contrast text coloring</p>
                      </div>
                      <Button className="bg-green-600 hover:bg-green-700 text-white" onClick={() => {
  if (generatedResult) {
    // Already downloaded
    return;
  }
}} disabled={!generatedResult}>
                        <Download className="h-4 w-4 mr-2" />
                        Download Enhanced PPT
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400">
                      Your enhanced presentation will appear here
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Info Cards */}
        <motion.div
          className="grid md:grid-cols-4 gap-6 mt-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <Card className="text-center shadow-lg border-0">
            <CardContent className="p-6">
              <Settings className="h-8 w-8 text-emerald-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Customizable Options
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Choose slide count, layout style, and content arrangement
              </p>
            </CardContent>
          </Card>
          <Card className="text-center shadow-lg border-0">
            <CardContent className="p-6">
              <Layout className="h-8 w-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Smart Layout Fitting
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Content automatically fits perfectly to your chosen template
              </p>
            </CardContent>
          </Card>
          <Card className="text-center shadow-lg border-0">
            <CardContent className="p-6">
              <Image className="h-8 w-8 text-purple-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Enhanced Visuals
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Professional images and perfect text-image alignment
              </p>
            </CardContent>
          </Card>
          <Card className="text-center shadow-lg border-0">
            <CardContent className="p-6">
              <CheckCircle className="h-8 w-8 text-orange-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Auto Contrast
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Text color automatically adjusts for perfect readability
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

export default GeneratePPT;
