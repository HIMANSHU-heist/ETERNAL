const API_URL = "";

async function handle(response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed: ${response.status} ${text}`);
  }
  return response.json();
}

export const uploadDataset = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${API_URL}/api/v1/upload`, { method: "POST", body: formData }).then(handle);
};

export const fetchDatasetList = () =>
  fetch(`${API_URL}/api/v1/datasets`).then(handle).then((d) => d.datasets || []);

export const runAnalysis = (datasetId, goal) =>
  fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, goal }),
  }).then(handle);

export const fetchChatHistory = (fileId) =>
  fetch(`${API_URL}/chat/history?file_id=${encodeURIComponent(fileId)}`)
    .then(handle)
    .then((d) => d.messages || []);

export const sendChatMessage = (fileId, message) =>
  fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, message }),
  }).then(handle);

