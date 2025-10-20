const API_BASE = 'http://127.0.0.1:8000';

export async function fetchFiles() {
  const res = await fetch(`${API_BASE}/files`);
  if (!res.ok) throw new Error('Failed to fetch file list');
  const data = await res.json();
  return data.files || [];
}

export async function deleteFile(fileId) {
    const url = `${API_BASE}/delete/${encodeURIComponent(fileId)}`;
    const res = await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    });

    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to delete file: ${errorText}`);
    }

    const data = await res.json();
    return data;
}

export async function deleteAllFiles() {
    const url = `${API_BASE}/delete/all`;
    const res = await fetch(url, { method: 'DELETE' });
    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to delete all files: ${errorText}`);
    }
    const data = await res.json();
    return data;
}

export async function uploadFiles(files) {
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }

    const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        body: formData
    });

    if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Upload failed: ${errText}`);
    }

    const data = await res.json();
    return data;
}

export async function sendQuery(queryText) {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: queryText })
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Query failed: ${errorText}`);
  }

  const data = await res.json();
  return data; // expected: { answer: "...", citations: [...] }
}