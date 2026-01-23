document.getElementById("analyzeBtn").addEventListener("click", upload);

async function upload() {
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  const button = document.getElementById("analyzeBtn");

  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) {
    alert("Please select an audio file");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  status.innerText = "⏳ Analyzing podcast... Please wait";
  results.innerHTML = "";
  button.disabled = true;

  try {
    const response = await fetch("http://127.0.0.1:8000/api/transcribe/", {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error("Server error");

    const data = await response.json();
    status.innerText = "✅ Analysis complete";

    data.topics.forEach(t => {
      results.innerHTML += `
        <div class="topic">
          <h3>📌 Topic ${t.topic_id}</h3>
          <b>⏱ ${t.start_time}s – ${t.end_time}s</b><br>
          <b>Keywords:</b> ${t.keywords}<br><br>
          <p>${t.text}</p>
        </div>
      `;
    });

    createDownloads(data);

  } catch (err) {
    console.error(err);
    status.innerText = "❌ Failed to analyze podcast";
  }

  button.disabled = false;
}

function createDownloads(data) {
  const results = document.getElementById("results");

  const jsonBlob = new Blob([JSON.stringify(data, null, 2)], {type: "application/json"});
  const jsonUrl = URL.createObjectURL(jsonBlob);

  let textContent = "";
  data.topics.forEach(t => {
    textContent += `Topic ${t.topic_id}\n`;
    textContent += `Time: ${t.start_time}s - ${t.end_time}s\n`;
    textContent += `Keywords: ${t.keywords}\n`;
    textContent += `${t.text}\n\n`;
  });
  const textBlob = new Blob([textContent], { type: "text/plain" });
  const textUrl = URL.createObjectURL(textBlob);

  results.innerHTML += `
    <div class="download">
      <h3>⬇ Download Results</h3>
      <a href="${jsonUrl}" download="transcription.json">📄 Download JSON</a><br>
      <a href="${textUrl}" download="transcription.txt">📝 Download TXT</a>
    </div>
  `;
}
