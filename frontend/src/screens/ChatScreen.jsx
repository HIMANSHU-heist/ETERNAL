import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Send, Brain, Sparkles, CheckCircle2, X, Paperclip, Wand2, BarChart3, PieChart } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { fetchChatHistory, sendChatMessage, applyFeaturePlan } from "../api";
import ChartRenderer from "../components/ChartRenderer";
import ChartModal from "../components/ChartModal";

const INTENT_META = {
  feature_engineering: { label: "Clean / Modify Data", icon: Wand2 },
  analysis: { label: "Analysis", icon: BarChart3 },
  chart: { label: "Plots & Graphs", icon: PieChart },
};

function ChatScreen() {
  const { datasetId } = useParams();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedChart, setExpandedChart] = useState(null);
  const [intent, setIntent] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const endRef = useRef(null);
  const textareaRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    fetchChatHistory(datasetId)
      .then((history) =>
        setMessages(
          history.map((m) => ({ role: m.role, content: m.content }))
        )
      )
      .catch(() => {});
  }, [datasetId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [question]);

  useEffect(() => {
    const onClickOutside = (e) => {
      if (menuOpen && menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [menuOpen]);

  const ask = async () => {
    if (!question.trim() || loading) return;
    const q = question.trim();
    const activeIntent = intent;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setQuestion("");
    setIntent(null);
    setLoading(true);
    try {
      const res = await sendChatMessage(datasetId, q, activeIntent);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.answer,
          chart_proposal: res.chart_proposal || null,
          chartDecision: null,
          fe_proposal: res.fe_proposal || null,
          feDecision: null,
        },
      ]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: `Sorry, I couldn't answer that. ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const decideChart = (index, decision) => {
    setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, chartDecision: decision } : m)));
  };

  const decideFeature = async (index, decision) => {
    if (decision === "rejected") {
      setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, feDecision: "rejected" } : m)));
      return;
    }
    const steps = messages[index]?.fe_proposal?.steps || [];
    setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, feDecision: "applying" } : m)));
    try {
      await applyFeaturePlan(datasetId, steps);
      setMessages((prev) =>
        prev.map((m, i) => (i === index ? { ...m, feDecision: "applied" } : m))
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m, i) => (i === index ? { ...m, feDecision: "error", feError: err.message } : m))
      );
    }
  };

  const selectIntent = (key) => {
    setIntent(key);
    setMenuOpen(false);
  };

  return (
    <div className="chatScreen">
      <header className="chatScreenHeader">
        <button className="chatBackBtn" onClick={() => navigate(`/dataset/${datasetId}`)}>
          <ArrowLeft size={18} /> Back to overview
        </button>
        <div className="chatScreenTitle">
          <Brain size={18} /> Ask your dataset
        </div>
        <div style={{ width: 140 }} />
      </header>

      <div className="chatScreenMessages">
        {messages.length === 0 && (
          <div className="chatWelcome">
            <Sparkles size={28} />
            <h4>Ask anything about your data</h4>
            <p>Try: "Which factor has the strongest relationship with the outcome?"</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role === "user" ? "user" : "ai"}`}>
            {message.role === "assistant" && (
              <div className="tinyAvatar"><Brain size={13} /></div>
            )}
            <div className="messageBubble">
              {message.role === "assistant" ? (
                <div className="markdownContent">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <p>{message.content}</p>
              )}

              {message.chart_proposal && (
                <div className="chartProposal">
                  {message.chartDecision === "approved" ? (
                    <ChartRenderer
                      proposal={message.chart_proposal}
                      onExpand={() => setExpandedChart(message.chart_proposal)}
                    />
                  ) : message.chartDecision === "rejected" ? (
                    <p className="chartDismissed">Chart dismissed.</p>
                  ) : (
                    <div className="chartApprovalRow">
                      <button className="approveBtn" onClick={() => decideChart(index, "approved")}>
                        <CheckCircle2 size={13} /> Approve
                      </button>
                      <button className="rejectBtn" onClick={() => decideChart(index, "rejected")}>
                        <X size={13} /> Dismiss
                      </button>
                    </div>
                  )}
                </div>
              )}

              {message.fe_proposal && (
                <div className="chartProposal">
                  {message.feDecision === "applied" ? (
                    <p className="chartDismissed" style={{ color: "#22c55e" }}>
                      <CheckCircle2 size={13} /> Applied — {message.fe_proposal.steps.length} step(s) cleaned. Dataset updated.
                    </p>
                  ) : message.feDecision === "rejected" ? (
                    <p className="chartDismissed">Cleaning skipped.</p>
                  ) : message.feDecision === "applying" ? (
                    <p className="chartDismissed">Applying changes…</p>
                  ) : message.feDecision === "error" ? (
                    <p className="chartDismissed" style={{ color: "#ef4444" }}>Failed: {message.feError}</p>
                  ) : (
                    <div className="chartApprovalRow">
                      <button className="approveBtn" onClick={() => decideFeature(index, "approved")}>
                        <CheckCircle2 size={13} /> Approve
                      </button>
                      <button className="rejectBtn" onClick={() => decideFeature(index, "rejected")}>
                        <X size={13} /> Dismiss
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message ai">
            <div className="tinyAvatar"><Brain size={13} /></div>
            <div className="messageBubble typing"><span /><span /><span /></div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {intent && (
        <div className="intentChipRow">
          <span className="intentChip">
            Mode: {INTENT_META[intent].label}
            <button onClick={() => setIntent(null)}><X size={12} /></button>
          </span>
        </div>
      )}

      <div className="chatScreenInput">
        <div className="chatInputTools" ref={menuRef}>
          <button className="pinBtn" onClick={() => setMenuOpen((o) => !o)} title="Choose action">
            <Paperclip size={18} />
          </button>
          {menuOpen && (
            <div className="intentMenu">
              {Object.entries(INTENT_META).map(([key, meta]) => {
                const Icon = meta.icon;
                return (
                  <button key={key} className="intentMenuItem" onClick={() => selectIntent(key)}>
                    <Icon size={14} /> {meta.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <textarea
          ref={textareaRef}
          rows={1}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              ask();
            }
          }}
          placeholder="Ask a question about your dataset..."
        />
        <button onClick={ask} disabled={loading || !question.trim()}>
          <Send size={18} />
        </button>
      </div>

      {expandedChart && <ChartModal proposal={expandedChart} onClose={() => setExpandedChart(null)} />}
    </div>
  );
}

export default ChatScreen;