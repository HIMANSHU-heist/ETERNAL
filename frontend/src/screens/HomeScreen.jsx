import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Sparkles, AlertTriangle, Loader2 } from "lucide-react";
import { uploadDataset } from "../api";

function HomeScreen() {
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async (selectedFile) => {
    if (!selectedFile) return;

    const allowed = [".csv", ".xlsx", ".xls"];
    const ext = "." + selectedFile.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setError("Please upload a CSV, XLSX or XLS file.");
      return;
    }

    setError("");
    setUploading(true);
    try {
      const data = await uploadDataset(selectedFile);
      navigate(`/dataset/${data.dataset_id}`);
    } catch (err) {
      setError(err.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <main className="container">
      <section className="hero">
        <div className="eyebrow">
          <Sparkles size={15} />
          Intelligent Data Analysis
        </div>
        <h1>
          Turn your data into
          <span> clear insights.</span>
        </h1>
        <p>Upload your dataset and let Analyzer AI discover patterns, relationships and actionable insights automatically.</p>
      </section>

      <section
        className={`uploadCard ${uploading ? "uploading" : ""}`}
        onDrop={(e) => {
          e.preventDefault();
          handleUpload(e.dataTransfer.files?.[0]);
        }}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => handleUpload(e.target.files?.[0])}
          hidden
        />
        <div className="uploadIcon">
          {uploading ? <Loader2 className="spin" size={32} /> : <Upload size={32} />}
        </div>
        <h2>{uploading ? "Uploading dataset..." : "Drop your dataset here"}</h2>
        <p>or <b>browse files</b></p>
        <small>CSV, XLSX or XLS • Max recommended size 50MB</small>
      </section>

      {error && (
        <div className="error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}
    </main>
  );
}

export default HomeScreen;

