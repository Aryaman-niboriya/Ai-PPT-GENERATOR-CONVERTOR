import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  HelpCircle,
  MessageSquare,
  Send,
  Star,
  Book,
  Video,
  Mail,
  Phone,
  ExternalLink,
  ChevronRight,
  Search,
  X,
  MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { toast } from "react-hot-toast";

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose }) => {
  const [feedbackForm, setFeedbackForm] = useState({
    type: "feedback",
    email: "",
    subject: "",
    message: "",
    rating: 0,
  });
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [contactForm, setContactForm] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [contactLoading, setContactLoading] = useState(false);

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

  const faqs = [
    {
      question: "How do I generate a presentation with AI?",
      answer:
        "Go to the Generate page, enter your topic, select or upload a template, and click 'Generate AI Content'. Our AI will create a structured presentation for you.",
    },
    {
      question: "What file formats are supported?",
      answer:
        "We support PowerPoint files (.pptx) for both templates and content files. All generated presentations are also provided in .pptx format.",
    },
    {
      question: "Can I customize the generated presentations?",
      answer:
        "Yes! You can use your own templates or choose from our library. The AI adapts the content to match your template's design and style.",
    },
    {
      question: "How do I convert existing presentations?",
      answer:
        "Upload your template file and content file on the Convert page. Our system will merge them while preserving your content and applying the new design.",
    },
    {
      question: "Is my data secure?",
      answer:
        "Absolutely! We use enterprise-grade encryption and security protocols. Your files are processed securely and deleted after conversion.",
    },
    {
      question: "What's the file size limit?",
      answer:
        "Currently, we support files up to 10MB in size. This covers most presentation needs while ensuring fast processing.",
    },
  ];

  const tutorials = [
    {
      title: "Getting Started Guide",
      description: "Learn the basics of creating your first presentation",
      duration: "5 min",
      type: "video",
    },
    {
      title: "AI Content Generation",
      description: "How to get the best results from our AI",
      duration: "3 min",
      type: "article",
    },
    {
      title: "Template Conversion",
      description: "Convert existing presentations with new designs",
      duration: "4 min",
      type: "video",
    },
    {
      title: "Best Practices",
      description: "Tips for creating professional presentations",
      duration: "6 min",
      type: "article",
    },
  ];

  const filteredFaqs = faqs.filter(
    (faq) =>
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5050/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackForm),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(data.message || "Thank you for your feedback! We appreciate your input.");
      setFeedbackForm({
        type: "feedback",
          email: "",
        subject: "",
        message: "",
        rating: 0,
      });
      } else {
        toast.error(data.error || "Failed to send feedback. Please try again.");
      }
    } catch (error) {
      console.error('Feedback form error:', error);
      toast.error("Failed to send feedback. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleContactSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setContactLoading(true);

    try {
      const response = await fetch('http://localhost:5050/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(contactForm),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(data.message || "Thank you for your message! We'll get back to you soon.");
        setContactForm({
          name: "",
          email: "",
          subject: "",
          message: "",
        });
      } else {
        toast.error(data.error || "Failed to send message. Please try again.");
      }
    } catch (error) {
      console.error('Contact form error:', error);
      toast.error("Failed to send message. Please try again.");
    } finally {
      setContactLoading(false);
    }
  };

  const handleClose = () => {
    // Reset body styles
    document.body.style.overflow = 'auto';
    document.body.style.pointerEvents = 'auto';
    onClose();
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setFeedbackForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleContactInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setContactForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

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
            className="relative bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <HelpCircle className="h-6 w-6 text-blue-600" />
                Help & Support
              </h2>
              <button
                onClick={handleClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              <Tabs defaultValue="faq" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="faq">FAQ</TabsTrigger>
                  <TabsTrigger value="tutorials">Tutorials</TabsTrigger>
                  <TabsTrigger value="contact">Contact</TabsTrigger>
                  <TabsTrigger value="feedback">Feedback</TabsTrigger>
                </TabsList>

                {/* FAQ Tab */}
                <TabsContent value="faq" className="space-y-6">
                  <div className="space-y-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Search frequently asked questions..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>

                    <Accordion type="single" collapsible className="w-full">
                      {filteredFaqs.map((faq, index) => (
                        <AccordionItem key={index} value={`item-${index}`}>
                          <AccordionTrigger className="text-left">
                            {faq.question}
                          </AccordionTrigger>
                          <AccordionContent className="text-gray-600 dark:text-gray-300">
                            {faq.answer}
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>

                    {filteredFaqs.length === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        No FAQ found matching your search. Try different keywords or
                        contact support.
                      </div>
                    )}
                  </div>
                </TabsContent>

                {/* Tutorials Tab */}
                <TabsContent value="tutorials" className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    {tutorials.map((tutorial, index) => (
                      <Card key={index} className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-lg">{tutorial.title}</CardTitle>
                            <Badge variant="secondary">{tutorial.duration}</Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-gray-600 dark:text-gray-400 mb-4">
                            {tutorial.description}
                          </p>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {tutorial.type === "video" ? (
                                <Video className="h-4 w-4 text-blue-600" />
                              ) : (
                                <Book className="h-4 w-4 text-green-600" />
                              )}
                              <span className="text-sm text-gray-500 capitalize">
                                {tutorial.type}
                              </span>
                            </div>
                            <Button variant="outline" size="sm">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Watch
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                {/* Contact Tab */}
                <TabsContent value="contact" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Mail className="h-5 w-5" />
                        Contact Us
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleContactSubmit} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Name</Label>
                          <Input
                            id="name"
                            name="name"
                            value={contactForm.name}
                            onChange={handleContactInputChange}
                            placeholder="Your full name"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="contactEmail">Email</Label>
                          <Input
                            id="contactEmail"
                            name="email"
                            type="email"
                            value={contactForm.email}
                            onChange={handleContactInputChange}
                            placeholder="your.email@example.com"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="contactSubject">Subject</Label>
                          <Input
                            id="contactSubject"
                            name="subject"
                            value={contactForm.subject}
                            onChange={handleContactInputChange}
                            placeholder="Brief description of your inquiry"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="contactMessage">Message</Label>
                          <Textarea
                            id="contactMessage"
                            name="message"
                            value={contactForm.message}
                            onChange={handleContactInputChange}
                            placeholder="Tell us more about your inquiry..."
                            rows={4}
                            required
                          />
                        </div>

                        <Button
                          type="submit"
                          disabled={contactLoading}
                          className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white"
                        >
                          {contactLoading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                              Sending...
                            </>
                          ) : (
                            <>
                              <Send className="h-4 w-4 mr-2" />
                              Send Message
                            </>
                          )}
                        </Button>
                      </form>
                    </CardContent>
                  </Card>

                  <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Phone className="h-5 w-5" />
                          Phone Support
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-gray-600 dark:text-gray-400">
                          Call us directly for immediate assistance.
                        </p>
                        <div className="space-y-2">
                          <p className="font-medium">+91 7697773087</p>
                          <p className="text-sm text-gray-500">
                            Available: 9 AM - 6 PM (IST)
                          </p>
                        </div>
                        <Button 
                          className="w-full"
                          onClick={() => {
                            window.open('tel:+917697773087', '_blank');
                          }}
                        >
                          <Phone className="h-4 w-4 mr-2" />
                          Call Now
                        </Button>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <MapPin className="h-5 w-5" />
                          Location
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-gray-600 dark:text-gray-400">
                          Visit our office for in-person support.
                        </p>
                        <div className="space-y-2">
                          <p className="font-medium">MP Gwalior 474004</p>
                          <p className="text-sm text-gray-500">
                            Madhya Pradesh, India
                          </p>
                        </div>
                        <Button 
                          className="w-full"
                          onClick={() => {
                            window.open('https://maps.google.com/?q=Gwalior,Madhya+Pradesh,India', '_blank');
                          }}
                        >
                          <MapPin className="h-4 w-4 mr-2" />
                          View on Map
                        </Button>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* Feedback Tab */}
                <TabsContent value="feedback" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Star className="h-5 w-5" />
                        Send Feedback
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleFeedbackSubmit} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="subject">Subject</Label>
                          <Input
                            id="subject"
                            name="subject"
                            value={feedbackForm.subject}
                            onChange={handleInputChange}
                            placeholder="Brief description of your feedback"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="message">Message</Label>
                          <Textarea
                            id="message"
                            name="message"
                            value={feedbackForm.message}
                            onChange={handleInputChange}
                            placeholder="Tell us more about your experience..."
                            rows={4}
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="email">Email (optional)</Label>
                          <Input
                            id="email"
                            name="email"
                            type="email"
                            value={feedbackForm.email}
                            onChange={handleInputChange}
                            placeholder="Your email address"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>Rating</Label>
                          <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <button
                                key={star}
                                type="button"
                                onClick={() =>
                                  setFeedbackForm((prev) => ({ ...prev, rating: star }))
                                }
                                className={`p-1 rounded transition-colors ${
                                  feedbackForm.rating >= star
                                    ? "text-yellow-500"
                                    : "text-gray-300 hover:text-yellow-400"
                                }`}
                              >
                                <Star className="h-6 w-6 fill-current" />
                              </button>
                            ))}
                          </div>
                        </div>

                        <Button
                          type="submit"
                          disabled={loading}
                          className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white"
                        >
                          {loading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                              Sending...
                            </>
                          ) : (
                            <>
                              <Send className="h-4 w-4 mr-2" />
                              Send Feedback
                            </>
                          )}
                        </Button>
                      </form>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default HelpModal;
