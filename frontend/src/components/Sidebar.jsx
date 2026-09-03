import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import {
  Plus,
  FileSpreadsheet,
  Menu,
  X,
  ChevronDown,
  ChevronRight,
  Table,
  MessageSquare,
  Sparkles,
  LayoutDashboard,
  RefreshCcwDot,
} from "lucide-react";
import { fetchDatasetList } from "../api";

function Sidebar() {
  const [datasets, setDatasets] = useState([]);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openId, setOpenId] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { datasetId: activeId } = useParams();

  const refresh = () => fetchDatasetList().then(setDatasets).catch(() => {});

  useEffect(() => {
    refresh();
  }, [location.pathname]);

  // keep the active dataset's sub-menu open as you navigate between its screens
  useEffect(() => {
    if (activeId) setOpenId(activeId);
  }, [activeId]);

  const go = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

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

        <button className="newDatasetBtn" onClick={() => go("/")}>
          <Plus size={16} /> New dataset
        </button>

        <div className="sidebarList">
          {datasets.length === 0 && <div className="sidebarEmpty">No datasets yet</div>}

          {datasets.map((d) => {
            const expanded = openId === d.file_id;
            return (
              <div key={d.file_id} className="sidebarGroup">
                <button
                  className={`sidebarItem ${d.file_id === activeId ? "active" : ""}`}
                  onClick={() => setOpenId(expanded ? null : d.file_id)}
                  title={d.filename}
                >
                  {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <FileSpreadsheet size={15} />
                  <span className="sidebarItemName">{d.filename}</span>
                  {d.dirty && <span className="dirtyDot" title="Changed since last analysis" />}
                </button>

                {expanded && (
                  <div className="sidebarSubList">
                    <button className="sidebarSubItem" onClick={() => go(`/dataset/${d.file_id}`)}>
                      <LayoutDashboard size={13} /> Overview
                    </button>
                    <button className="sidebarSubItem" onClick={() => go(`/dataset/${d.file_id}/csv`)}>
                      <Table size={13} /> View CSV
                    </button>
                    <button className="sidebarSubItem" onClick={() => go(`/dataset/${d.file_id}/clean`)}>
                      <Sparkles size={13} /> Clean data
                    </button>
                    <button className="sidebarSubItem" onClick={() => go(`/dataset/${d.file_id}/chat`)}>
                      <MessageSquare size={13} /> Chat
                    </button>
                    {d.dirty && (
                      <div className="sidebarDirtyNote">
                        <RefreshCcwDot size={11} /> Dataset changed — re-analyze in Overview
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </aside>

      {mobileOpen && <div className="sidebarBackdrop" onClick={() => setMobileOpen(false)} />}
    </>
  );
}

export default Sidebar;