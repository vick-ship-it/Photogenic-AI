const form = document.getElementById('studio-form');
const submitButton = document.getElementById('submit');
const resultSection = document.getElementById('result');
const imageEl = document.getElementById('image');
const promptEl = document.getElementById('prompt');
const errorEl = document.getElementById('error');

async function generate(e) {
  e.preventDefault();
  resultSection.hidden = false;
  errorEl.hidden = true;
  errorEl.textContent = '';
  imageEl.removeAttribute('src');
  promptEl.textContent = '';

  const formData = new FormData(form);

  submitButton.disabled = true;
  submitButton.textContent = 'Generating…';

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data?.detail || 'Generation failed');
    }

    if (data.image_url) {
      imageEl.src = data.image_url;
    }

    if (data.prompt) {
      promptEl.textContent = `Prompt: ${data.prompt}`;
    }
  } catch (err) {
    console.error(err);
    errorEl.textContent = err.message || String(err);
    errorEl.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = 'Generate';
  }
}

form.addEventListener('submit', generate);
