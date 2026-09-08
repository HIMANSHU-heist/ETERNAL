function getDeviceId() {
  let id = localStorage.getItem("device_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("device_id", id);
  }
  return id;
}

const DEVICE_ID = getDeviceId();
const API_URL = "https://eternal-bme9btamafeaa9ew.uaenorth-01.azurewebsites.net";

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
  return fetch(`${API_URL}/api/v1/upload`, {
    method: "POST",
    headers: { "X-Device-Id": DEVICE_ID },
    body: formData,
  }).then(handle);
};

export const fetchDatasetList = () =>
  fetch(`${API_URL}/api/v1/datasets`, { headers: { "X-Device-Id": DEVICE_ID } })
    .then(handle)
    .then((d) => d.datasets || []);

export const fetchDatasetSchema = (datasetId) =>
  fetch(`${API_URL}/api/v1/dataset/${datasetId}/schema`).then(handle);

export const fetchDatasetCsv = (datasetId, page = 1, pageSize = 50) =>
  fetch(`${API_URL}/api/v1/dataset/${datasetId}/csv?page=${page}&page_size=${pageSize}`).then(handle);

export const runAnalysis = (datasetId, goal) =>
  fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, goal }),
  }).then(handle);

// Returns null (not an error) when the dataset has never been analyzed yet.
export const fetchCachedAnalysis = async (datasetId) => {
  const res = await fetch(`${API_URL}/analyze/${datasetId}`);
  if (res.status === 404) return null;
  return handle(res);
};

export const getFeaturePlan = (datasetId) =>
  fetch(`${API_URL}/api/v1/feature-plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId }),
  }).then(handle);

export const applyFeaturePlan = (datasetId, steps) =>
  fetch(`${API_URL}/api/v1/feature-apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, steps }),
  }).then(handle);

export const fetchChatHistory = (fileId) =>
  fetch(`${API_URL}/chat/history?file_id=${encodeURIComponent(fileId)}`)
    .then(handle)
    .then((d) => d.messages || []);

export const sendChatMessage = (fileId, message, intent = null) =>
  fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, message, intent }),
  }).then(handle);