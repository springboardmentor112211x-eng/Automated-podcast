"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Mic2, 
  FileText, 
  Layers, 
  Tag, 
  Download, 
  ArrowRight,
  CheckCircle2,
  Cpu,
  Zap,
  Shield
} from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative py-24 md:py-32 overflow-hidden bg-slate-50 dark:bg-zinc-950">
        <div className="absolute inset-0 z-0 opacity-30 dark:opacity-20">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob" />
          <div className="absolute top-0 -right-4 w-72 h-72 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000" />
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000" />
        </div>
        
        <div className="container relative z-10 px-4 md:px-6">
          <div className="flex flex-col items-center space-y-8 text-center">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center rounded-full border px-4 py-1.5 text-sm font-medium bg-white/50 dark:bg-zinc-900/50 backdrop-blur-sm"
            >
              <span className="flex h-2 w-2 rounded-full bg-blue-600 mr-2" />
              Revolutionizing Podcast Content
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-4xl font-extrabold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl max-w-4xl"
            >
              Transform Your Podcasts into <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Actionable Knowledge</span>
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mx-auto max-w-[700px] text-zinc-500 md:text-xl dark:text-zinc-400"
            >
              Automated transcription, topic segmentation, and smart classification. Get SRTs, JSON, and podcast chapters in seconds.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="flex flex-col sm:flex-row gap-4"
            >
              <Link href="/dashboard">
                <Button size="lg" className="h-12 px-8 text-lg rounded-full shadow-lg shadow-blue-500/20 bg-blue-600 hover:bg-blue-700 transition-all">
                  Get Started Free <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="h-12 px-8 text-lg rounded-full backdrop-blur-sm">
                View Demo
              </Button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white dark:bg-black">
        <div className="container px-4 md:px-6">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">Engineered for Accuracy</h2>
            <p className="mx-auto max-w-[600px] text-zinc-500 dark:text-zinc-400">
              Our AI models are trained on thousands of hours of speech to provide industry-leading results.
            </p>
          </div>
          
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {[
              {
                title: "Auto-Transcription",
                desc: "High-fidelity text conversion with speaker diarization and timestamps.",
                icon: FileText,
                color: "text-blue-500"
              },
              {
                title: "Topic Segmentation",
                desc: "Intelligently detects when topics shift to create natural break points.",
                icon: Layers,
                color: "text-indigo-500"
              },
              {
                title: "Smart Classification",
                desc: "Automatically categorize content into Tech, Politics, Sports, and more.",
                icon: Tag,
                color: "text-purple-500"
              },
              {
                title: "Multi-Export",
                desc: "Download in JSON, SRT, CSV, or formatted Podcast Chapters.",
                icon: Download,
                color: "text-pink-500"
              }
            ].map((feature, idx) => (
              <motion.div key={idx} variants={itemVariants}>
                <Card className="border-none shadow-md hover:shadow-xl transition-shadow bg-zinc-50 dark:bg-zinc-900 overflow-hidden group">
                  <CardContent className="p-8">
                    <div className={`p-3 rounded-2xl bg-white dark:bg-zinc-800 w-fit mb-6 shadow-sm group-hover:scale-110 transition-transform ${feature.color}`}>
                      <feature.icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
                      {feature.desc}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 border-y bg-zinc-50/50 dark:bg-zinc-950/50">
        <div className="container px-4 md:px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { label: "Transcription Accuracy", value: "98.5%" },
              { label: "Processing Speed", value: "10x" },
              { label: "Users Worldwide", value: "50k+" },
              { label: "Podcasts Processed", value: "1M+" }
            ].map((stat, idx) => (
              <div key={idx} className="space-y-2">
                <h4 className="text-3xl md:text-4xl font-bold text-blue-600">{stat.value}</h4>
                <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-24 bg-white dark:bg-black overflow-hidden">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col md:flex-row gap-16 items-center">
            <div className="flex-1 space-y-6">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">From Audio to Insights in 3 Steps</h2>
              <div className="space-y-8">
                {[
                  {
                    step: "01",
                    title: "Upload Audio",
                    desc: "Drag and drop your MP3, WAV, or M4A file directly into the dashboard."
                  },
                  {
                    step: "02",
                    title: "AI Processing",
                    desc: "Our neural networks transcribe and analyze your content in real-time."
                  },
                  {
                    step: "03",
                    title: "Review & Export",
                    desc: "Fine-tune segments and download in your preferred format."
                  }
                ].map((item, idx) => (
                  <div key={idx} className="flex gap-4">
                    <span className="text-4xl font-black text-zinc-100 dark:text-zinc-800 tabular-nums">
                      {item.step}
                    </span>
                    <div className="space-y-1">
                      <h4 className="text-xl font-bold">{item.title}</h4>
                      <p className="text-zinc-500 dark:text-zinc-400">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
              <Link href="/dashboard" className="inline-block mt-4">
                <Button variant="link" className="px-0 text-blue-600 text-lg hover:text-blue-700 p-0">
                  Try it yourself now <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>
            <div className="flex-1 relative">
              <div className="absolute inset-0 bg-blue-600/10 blur-3xl rounded-full" />
              <div className="relative border rounded-2xl bg-white dark:bg-zinc-900 shadow-2xl p-4 overflow-hidden">
                <div className="flex items-center gap-2 mb-4 border-b pb-4">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                  <div className="h-4 w-32 bg-zinc-100 dark:bg-zinc-800 rounded mx-auto" />
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-4 bg-blue-100 dark:bg-blue-900/30 rounded" />
                    <div className="flex-1 h-4 bg-zinc-100 dark:bg-zinc-800 rounded" />
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-4 bg-blue-100 dark:bg-blue-900/30 rounded" />
                    <div className="flex-1 h-4 bg-zinc-100 dark:bg-zinc-800 rounded w-2/3" />
                  </div>
                  <div className="h-24 bg-blue-50 dark:bg-blue-900/10 rounded-lg flex items-center justify-center border border-blue-100 dark:border-blue-900/30">
                    <div className="text-center">
                      <Zap className="h-6 w-6 text-blue-600 mx-auto mb-2" />
                      <span className="text-xs font-medium text-blue-600">Detecting Topic: Artificial Intelligence</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-4 bg-blue-100 dark:bg-blue-900/30 rounded" />
                    <div className="flex-1 h-4 bg-zinc-100 dark:bg-zinc-800 rounded" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-blue-600 text-white">
        <div className="container px-4 md:px-6 text-center space-y-8">
          <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">Ready to unlock your podcast's potential?</h2>
          <p className="mx-auto max-w-[600px] text-blue-100 text-lg md:text-xl">
            Join thousands of creators who use PodScribe AI to save time and reach more listeners.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-zinc-100 h-14 px-10 rounded-full text-lg font-bold">
                Start Transcribing Now
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t bg-zinc-50 dark:bg-zinc-950">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center space-x-2">
              <Mic2 className="h-6 w-6 text-blue-600" />
              <span className="font-bold text-xl">PodScribe AI</span>
            </div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              © {new Date().getFullYear()} PodScribe AI. All rights reserved.
            </p>
            <div className="flex gap-6">
              <Link href="#" className="text-sm text-zinc-500 hover:text-blue-600 transition-colors">Privacy</Link>
              <Link href="#" className="text-sm text-zinc-500 hover:text-blue-600 transition-colors">Terms</Link>
              <Link href="#" className="text-sm text-zinc-500 hover:text-blue-600 transition-colors">Contact</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
