import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';

const UPLOAD_DIR = '/tmp/uploads';
const ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm'];
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

// In-memory job storage (in production, use Redis or DB)
const jobs: Map<string, any> = new Map();

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;

    if (!file) {
      console.error('Upload error: No file provided');
      return NextResponse.json({ detail: 'No file provided' }, { status: 400 });
    }

    console.log(`Upload received: ${file.name}, size: ${file.size}, type: ${file.type}`);

    // Validate file extension
    const ext = path.extname(file.name).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      console.error(`Upload error: Unsupported format ${ext}`);
      return NextResponse.json({ 
        detail: `Unsupported file format: ${ext}. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}` 
      }, { status: 400 });
    }

    // Validate file size
    if (file.size === 0) {
      console.error('Upload error: Empty file');
      return NextResponse.json({ detail: 'File is empty (0 bytes)' }, { status: 400 });
    }

    if (file.size > MAX_FILE_SIZE) {
      console.error(`Upload error: File too large (${file.size} bytes)`);
      return NextResponse.json({ 
        detail: `File too large. Maximum size: ${MAX_FILE_SIZE / (1024 * 1024)}MB` 
      }, { status: 400 });
    }

    // Create upload directory if it doesn't exist
    if (!existsSync(UPLOAD_DIR)) {
      await mkdir(UPLOAD_DIR, { recursive: true });
    }

    // Generate job ID and safe filename
    const jobId = randomUUID();
    const safeFilename = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
    const filePath = path.join(UPLOAD_DIR, `${jobId}_${safeFilename}`);

    // Save file
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    await writeFile(filePath, buffer);

    console.log(`File saved: ${filePath} (${buffer.length} bytes)`);

    // Store job info
    jobs.set(jobId, {
      id: jobId,
      filename: file.name,
      filePath,
      status: 'Queued',
      progress: 0,
      result: null,
      createdAt: new Date().toISOString()
    });

    // Export jobs for other routes
    (global as any).__jobs = jobs;

    return NextResponse.json({ 
      job_id: jobId, 
      filename: file.name, 
      size: buffer.length 
    });

  } catch (error: any) {
    console.error('Upload error:', error);
    return NextResponse.json({ 
      detail: `Upload failed: ${error.message}` 
    }, { status: 500 });
  }
}
