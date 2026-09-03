import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { Plus, FileSpreadsheet, Menu, X } from "lucide-react";
import { fetchDatasetList } from "../api";

function Sidebar() {
  const [datasets, setDatasets] = useState([]);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { datasetId: activeId } = useParams();

  const refresh = () => fetchDatasetList().then(setDatasets).catch(() => {});

  useEffect(() => {
    refresh();
  }, [location.pathname]);

  return (
    <>
      <button className="sidebarToggle" onClick={() => setMobileOpen(true)}>
        <Menu size={20} />
      </button>

      <aside className={`sidebar ${mobileOpen ? "open" : ""}`}>
        <div className="sidebarHeader">
          <span>Your datasets</span>
          <button className="sidebarClose" onClick={() => setMobileOpen(false)}>
            <X size={18} />
          </button>
        </div>

        <button
          className="newDatasetBtn"
          onClick={() => {
            navigate("/");
            setMobileOpen(false);
          }}
        >
          <Plus size={16} /> New dataset
        </button>

        <div className="sidebarList">
          {datasets.length === 0 && <div className="sidebarEmpty">No datasets yet</div>}
          {datasets.map((d) => (
            <button
              key={d.file_id}
              className={`sidebarItem ${d.file_id === activeId ? "active" : ""}`}
              onClick={() => {
                navigate(`/dataset/${d.file_id}`);
                setMobileOpen(false);
              }}
              title={d.filename}
            >
              <FileSpreadsheet size={15} />
              <span className="sidebarItemName">{d.filename}</span>
            </button>
          ))}
        </div>
      </aside>

      {mobileOpen && <div className="sidebarBackdrop" onClick={() => setMobileOpen(false)} />}
    </>
  );
}

export default Sidebar;

