import { useRef } from "react";
import { X, Download } from "lucide-react";
import { toPng } from "html-to-image";
import ChartRenderer from "./ChartRenderer";

function ChartModal({ proposal, onClose }) {
  const chartRef = useRef(null);

  const handleDownload = async () => {
    if (!chartRef.current) return;
    try {
      const dataUrl = await toPng(chartRef.current, { backgroundColor: "#ffffff", pixelRatio: 2 });
      const link = document.createElement("a");
      link.download = `${(proposal.title || "chart").replace(/\s+/g, "_")}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error("Chart download failed:", err);
    }
  };

  return (
    <div className="chartModalOverlay" onClick={onClose}>
      <div className="chartModalContent" onClick={(e) => e.stopPropagation()}>
        <div className="chartModalHeader">
          <h3>{proposal.title}</h3>
          <div className="chartModalActions">
            <button className="chartModalActionBtn" onClick={handleDownload}>
              <Download size={16} /> Download
            </button>
            <button className="chartModalActionBtn" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </div>
        <div className="chartModalBody" ref={chartRef}>
          <ChartRenderer proposal={proposal} large />
        </div>
      </div>
    </div>
  );
}

export default ChartModal;

