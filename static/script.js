const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const emptyState = document.getElementById('emptyState');
const previewImg = document.getElementById('previewImg');
const developBtn = document.getElementById('developBtn');
const captionText = document.getElementById('captionText');
const trayMeta = document.getElementById('trayMeta');
const frameNumber = document.getElementById('frameNumber');
const methodToggle = document.getElementById('methodToggle');

let selectedFile = null;
let currentMethod = 'beam';
let frameCount = Math.floor(Math.random() * 40) + 1;

frameNumber.textContent = `FRAME No. ${String(frameCount).padStart(3, '0')}`;

// --- Method toggle ---
methodToggle.addEventListener('click', (e) => {
  const btn = e.target.closest('.toggle-btn');
  if (!btn) return;
  document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentMethod = btn.dataset.method;
});

// --- Upload handling ---
dropzone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

['dragover', 'dragenter'].forEach(evt => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.style.borderColor = 'var(--accent)';
  });
});
['dragleave', 'drop'].forEach(evt => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.style.borderColor = 'var(--border)';
  });
});
dropzone.addEventListener('drop', (e) => {
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  if (!file.type.startsWith('image/')) return;
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewImg.classList.remove('hidden');
    emptyState.classList.add('hidden');
  };
  reader.readAsDataURL(file);

  developBtn.disabled = false;
  captionText.textContent = '\u00A0';
  captionText.classList.remove('visible');
  trayMeta.textContent = '';
}

// --- Generate caption ---
developBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  developBtn.disabled = true;
  developBtn.classList.add('loading');
  developBtn.textContent = 'Developing...';
  captionText.classList.remove('visible');

  const formData = new FormData();
  formData.append('image', selectedFile);
  formData.append('method', currentMethod);

  try {
      const res = await fetch('/generate', { method: 'POST', body: formData });
      const data = await res.json();

      if (data.error) {
        captionText.textContent = `Error: ${data.error}`;
        captionText.classList.add('visible');
      } else {
        revealWordByWord(data.caption);
        trayMeta.textContent = `DECODED VIA ${data.method.toUpperCase()} SEARCH`;
        frameCount += 1;
        frameNumber.textContent = `FRAME No. ${String(frameCount).padStart(3, '0')}`;
      }
    } catch (err) {
      captionText.textContent = 'Error: could not reach the model.';
      captionText.classList.add('visible');
  }
  
  function revealWordByWord(caption) {
    const words = caption.split(' ');
    captionText.innerHTML = '';
    captionText.classList.add('visible');

    captionText.appendChild(document.createTextNode('"'));

    words.forEach((word) => {
      const span = document.createElement('span');
      span.className = 'word';
      span.textContent = word;
      captionText.appendChild(span);
      captionText.appendChild(document.createTextNode(' '));  // real space, outside the span
    });

    captionText.appendChild(document.createTextNode('"'));

    const allSpans = captionText.querySelectorAll('.word');
    allSpans.forEach((span, i) => {
      setTimeout(() => {
        span.classList.add('word-visible');
      }, i * 90);
    });
  }

  developBtn.disabled = false;
  developBtn.classList.remove('loading');
  developBtn.textContent = 'Develop Caption';
});
