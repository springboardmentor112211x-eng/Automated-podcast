(function(){
  const API = (path) => `${window.API_BASE.replace(/\/+$/, '')}${path}`;
  const fileInput = document.getElementById('fileInput');
  const uploadBtn = document.getElementById('uploadBtn');
  const statusEl = document.getElementById('status');
  const transEl = document.getElementById('transcription');
  const sumEl = document.getElementById('summary');

  const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200 MB per backend (configurable server-side)

  function setStatus(msg, type = 'info'){
    statusEl.textContent = msg;
    statusEl.className = `status ${type}`;
  }

  function renderProcessing(){
    const msg = '<p class="muted">Processing audio... This may take a while for long podcasts. Keep this tab open.</p>';
    if (transEl) transEl.innerHTML = msg;
    if (sumEl) sumEl.innerHTML = msg;
  }

  function renderResult(data){
    if (!data || data.status === 'processing'){
      renderProcessing();
      return;
    }

    const topics = Array.isArray(data.topics) ? data.topics : [];
    const summaries = Array.isArray(data.summaries) ? data.summaries : [];
    const labels = Array.isArray(data.labels) ? data.labels : [];

    const summaryMap = new Map(summaries.map(s => [String(s.topic_id), s.topic_summary]));
    const labelMap = new Map(labels.map(l => [String(l.topic_id), l.topic_label]));

    const transcriptionSections = topics.map((t, idx) => {
      const tid = String(t.topic_id);
      const transcript = t.transcript || '';
      if (!transcript) return '';
      return `
        <div class="topic">
          <div class="topic-header">
            <div class="topic-title">Topic ${tid || idx+1}</div>
          </div>
          <div class="topic-body">
            <div class="block"><div class="block-title">Transcript</div><div class="block-content">${escapeHtml(transcript)}</div></div>
          </div>
        </div>
      `;
    }).join('');

    // Build a single combined summary (not topic-wise), using summaries list to avoid duplicates
    const combinedSummary = (() => {
      const seen = new Set();
      const items = [];
      const ordered = summaries
        .slice()
        .sort((a, b) => (parseInt(a.topic_id ?? 0) - parseInt(b.topic_id ?? 0)));
      for (const s of ordered) {
        const txt = (s.topic_summary || '').trim();
        if (!txt) continue;
        const key = txt.toLowerCase();
        if (seen.has(key)) continue; // de-duplicate identical summaries
        seen.add(key);
        items.push(txt);
      }
      return items.join('\n\n');
    })();

    const finalSummary = (data.global_summary || '').trim() || combinedSummary;

    if (transEl) transEl.innerHTML = transcriptionSections || '<p class="muted">No transcription available.</p>';
    if (sumEl) {
      sumEl.innerHTML = finalSummary
        ? `<div class="block"><div class="block-title">Summary</div><div class="block-content">${escapeHtml(finalSummary)}</div></div>`
        : '<p class="muted">No summary available.</p>';
    }
  }

  function escapeHtml(str){
    return String(str)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  async function upload(file){
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(API('/upload'), { method: 'POST', body: fd });
    if (!res.ok){
      const txt = await res.text();
      throw new Error(txt || `Upload failed (${res.status})`);
    }
    return res.json();
  }

  async function startProcess(audioId){
    const res = await fetch(API(`/process/${audioId}`), { method: 'POST' });
    if (!res.ok){
      const txt = await res.text();
      throw new Error(txt || `Process start failed (${res.status})`);
    }
    return res.json();
  }

  async function getResult(audioId){
    const res = await fetch(API(`/result/${audioId}`));
    if (!res.ok){
      const txt = await res.text();
      throw new Error(txt || `Get result failed (${res.status})`);
    }
    return res.json();
  }

  function sleep(ms){ return new Promise(r => setTimeout(r, ms)); }

  async function pollResult(audioId){
    renderProcessing();
    for(;;){
      const data = await getResult(audioId);
      if (data && data.status !== 'processing'){
        return data;
      }
      await sleep(2000);
    }
  }

  uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file){
      setStatus('Please choose an audio file first.', 'warn');
      return;
    }
    if (file.size > MAX_FILE_SIZE){
      setStatus('File is too large. Current backend limit is 200 MB.', 'error');
      return;
    }

    setStatus('Uploading file...', 'info');
    uploadBtn.disabled = true;

    try{
      const { audio_id } = await upload(file);
      setStatus('Starting processing...', 'info');
      await startProcess(audio_id);
      setStatus('Processing... This may take several minutes for long audio.', 'info');
      const data = await pollResult(audio_id);
      setStatus('Done.', 'success');
      renderResult(data);
      try { alert('Processing complete! Your transcription and summary are ready.'); } catch(_) {}
    }catch(err){
      console.error(err);
      setStatus(err?.message || 'Something went wrong', 'error');
    }finally{
      uploadBtn.disabled = false;
    }
  });
})();
