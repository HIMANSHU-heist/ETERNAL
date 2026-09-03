import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FileSpreadsheet, Database, BarChart3, AlertTriangle, CheckCircle2,
  Sparkles, TrendingUp, Award, Loader2, MessageSquare,
} from "lucide-react";
import { runAnalysis, fetchDatasetList } from "../api";
import { ChartsSection } from "../components/ChartRenderer";
import ChartModal from "../components/ChartModal";

function formatMessage(text) {
  if (!text) return null;
  const lines = text.split("\n");
  const elements = [];
  let listBuffer = [];
  const flushList = (key) => {
    if (listBuffer.length) {
      elements.push(
        <ul key={`ul-${key}`}>
          {listBuffer.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
      );
      listBuffer = [];
    }
  };
  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      listBuffer.push(trimmed.slice(2));
      return;
    }
    flushList(idx);
    if (trimmed) elements.push(<p key={idx}>{trimmed}</p>);
  });
  flushList("end");
  return elements;
}

function OverviewScreen() {
  const { datasetId } = useParams();
  const navigate = useNavigate();

  const [schema, setSchema] = useState(null);
  const [fileName, setFileName] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [expandedChart, setExpandedChart] = useState(null);

  useEffect(() => {
    fetchDatasetList().then((list) => {
      const found = list.find((d) => d.file_id === datasetId);
      if (found) {
        setFileName(found.filename);
        setSchema({ num_rows: found.num_rows, num_columns: found.num_columns, columns: found.columns || [] });
      }
    });
  }, [datasetId]);

  const buildGoal = () => {
    const columns = schema?.columns?.map((c) => c.name) || [];
    const likelyTarget = columns[columns.length - 1];
    return likelyTarget
      ? `Analyze this dataset and identify the main factors that influence '${likelyTarget}'. Highlight the strongest relationships and any data quality issues.`
      : "Analyze this dataset, identify the main patterns and relationships between variables, and flag any data quality issues.";
  };

  const handleAnalyze = async () => {
    setError("");
    setAnalyzing(true);
    try {
      const data = await runAnalysis(datasetId, buildGoal());
      setAnalysis(data);
    } catch (err) {
      setError(err.message || "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  const strongest = (() => {
    const results = analysis?.analysis_results || [];
    const correlationStep = results.find((x) => x.step?.type === "correlation");
    const matrix = correlationStep?.result;
    if (!matrix) return null;
    let best = null;
    const columns = Object.keys(matrix);
    for (const r of columns) {
      for (const c of columns) {
        if (r === c) continue;
        const val = Number(matrix[r]?.[c] ?? 0);
        if (!best || Math.abs(val) > Math.abs(best.value)) best = { pair: `${r} ↔ ${c}`, value: val };
      }
    }
    return best;
  })();

  const missingResult = analysis?.analysis_results?.find((x) => x.step?.type === "missing_report")?.result;

  return (
    <main className="container">
      <div className="datasetHeader">
        <div className="fileInfo">
          <div className={`fileIcon ${analysis ? "success" : ""}`}>
            {analysis ? <CheckCircle2 size={25} /> : <FileSpreadsheet size={25} />}
          </div>
          <div>
            <h2>{fileName || "Dataset"}</h2>
            <p>{analysis ? "AI analysis completed successfully" : "Dataset ready for AI analysis"}</p>
          </div>
        </div>
      </div>

      {!analysis && schema && (
        <>
          <div className="statsGrid">
            <StatCard icon={<Database />} label="Rows" value={schema.num_rows} />
            <StatCard icon={<BarChart3 />} label="Columns" value={schema.num_columns} />
            <StatCard
              icon={<AlertTriangle />}
              label="Missing Values"
              value={schema.columns?.reduce((sum, c) => sum + (c.num_missing || 0), 0) || 0}
            />
            <StatCard icon={<CheckCircle2 />} label="Dataset Status" value="Ready" green />
          </div>

          <button className="analyzeButton" onClick={handleAnalyze} disabled={analyzing}>
            {analyzing ? (
              <><Loader2 className="spin" size={19} /> Analyzing dataset...</>
            ) : (
              <><Sparkles size={19} /> Analyze Dataset</>
            )}
          </button>
        </>
      )}

      {error && (
        <div className="error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      {analysis && (
        <>
          <div className="insightGrid">
            <InsightCard
              icon={<TrendingUp />}
              title="Strongest relationship"
              value={strongest?.pair || "N/A"}
              detail={strongest ? `Pearson correlation: ${Number(strongest.value).toFixed(3)}` : "No correlation data"}
            />
            <InsightCard
              icon={<Award />}
              title="Data quality"
              value={
                Object.values(missingResult || {}).reduce((a, b) => a + Number(b || 0), 0) > 0
                  ? "Needs attention"
                  : "Clean dataset"
              }
              detail={
                Object.values(missingResult || {}).reduce((a, b) => a + Number(b || 0), 0) > 0
                  ? "Some values are missing"
                  : "No missing values detected"
              }
            />
          </div>

          <ChartsSection analysisResults={analysis?.analysis_results} onExpandChart={setExpandedChart} />

          <div className="reportCard">
            <div className="sectionTitle">
              <div>
                <h3>Analysis report</h3>
                <p>Generated from the actual dataset analysis.</p>
              </div>
            </div>
            <div className="report">
              {formatMessage(analysis.report?.replaceAll("###", "").replaceAll("##", "").replaceAll("---", ""))}
            </div>
          </div>
        </>
      )}

      <button className="openChatFab" onClick={() => navigate(`/dataset/${datasetId}/chat`)}>
        <MessageSquare size={18} />
        Open chat
      </button>

      {expandedChart && <ChartModal proposal={expandedChart} onClose={() => setExpandedChart(null)} />}
    </main>
  );
}

function StatCard({ icon, label, value, green }) {
  return (
    <div className="statCard">
      <div className="statIcon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong className={green ? "greenText" : ""}>{value}</strong>
      </div>
    </div>
  );
}

function InsightCard({ icon, title, value, detail }) {
  return (
    <div className="insightCard">
      <div className="insightTop">
        <div className="insightIcon">{icon}</div>
        <span>{title}</span>
      </div>
      <h3>{value}</h3>
      <p>{detail}</p>
    </div>
  );
}

export default OverviewScreen;

