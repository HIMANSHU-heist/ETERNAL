import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  X,
  Loader2,
  Wand2,
  AlertTriangle,
} from "lucide-react";
import { getFeaturePlan, applyFeaturePlan } from "../api";

function stepLabel(step) {
  switch (step.type) {
    case "fillna":
      return `Fill missing values in "${step.column}" using ${step.strategy}`;
    case "drop_column":
      return `Drop column "${step.column}"`;
    case "encode_categorical":
      return `Encode "${step.column}" (${step.method})`;
    case "create_ratio":
      return `Create "${step.new_column}" = ${step.numerator} / ${step.denominator}`;
    case "bin_numeric":
      return `Bin "${step.column}" into ${step.bins} groups as "${step.new_column}"`;
    case "log_transform":
      return `Log-transform "${step.column}"`;
    default:
      return step.description || step.type;
  }
}

function FeatureEngineeringScreen() {
  const { datasetId } = useParams();
  const navigate = useNavigate();

  const [steps, setSteps] = useState([]);
  const [decisions, setDecisions] = useState({}); // step.id -> "approved" | "rejected"
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getFeaturePlan(datasetId)
      .then((res) => {
        const proposed = res.proposed_steps || [];
        setSteps(proposed);
        const initial = {};
        proposed.forEach((s) => (initial[s.id] = "approved"));
        setDecisions(initial);
      })
      .catch((e) => setError(e.message || "Could not load a cleaning plan."))
      .finally(() => setLoading(false));
  }, [datasetId]);

  const decide = (id, decision) => setDecisions((d) => ({ ...d, [id]: decision }));

  const approvedCount = steps.filter((s) => decisions[s.id] !== "rejected").length;

  const apply = async () => {
    const approvedSteps = steps.filter((s) => decisions[s.id] !== "rejected");
    if (!approvedSteps.length) return;
    setApplying(true);
    setError("");
    try {
      const res = await applyFeaturePlan(datasetId, approvedSteps);
      setResult(res);
    } catch (e) {
      setError(e.message || "Applying these changes failed.");
    } finally {
      setApplying(false);
    }
  };

  return (
    <main className="container">
      <button className="chatBackBtn" onClick={() => navigate(`/dataset/${datasetId}`)}>
        <ArrowLeft size={18} /> <span>Back to overview</span>
      </button>

      <div className="sectionHeading" style={{ marginTop: 16 }}>
        <h2>
          <Sparkles size={18} style={{ verticalAlign: "-3px" }} /> Clean &amp; prepare data
        </h2>
        <p>Review each proposed change — nothing touches your CSV until you approve and apply it.</p>
      </div>

      {error && (
        <div className="error">
          <AlertTriangle size={18} /> {error}
        </div>
      )}

      {loading && (
        <div style={{ padding: 60, textAlign: "center", color: "#8792a3" }}>
          <Loader2 className="spin" size={26} />
        </div>
      )}

      {!loading && result && (
        <div className="completeBanner">
          <div className="completeIcon">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <h3>Changes applied to your dataset</h3>
            <p>
              Rows: {result.before_schema.num_rows} → {result.after_schema.num_rows} · Columns:{" "}
              {result.before_schema.num_columns} → {result.after_schema.num_columns}
            </p>
          </div>
        </div>
      )}

      {!loading && !result && steps.length === 0 && !error && (
        <p style={{ color: "#6b7280", fontSize: 13 }}>
          No cleaning steps were proposed for this dataset — it already looks tidy.
        </p>
      )}

      {!loading &&
        !result &&
        steps.map((step) => {
          const decision = decisions[step.id];
          return (
            <div key={step.id} className="chartBlock" style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                <div>
                  <strong style={{ fontSize: 13 }}>{stepLabel(step)}</strong>
                  {step.description && (
                    <p style={{ margin: "4px 0 0", fontSize: 11, color: "#6b7280" }}>{step.description}</p>
                  )}
                </div>
                <div className="chartApprovalRow">
                  <button
                    className="approveBtn"
                    style={{ opacity: decision === "approved" ? 1 : 0.45 }}
                    onClick={() => decide(step.id, "approved")}
                  >
                    <CheckCircle2 size={13} /> Keep
                  </button>
                  <button
                    className="rejectBtn"
                    style={{ opacity: decision === "rejected" ? 1 : 0.45 }}
                    onClick={() => decide(step.id, "rejected")}
                  >
                    <X size={13} /> Skip
                  </button>
                </div>
              </div>
            </div>
          );
        })}

      {!loading && !result && steps.length > 0 && (
        <button className="analyzeButton" onClick={apply} disabled={applying || approvedCount === 0}>
          {applying ? (
            <>
              <Loader2 className="spin" size={18} /> Applying to your CSV...
            </>
          ) : (
            <>
              <Wand2 size={18} /> Apply {approvedCount} change{approvedCount === 1 ? "" : "s"} to dataset
            </>
          )}
        </button>
      )}

      {result && (
        <>
          <div className="schemaCard" style={{ marginTop: 18 }}>
            <div className="sectionTitle">
              <div>
                <h3>Updated schema</h3>
                <p>Real stats computed from the CSV as it now sits on disk.</p>
              </div>
            </div>
            <div className="columnList">
              {result.after_schema.columns.map((col) => (
                <div className="columnRow" key={col.name}>
                  <div>
                    <strong>{col.name}</strong>
                    <span>{col.dtype}</span>
                  </div>
                  <div className="columnMeta">
                    {col.num_missing > 0 && <span className="missing">{col.num_missing} missing</span>}
                    <span>{col.num_unique} unique</span>
                    {typeof col.mean === "number" && <span>mean {col.mean.toFixed(2)}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button className="analyzeButton" style={{ marginTop: 14 }} onClick={() => navigate(`/dataset/${datasetId}`)}>
            Go re-analyze the updated dataset
          </button>
        </>
      )}
    </main>
  );
}

export default FeatureEngineeringScreen;