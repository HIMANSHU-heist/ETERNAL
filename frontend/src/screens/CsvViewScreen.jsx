import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, ChevronLeft, ChevronRight, Loader2, AlertTriangle } from "lucide-react";
import { fetchDatasetCsv } from "../api";

const PAGE_SIZE = 50;

function CsvViewScreen() {
  const { datasetId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    fetchDatasetCsv(datasetId, page, PAGE_SIZE)
      .then(setData)
      .catch((e) => setError(e.message || "Could not load this dataset."))
      .finally(() => setLoading(false));
  }, [datasetId, page]);

  return (
    <main className="container">
      <button className="chatBackBtn" onClick={() => navigate(`/dataset/${datasetId}`)}>
        <ArrowLeft size={18} /> <span>Back to overview</span>
      </button>

      <div className="sectionHeading" style={{ marginTop: 16 }}>
        <h2>Dataset preview</h2>
        {data && (
          <p>
            {data.total_rows.toLocaleString()} rows total · showing {PAGE_SIZE} at a time so large files stay
            fast
          </p>
        )}
      </div>

      {error && (
        <div className="error">
          <AlertTriangle size={18} /> {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: 60, textAlign: "center", color: "#8792a3" }}>
          <Loader2 className="spin" size={26} />
        </div>
      ) : (
        data && (
          <>
            <div className="csvTableWrap">
              <table className="csvTable">
                <thead>
                  <tr>
                    {data.columns.map((c) => (
                      <th key={c}>{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row, i) => (
                    <tr key={i}>
                      {data.columns.map((c) => (
                        <td key={c}>{String(row[c])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="csvPager">
              <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                <ChevronLeft size={16} /> Prev
              </button>
              <span>
                Page {data.page} of {data.total_pages}
              </span>
              <button disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)}>
                Next <ChevronRight size={16} />
              </button>
            </div>
          </>
        )
      )}
    </main>
  );
}

export default CsvViewScreen;