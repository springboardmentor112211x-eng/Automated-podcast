import { NextRequest, NextResponse } from 'next/server';

function getJobs(): Map<string, any> {
  if (!(global as any).__jobs) {
    (global as any).__jobs = new Map();
  }
  return (global as any).__jobs;
}

function generateSrt(transcription: any[]): string {
  return transcription.map((seg, idx) => {
    const formatSrtTime = (seconds: number) => {
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      const s = Math.floor(seconds % 60);
      const ms = Math.floor((seconds % 1) * 1000);
      return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
    };
    return `${idx + 1}\n${formatSrtTime(seg.start)} --> ${formatSrtTime(seg.end)}\n${seg.text}\n`;
  }).join('\n');
}

function generateCsv(transcription: any[]): string {
  const header = 'start,end,text\n';
  const rows = transcription.map(seg => 
    `${seg.start},${seg.end},"${seg.text.replace(/"/g, '""')}"`
  ).join('\n');
  return header + rows;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string; format: string }> }
) {
  const { jobId, format } = await params;
  const jobs = getJobs();
  const job = jobs.get(jobId);

  if (!job || job.status !== 'Complete') {
    return NextResponse.json({ detail: 'Results not ready' }, { status: 404 });
  }

  const result = job.result;

  if (format === 'json') {
    return NextResponse.json(result);
  } else if (format === 'srt') {
    return NextResponse.json({ 
      content: generateSrt(result.transcription), 
      filename: 'transcript.srt' 
    });
  } else if (format === 'csv') {
    return NextResponse.json({ 
      content: generateCsv(result.transcription), 
      filename: 'transcript.csv' 
    });
  } else {
    return NextResponse.json({ detail: 'Invalid format' }, { status: 400 });
  }
}
