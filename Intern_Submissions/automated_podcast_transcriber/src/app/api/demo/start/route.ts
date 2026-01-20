import { NextRequest, NextResponse } from 'next/server';
import { randomUUID } from 'crypto';

function getJobs(): Map<string, any> {
  if (!(global as any).__jobs) {
    (global as any).__jobs = new Map();
  }
  return (global as any).__jobs;
}

export async function POST(request: NextRequest) {
  try {
    const jobId = randomUUID();
    const jobs = getJobs();

    console.log(`Demo started: ${jobId}`);

    jobs.set(jobId, {
      id: jobId,
      filename: 'demo_sample.mp3',
      filePath: null,
      status: 'Queued',
      progress: 0,
      result: null,
      isDemo: true,
      createdAt: new Date().toISOString()
    });

    return NextResponse.json({ 
      job_id: jobId, 
      filename: 'demo_sample.mp3',
      is_demo: true 
    });

  } catch (error: any) {
    console.error('Demo start error:', error);
    return NextResponse.json({ 
      detail: `Demo failed to start: ${error.message}` 
    }, { status: 500 });
  }
}
