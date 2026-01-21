import { NextRequest, NextResponse } from 'next/server';

// Demo transcription data
const DEMO_SENTENCES = [
  "Welcome to the Podcast Topic Analyzer demo.",
  "This is a real-time streaming transcription powered by AI.",
  "We are currently analyzing the audio for semantic shifts.",
  "As the speaker continues, the topic segmentation engine identifies boundaries.",
  "In this segment, the discussion is shifting towards technology and its impact.",
  "Artificial Intelligence is revolutionizing how we process large datasets.",
  "Next, we might see a shift towards business and market trends.",
  "Companies are investing heavily in LLMs and generative models.",
  "This concludes our short demonstration of real-time processing.",
  "Thank you for watching the live transcription feed."
];

const DEMO_TOPICS = [
  { category: 'Introduction', name: 'Welcome' },
  { category: 'Technology', name: 'AI Overview' },
  { category: 'Technology', name: 'Data Analysis' },
  { category: 'Business', name: 'Market Trends' },
  { category: 'Technology', name: 'LLM Investment' },
  { category: 'Conclusion', name: 'Summary' }
];

// Get jobs storage
function getJobs(): Map<string, any> {
  if (!(global as any).__jobs) {
    (global as any).__jobs = new Map();
  }
  return (global as any).__jobs;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;
  const jobs = getJobs();
  const job = jobs.get(jobId);

  if (!job) {
    return NextResponse.json({ error: 'Job not found' }, { status: 404 });
  }

  // For WebSocket upgrade - Next.js doesn't natively support WebSockets in API routes
  // We'll use Server-Sent Events (SSE) instead which works better with Next.js
  const encoder = new TextEncoder();
  
  const stream = new ReadableStream({
    async start(controller) {
      const totalDuration = 120; // 2 minutes
      const chunkDuration = 15;
      let currentTime = 0;
      let topicIndex = 0;
      let sentenceIndex = 0;

      const sendUpdate = (data: any) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
      };

      // Simulate processing
      for (let i = 0; currentTime < totalDuration; i++) {
        await new Promise(resolve => setTimeout(resolve, 1500)); // 1.5 second delay

        const segments = [];
        const topics = [];
        
        // Add 2 sentences per chunk
        for (let j = 0; j < 2 && sentenceIndex < DEMO_SENTENCES.length; j++) {
          const segStart = currentTime + (j * chunkDuration / 2);
          segments.push({
            start: segStart,
            end: segStart + chunkDuration / 2,
            text: DEMO_SENTENCES[sentenceIndex % DEMO_SENTENCES.length]
          });
          sentenceIndex++;
        }

        // Add topic every 2 chunks
        if (i % 2 === 0 && topicIndex < DEMO_TOPICS.length) {
          const topic = DEMO_TOPICS[topicIndex];
          topics.push({
            id: topicIndex + 1,
            name: topic.name,
            category: topic.category,
            startTime: currentTime,
            endTime: currentTime + chunkDuration * 2,
            text: DEMO_SENTENCES[sentenceIndex % DEMO_SENTENCES.length],
            confidence: 0.85 + Math.random() * 0.14
          });
          topicIndex++;
        }

        currentTime += chunkDuration;
        const progress = Math.min(100, Math.round((currentTime / totalDuration) * 100));

        sendUpdate({
          type: 'update',
          new_segments: segments,
          new_topics: topics,
          progress,
          current_time: currentTime
        });

        // Update job status
        job.progress = progress;
        job.status = 'Processing';
      }

      // Send final result
      const finalResult = {
        transcription: DEMO_SENTENCES.map((text, idx) => ({
          start: idx * 12,
          end: (idx + 1) * 12,
          text
        })),
        topics: DEMO_TOPICS.map((topic, idx) => ({
          id: idx + 1,
          name: topic.name,
          category: topic.category,
          startTime: idx * 20,
          endTime: (idx + 1) * 20,
          text: DEMO_SENTENCES[idx % DEMO_SENTENCES.length],
          confidence: 0.85 + Math.random() * 0.14
        })),
        full_text: DEMO_SENTENCES.join(' '),
        metadata: {
          accuracy: 0.94,
          duration: totalDuration
        }
      };

      job.status = 'Complete';
      job.result = finalResult;

      sendUpdate({
        type: 'final',
        result: finalResult
      });

      controller.close();
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
