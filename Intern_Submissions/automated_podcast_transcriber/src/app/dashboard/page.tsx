"use client";

import React, { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { 
  Upload, 
  FileAudio, 
  X, 
  Download, 
  FileText, 
  Tag, 
  Play, 
  Loader2,
  Mic2,
  BarChart3,
  Table as TableIcon,
  Volume2,
  Database,
  ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

// Types
interface TranscriptionSegment {
  start: number;
  end: number;
  text: string;
}

interface TopicSegment {
  id: number;
  name: string;
  startTime: number;
  endTime: number;
  text: string;
  category: string;
  confidence: number;
}

interface AnalysisResults {
  transcription: TranscriptionSegment[];
  topics: TopicSegment[];
  full_text: string;
  metadata: {
    accuracy: number;
    duration: number;
  };
}

const API_BASE = "/api";

const PROCESSING_STEPS = [
  "Preprocessing Audio",
  "Whisper Transcription",
  "Topic Segmentation",
  "ML Classification",
  "Generating Assets"
];

const PEOPLES_SPEECH_SAMPLES = [
  { id: 'ps-1', name: 'Tech Talk: Neural Nets', duration: '12:45', size: '14MB' },
  { id: 'ps-2', name: 'Weather Report: Global Trends', duration: '05:22', size: '6MB' },
  { id: 'ps-3', name: 'History Podcast: Industrial Era', duration: '45:10', size: '52MB' },
  { id: 'ps-4', name: 'Health Weekly: Sleep Science', duration: '28:15', size: '31MB' },
  { id: 'ps-5', name: 'MLCommons: Dataset Overview', duration: '18:30', size: '20MB' },
];

const ALLOWED_TYPES = ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/mp4', 'audio/ogg', 'audio/flac', 'audio/webm'];
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

const validateFile = (file: File): { valid: boolean; error?: string } => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  const allowedExts = ['mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm'];
  
  if (!ext || !allowedExts.includes(ext)) {
    return { valid: false, error: `Unsupported format. Allowed: ${allowedExts.join(', ')}` };
  }
  
  if (file.size === 0) {
    return { valid: false, error: 'File is empty' };
  }
  
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: `File too large. Maximum: ${MAX_FILE_SIZE / (1024*1024)}MB` };
  }
  
  return { valid: true };
};

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "processing" | "completed" | "error">("idle");
  const [backendStatus, setBackendStatus] = useState<string>("");
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [liveTranscription, setLiveTranscription] = useState<TranscriptionSegment[]>([]);
  const [liveTopics, setLiveTopics] = useState<TopicSegment[]>([]);
  const [activeTopic, setActiveTopic] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    if (jobId && status === "processing") {
      const eventSource = new EventSource(`${API_BASE}/ws/${jobId}`);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "update") {
            setLiveTranscription(prev => [...prev, ...data.new_segments]);
            setLiveTopics(prev => [...prev, ...data.new_topics]);
            setProgress(data.progress);
            setCurrentTime(data.current_time);
            setBackendStatus(`Live: ${Math.floor(data.current_time)}s / Topic: ${data.new_topics.length > 0 ? data.new_topics[0].category : 'Analyzing...'}`);
          } else if (data.type === "final") {
            setStatus("completed");
            setResults(data.result);
            toast.success("Analysis complete!");
            eventSource.close();
          } else if (data.type === "error") {
            setStatus("error");
            toast.error("Analysis failed: " + data.error);
            eventSource.close();
          }
        } catch (e) {
          console.error("SSE parse error:", e);
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE connection error:", error);
        eventSource.close();
      };

      return () => eventSource.close();
    }
  }, [jobId, status]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      const validation = validateFile(selectedFile);
      
      if (!validation.valid) {
        toast.error(validation.error);
        return;
      }
      
      setFile(selectedFile);
      toast.success(`Ready to analyze: ${selectedFile.name} (${(selectedFile.size / (1024*1024)).toFixed(1)}MB)`);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'audio/*': ['.mp3', '.wav', '.m4a'] },
    multiple: false
  });

  const handleStartProcessing = async () => {
    if (!file) return;
    
    setStatus("uploading");
    setLiveTranscription([]);
    setLiveTopics([]);
    setProgress(0);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      console.log(`Uploading file: ${file.name}, size: ${file.size}, type: ${file.type}`);
      
      const res = await fetch(`${API_BASE}/upload`, { 
        method: "POST", 
        body: formData 
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || `Upload failed: ${res.status}`);
      }
      
      const data = await res.json();
      console.log("Upload successful:", data);
      
      setJobId(data.job_id);
      setStatus("processing");
      toast.success("Upload complete! Processing started...");
    } catch (err: any) {
      console.error("Upload error:", err);
      setStatus("error");
      toast.error(err.message || "Failed to upload audio file");
    }
  };

  const handleTryDemo = async (sample: typeof PEOPLES_SPEECH_SAMPLES[0]) => {
    toast.info(`Starting demo: ${sample.name}...`);
    
    setStatus("uploading");
    setLiveTranscription([]);
    setLiveTopics([]);
    setProgress(0);
    setFile(null);
    
    try {
      const res = await fetch(`${API_BASE}/demo/start`, { 
        method: "POST"
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Demo failed to start' }));
        throw new Error(errorData.detail || `Demo failed: ${res.status}`);
      }
      
      const data = await res.json();
      console.log("Demo started:", data);
      
      const demoFile = new File(["demo"], sample.name + ".mp3", { type: "audio/mpeg" });
      setFile(demoFile);
      setJobId(data.job_id);
      setStatus("processing");
      toast.success("Demo started! Watch the live transcription...");
    } catch (err: any) {
      console.error("Demo error:", err);
      setStatus("error");
      toast.error(err.message || "Failed to start demo");
    }
  };

  const handleDownload = async (format: string) => {
    if (!jobId) return;
    try {
      const res = await fetch(`${API_BASE}/download/${jobId}/${format}`);
      const data = await res.json();
      
      let blob: Blob;
      let filename: string;
      
      if (format === 'json') {
        blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        filename = `analysis_${jobId}.json`;
      } else {
        blob = new Blob([data.content], { type: 'text/plain' });
        filename = data.filename;
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success(`Downloaded ${format.toUpperCase()}`);
    } catch (err) {
      toast.error("Download failed");
    }
  };

  const reset = () => {
    setFile(null);
    setJobId(null);
    setStatus("idle");
    setProgress(0);
    setResults(null);
    setLiveTranscription([]);
    setLiveTopics([]);
    setCurrentTime(0);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentStepIndex = () => {
    const step = PROCESSING_STEPS.findIndex(s => s.startsWith(backendStatus));
    return step === -1 ? 0 : step;
  };

  return (
    <div className="container py-8 px-4 md:px-6 max-w-7xl mx-auto">
      <div className="flex flex-col space-y-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
              Podcast Topic Analyzer
            </h1>
            <p className="text-zinc-500 dark:text-zinc-400 mt-2 text-lg">
              Powered by Whisper & MLCommons People's Speech
            </p>
          </div>
          {status === "completed" && (
            <div className="flex gap-3">
              <Button variant="outline" size="sm" className="bg-white dark:bg-zinc-900 shadow-sm border-zinc-200 dark:border-zinc-800">
                <Download className="mr-2 h-4 w-4" /> Export Results
              </Button>
              <Button onClick={reset} size="sm" className="bg-blue-600 hover:bg-blue-700">
                New Analysis
              </Button>
            </div>
          )}
        </div>

        <AnimatePresence mode="wait">
          {(status === "idle" || status === "error") && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="grid grid-cols-1 lg:grid-cols-4 gap-8"
            >
              <Card className="lg:col-span-3 border-2 border-dashed bg-zinc-50/50 dark:bg-zinc-900/30 hover:bg-zinc-100/50 dark:hover:bg-zinc-900/50 transition-all duration-300 group">
                <CardContent className="p-0">
                  <div 
                    {...getRootProps()} 
                    className={`relative flex flex-col items-center justify-center p-16 rounded-xl cursor-pointer min-h-[400px] ${isDragActive ? 'bg-blue-50/50 dark:bg-blue-900/10 border-blue-400' : 'border-zinc-200 dark:border-zinc-800'}`}
                  >
                    <input {...getInputProps()} />
                    <div className="p-6 rounded-2xl bg-white dark:bg-zinc-800 shadow-xl border border-zinc-100 dark:border-zinc-700 mb-6 group-hover:scale-110 transition-transform duration-300">
                      <Upload className="h-12 w-12 text-blue-600" />
                    </div>
                    <div className="text-center space-y-4">
                      <h3 className="text-2xl font-bold text-zinc-800 dark:text-zinc-100">
                        {file ? file.name : "Drop your podcast audio here"}
                      </h3>
                      <p className="text-zinc-500 dark:text-zinc-400 max-w-sm mx-auto">
                        We'll transcribe, segment, and classify your audio using state-of-the-art ML models.
                      </p>
                    </div>
                    {file && status !== "uploading" && (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-10 flex items-center gap-4"
                      >
                        <Button 
                          onClick={(e) => { e.stopPropagation(); handleStartProcessing(); }} 
                          className="bg-blue-600 hover:bg-blue-700 h-14 px-10 text-lg font-bold shadow-lg shadow-blue-500/20"
                        >
                          Analyze Now
                        </Button>
                        <Button 
                          onClick={(e) => { e.stopPropagation(); setFile(null); }} 
                          variant="ghost" 
                          size="icon" 
                          className="h-14 w-14 rounded-xl hover:bg-red-50 hover:text-red-600 transition-colors"
                        >
                          <X className="h-6 w-6" />
                        </Button>
                      </motion.div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <div className="lg:col-span-1 space-y-6">
                <Card className="bg-zinc-900 text-white border-none overflow-hidden relative">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <Database className="h-24 w-24" />
                  </div>
                  <CardHeader>
                    <CardTitle className="text-xl">Try Demo Samples</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Explore the MLCommons People's Speech dataset.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 relative z-10">
                    {PEOPLES_SPEECH_SAMPLES.map((sample) => (
                      <button
                        key={sample.id}
                        onClick={() => handleTryDemo(sample)}
                        className="w-full flex items-center justify-between p-3 rounded-lg bg-zinc-800/50 hover:bg-zinc-800 transition-colors text-left group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded bg-blue-600/20 text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-all">
                            <Play className="h-3 w-3 fill-current" />
                          </div>
                          <div>
                            <p className="text-sm font-medium truncate max-w-[120px]">{sample.name}</p>
                            <p className="text-[10px] text-zinc-500">{sample.duration} • {sample.size}</p>
                          </div>
                        </div>
                        <ChevronRight className="h-4 w-4 text-zinc-600 group-hover:text-zinc-300" />
                      </button>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </motion.div>
          )}

          {(status === "uploading" || status === "processing") && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-8"
            >
              <div className="flex flex-col md:flex-row gap-8 items-start">
                <Card className="flex-1 border-zinc-200 dark:border-zinc-800 shadow-xl overflow-hidden min-h-[500px]">
                  <CardHeader className="bg-zinc-50 dark:bg-zinc-900 border-b dark:border-zinc-800 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Mic2 className="h-5 w-5 text-blue-600 animate-pulse" />
                        Live Transcription
                      </CardTitle>
                      <CardDescription>Streaming text from Whisper model...</CardDescription>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 text-xs font-bold flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
                        Processing: {formatTime(currentTime)}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    <ScrollArea className="h-[400px] p-6">
                      <div className="space-y-4">
                        {liveTranscription.length === 0 && (
                          <div className="flex flex-col items-center justify-center h-64 text-zinc-400 space-y-4">
                            <Loader2 className="h-8 w-8 animate-spin" />
                            <p>Initial chunks being processed...</p>
                          </div>
                        )}
                        {liveTranscription.map((seg, idx) => (
                          <motion.div 
                            key={idx}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex gap-4 group"
                          >
                            <span className="text-[10px] font-mono text-zinc-400 w-12 shrink-0 pt-1">{formatTime(seg.start)}</span>
                            <p className="text-zinc-700 dark:text-zinc-300 group-last:text-blue-600 dark:group-last:text-blue-400 group-last:font-medium transition-colors">
                              {seg.text}
                            </p>
                          </motion.div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                  <div className="p-4 bg-zinc-50 dark:bg-zinc-900 border-t dark:border-zinc-800">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold text-zinc-500">Overall Progress</span>
                      <span className="text-xs font-bold text-blue-600">{progress}%</span>
                    </div>
                    <Progress value={progress} className="h-2" />
                  </div>
                </Card>

                <div className="w-full md:w-80 space-y-6">
                  <Card className="border-zinc-200 dark:border-zinc-800 shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-sm">Detected Topics</CardTitle>
                      <CardDescription className="text-[10px]">Updating every 30s</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {liveTopics.length === 0 && (
                        <div className="text-center py-8 text-zinc-400">
                          <Tag className="h-8 w-8 mx-auto mb-2 opacity-20" />
                          <p className="text-xs">No topics identified yet</p>
                        </div>
                      )}
                      {liveTopics.map((topic, idx) => (
                        <motion.div
                          key={topic.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 flex items-center justify-between group"
                        >
                          <div className="flex items-center gap-3 overflow-hidden">
                            <div className="p-2 rounded bg-blue-100 text-blue-600">
                              <Tag className="h-3 w-3" />
                            </div>
                            <div className="overflow-hidden">
                              <p className="text-xs font-bold truncate">{topic.category}</p>
                              <p className="text-[10px] text-zinc-500">{formatTime(topic.startTime)}</p>
                            </div>
                          </div>
                          <div className="text-[10px] font-bold text-green-600">{Math.round(topic.confidence * 100)}%</div>
                        </motion.div>
                      ))}
                    </CardContent>
                  </Card>

                  <Card className="bg-zinc-900 text-white border-none overflow-hidden">
                    <CardContent className="p-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center animate-pulse">
                          <FileAudio className="h-6 w-6" />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Processing</p>
                          <p className="text-sm font-medium truncate w-40">{file?.name}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </motion.div>
          )}

          {status === "completed" && results && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-8"
            >
              {/* Interactive Timeline */}
              <Card className="border-none shadow-xl bg-white dark:bg-zinc-950 overflow-hidden">
                <CardHeader className="bg-zinc-50 dark:bg-zinc-900/50 border-b border-zinc-100 dark:border-zinc-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="h-5 w-5 text-blue-600" />
                        Topic Segmentation Timeline
                      </CardTitle>
                      <CardDescription>Visualize semantic shifts throughout the recording</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-8">
                  <div className="relative h-24 bg-zinc-100 dark:bg-zinc-900 rounded-2xl overflow-hidden flex shadow-inner">
                    {results.topics.map((topic, idx) => {
                      const width = ((topic.endTime - topic.startTime) / results.metadata.duration) * 100;
                      const categories: Record<string, string> = {
                        'Technology': 'bg-blue-500',
                        'Science': 'bg-purple-500',
                        'Politics': 'bg-red-500',
                        'Sports': 'bg-orange-500',
                        'Weather': 'bg-cyan-500',
                        'Business': 'bg-emerald-500'
                      };
                      const color = categories[topic.category] || 'bg-zinc-500';
                      return (
                        <motion.div
                          key={topic.id}
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: 1 }}
                          transition={{ delay: idx * 0.1 }}
                          style={{ width: `${width}%`, transformOrigin: 'left' }}
                          onClick={() => setActiveTopic(topic.id)}
                          className={`h-full border-r border-white/20 relative cursor-pointer group ${color} hover:brightness-110 transition-all`}
                        >
                          <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                          <div className="absolute bottom-2 left-2 right-2 truncate text-[10px] font-bold text-white uppercase tracking-tighter opacity-0 group-hover:opacity-100 transition-opacity">
                            {topic.name}: {topic.category}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                  <div className="mt-4 flex justify-between text-xs font-mono text-zinc-400">
                    <span>00:00</span>
                    <span>{formatTime(results.metadata.duration / 2)}</span>
                    <span>{formatTime(results.metadata.duration)}</span>
                  </div>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left: Table & Segments */}
                <div className="lg:col-span-8 space-y-6">
                  <Card className="border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden">
                    <Tabs defaultValue="segments" className="w-full">
                      <div className="px-6 pt-6 border-b dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30">
                        <TabsList className="bg-zinc-100 dark:bg-zinc-800 p-1 mb-0 border-b-0 rounded-b-none">
                          <TabsTrigger value="segments" className="flex items-center gap-2 px-6">
                            <TableIcon className="h-4 w-4" /> Topic Table
                          </TabsTrigger>
                          <TabsTrigger value="transcript" className="flex items-center gap-2 px-6">
                            <FileText className="h-4 w-4" /> Full Transcript
                          </TabsTrigger>
                        </TabsList>
                      </div>
                      
                      <TabsContent value="segments" className="m-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-sm">
                            <thead className="bg-zinc-50 dark:bg-zinc-900 border-b dark:border-zinc-800">
                              <tr>
                                <th className="px-6 py-4 font-bold text-zinc-500 uppercase tracking-wider text-[10px]">Topic</th>
                                <th className="px-6 py-4 font-bold text-zinc-500 uppercase tracking-wider text-[10px]">Start/End</th>
                                <th className="px-6 py-4 font-bold text-zinc-500 uppercase tracking-wider text-[10px]">Preview</th>
                                <th className="px-6 py-4 font-bold text-zinc-500 uppercase tracking-wider text-[10px]">Confidence</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y dark:divide-zinc-800">
                              {results.topics.map((topic) => (
                                <tr 
                                  key={topic.id} 
                                  className={`hover:bg-zinc-50 dark:hover:bg-zinc-900/50 transition-colors group ${activeTopic === topic.id ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}`}
                                >
                                  <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                      <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
                                        <Tag className="h-3 w-3" />
                                      </div>
                                      <div>
                                        <p className="font-bold">{topic.name}</p>
                                        <p className="text-[10px] text-zinc-400">{topic.category}</p>
                                      </div>
                                    </div>
                                  </td>
                                  <td className="px-6 py-4 font-mono text-xs text-zinc-500">
                                    {formatTime(topic.startTime)} - {formatTime(topic.endTime)}
                                  </td>
                                  <td className="px-6 py-4">
                                    <p className="line-clamp-1 text-zinc-600 dark:text-zinc-400 italic max-w-xs text-xs">
                                      "{topic.text}"
                                    </p>
                                  </td>
                                  <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                      <div className="flex-1 h-1 w-12 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-green-500" style={{ width: `${topic.confidence * 100}%` }} />
                                      </div>
                                      <span className="text-[10px] font-bold text-green-600">{Math.round(topic.confidence * 100)}%</span>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </TabsContent>

                      <TabsContent value="transcript" className="m-0">
                        <ScrollArea className="h-[400px] p-8">
                          <div className="space-y-8 max-w-3xl mx-auto">
                            {results.transcription.map((seg, idx) => (
                              <div key={idx} className="group flex gap-8">
                                <span className="text-xs font-mono text-zinc-400 pt-1 shrink-0">
                                  {formatTime(seg.start)}
                                </span>
                                <div className="space-y-2">
                                  <p className="text-zinc-700 dark:text-zinc-300 leading-relaxed text-lg group-hover:text-zinc-900 dark:group-hover:text-white transition-colors">
                                    {seg.text}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </ScrollArea>
                      </TabsContent>
                    </Tabs>
                  </Card>
                </div>

                {/* Right: Insights & Actions */}
                <div className="lg:col-span-4 space-y-6">
                  <Card className="bg-blue-600 text-white border-none shadow-xl relative overflow-hidden">
                    <div className="absolute -right-4 -bottom-4 opacity-10">
                      <Volume2 className="h-32 w-32" />
                    </div>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Download className="h-4 w-4" /> Export Assets
                      </CardTitle>
                    </CardHeader>
                      <CardContent className="space-y-4 relative z-10">
                        <div className="grid grid-cols-2 gap-2">
                          <Button 
                            variant="outline" 
                            onClick={() => handleDownload('json')}
                            className="bg-blue-700/50 border-blue-500 text-white hover:bg-blue-700 h-10"
                          >
                            JSON
                          </Button>
                          <Button 
                            variant="outline" 
                            onClick={() => handleDownload('srt')}
                            className="bg-blue-700/50 border-blue-500 text-white hover:bg-blue-700 h-10"
                          >
                            SRT Subtitles
                          </Button>
                          <Button 
                            variant="outline" 
                            onClick={() => handleDownload('csv')}
                            className="bg-blue-700/50 border-blue-500 text-white hover:bg-blue-700 h-10"
                          >
                            CSV Data
                          </Button>
                          <Button 
                            variant="outline" 
                            onClick={() => handleDownload('json')}
                            className="bg-blue-700/50 border-blue-500 text-white hover:bg-blue-700 h-10"
                          >
                            Chapters
                          </Button>
                        </div>
                      </CardContent>

                  </Card>

                  <Card className="border-zinc-200 dark:border-zinc-800">
                    <CardHeader>
                      <CardTitle className="text-lg">Analysis Metrics</CardTitle>
                      <CardDescription>ML performance on this file</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-zinc-500">Transcription Accuracy</span>
                          <span className="font-bold text-green-500">{results.metadata.accuracy * 100}%</span>
                        </div>
                        <Progress value={results.metadata.accuracy * 100} className="h-1 bg-zinc-100 dark:bg-zinc-800 [&>div]:bg-green-500" />
                      </div>
                      <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800">
                        <p className="text-[10px] font-black uppercase text-zinc-400 mb-2">Duration</p>
                        <p className="text-2xl font-bold text-zinc-800 dark:text-zinc-100">{formatTime(results.metadata.duration)}</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
