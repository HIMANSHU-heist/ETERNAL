import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import HomeScreen from "./screens/HomeScreen";
import OverviewScreen from "./screens/OverviewScreen";
import ChatScreen from "./screens/ChatScreen";
import "./App.css";

function App() {
  return (
    <div className="appShell">
      <Sidebar />
      <div className="mainArea">
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/dataset/:datasetId" element={<OverviewScreen />} />
          <Route path="/dataset/:datasetId/chat" element={<ChatScreen />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
