import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Maximize2 } from "lucide-react";

export const PIE_COLORS = [
  "#636EFA", "#00CC96", "#EF553B", "#AB63FA",
  "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
  "#FF97FF", "#FECB52",
];

const LINE_COLOR = "#00CC96";
const SCATTER_COLOR = "#EF553B";

const tooltipStyle = {
  background: "#ffffff",
  border: "1px solid #e2e6ee",
  borderRadius: 8,
  fontSize: 12,
  color: "#1a2233",
};

const axisLabelStyle = { fontSize: 11, fill: "#4b5563", fontWeight: 600 };

function ExpandButton({ onExpand }) {
  if (!onExpand) return null;
  return (
    <button className="chartExpandBtn" onClick={onExpand} title="View fullscreen">
      <Maximize2 size={14} />
    </button>
  );
}

function ChartRenderer({ proposal, onExpand, large = false }) {
  const { chart_type, data } = proposal;
  const height = large ? 420 : 260;

  let body = null;

  if (chart_type === "pie") {
    const chartData = data.labels.map((label, i) => ({ name: label, value: data.values[i] }));
    body = (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            outerRadius={large ? 140 : 85}
            label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="#fff" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "bar" || chart_type === "histogram") {
    const chartData = data.labels.map((label, i) => ({ name: label, value: data.values[i] }));
    body = (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 10, right: 12, left: 4, bottom: chartData.length > 5 ? 30 : 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef1f7" />
          <XAxis
            dataKey="name"
            stroke="#697589"
            fontSize={10}
            interval={0}
            angle={chartData.length > 5 ? -30 : 0}
            textAnchor={chartData.length > 5 ? "end" : "middle"}
            height={chartData.length > 5 ? 50 : 30}
            label={{ value: data.x_label, position: "insideBottom", offset: -4, style: axisLabelStyle }}
          />
          <YAxis
            stroke="#697589"
            fontSize={10}
            width={42}
            allowDecimals={false}
            label={{ value: data.y_label, angle: -90, position: "insideLeft", style: axisLabelStyle }}
          />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(99,110,250,0.08)" }} />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "grouped_bar") {
    const chartData = data.labels.map((label, i) => {
      const row = { name: label };
      data.categories.forEach((cat) => {
        row[cat] = data.series[cat][i];
      });
      return row;
    });
    body = (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 10, right: 12, left: 4, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef1f7" />
          <XAxis
            dataKey="name"
            stroke="#697589"
            fontSize={10}
            label={{ value: data.x_label, position: "insideBottom", offset: -4, style: axisLabelStyle }}
          />
          <YAxis
            stroke="#697589"
            fontSize={10}
            width={42}
            allowDecimals={false}
            label={{ value: data.y_label, angle: -90, position: "insideLeft", style: axisLabelStyle }}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {data.categories.map((cat, i) => (
            <Bar key={cat} dataKey={cat} fill={PIE_COLORS[i % PIE_COLORS.length]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "line") {
    const chartData = data.labels.map((label, i) => ({ name: label, value: data.values[i] }));
    body = (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 10, right: 12, left: 4, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef1f7" />
          <XAxis
            dataKey="name"
            stroke="#697589"
            fontSize={9}
            hide={chartData.length > 30}
            label={{ value: data.x_label, position: "insideBottom", offset: -4, style: axisLabelStyle }}
          />
          <YAxis
            stroke="#697589"
            fontSize={10}
            width={42}
            label={{ value: data.y_label, angle: -90, position: "insideLeft", style: axisLabelStyle }}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Line type="monotone" dataKey="value" stroke={LINE_COLOR} strokeWidth={2.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "scatter") {
    body = (
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 10, right: 12, left: 4, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef1f7" />
          <XAxis
            type="number"
            dataKey="x"
            name={data.x_label}
            stroke="#697589"
            fontSize={10}
            label={{ value: data.x_label, position: "insideBottom", offset: -4, style: axisLabelStyle }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={data.y_label}
            stroke="#697589"
            fontSize={10}
            width={42}
            label={{ value: data.y_label, angle: -90, position: "insideLeft", style: axisLabelStyle }}
          />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={tooltipStyle} />
          <Scatter data={data.points} fill={SCATTER_COLOR} fillOpacity={0.75} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "heatmap") {
    const columns = Object.keys(data.matrix);
    body = (
      <div className="heatmapWrap">
        <div className="heatmapGrid" style={{ gridTemplateColumns: `110px repeat(${columns.length}, 1fr)` }}>
          <div />
          {columns.map((col) => (
            <div key={`h-${col}`} className="heatmapHeader">{col}</div>
          ))}
          {columns.map((row) => (
            <HeatmapRow key={row} row={row} columns={columns} matrix={data.matrix} />
          ))}
        </div>
      </div>
    );
  }

  if (!body) {
    body = <p className="chartUnsupported">Couldn't render this chart type.</p>;
  }

  return (
    <div className="chartRendererWrap">
      <ExpandButton onExpand={onExpand} />
      {body}
    </div>
  );
}

function HeatmapRow({ row, columns, matrix }) {
  return (
    <>
      <div className="heatmapRowLabel">{row}</div>
      {columns.map((col) => {
        const val = Number(matrix[row]?.[col] ?? 0);
        const intensity = Math.min(Math.abs(val), 1);
        const bg =
          val >= 0
            ? `rgba(0, 204, 150, ${0.18 + intensity * 0.72})`
            : `rgba(239, 85, 59, ${0.18 + intensity * 0.72})`;
        const textColor = intensity > 0.55 ? "#ffffff" : "#10192b";
        return (
          <div key={`${row}-${col}`} className="heatmapCell" style={{ background: bg, color: textColor }}>
            {val.toFixed(2)}
          </div>
        );
      })}
    </>
  );
}

export function ChartsSection({ analysisResults, onExpandChart }) {
  if (!analysisResults?.length) return null;

  const blocks = analysisResults
    .filter((item) => item.status === "ok")
    .map((item, idx) => {
      const step = item.step || {};

      if (step.type === "value_counts") {
        return wrapAsBarProposal(`Distribution: ${step.column}`, step.column, item.result, idx, onExpandChart);
      }
      if (step.type === "groupby_mean") {
        return wrapAsBarProposal(
          `Avg ${step.target_col} by ${step.group_col}`,
          step.group_col,
          item.result,
          idx,
          onExpandChart
        );
      }
      if (step.type === "missing_report") {
        const withMissing = Object.fromEntries(Object.entries(item.result).filter(([, v]) => Number(v) > 0));
        if (!Object.keys(withMissing).length) return null;
        return wrapAsBarProposal("Missing values by column", "column", withMissing, idx, onExpandChart);
      }
      if (step.type === "correlation") {
        const proposal = { chart_type: "heatmap", title: "Correlation matrix", data: { matrix: item.result } };
        return (
          <div className="chartBlock chartBlockWide" key={idx}>
            <h4>Correlation matrix</h4>
            <ChartRenderer proposal={proposal} onExpand={onExpandChart ? () => onExpandChart(proposal) : undefined} />
          </div>
        );
      }
      return null;
    })
    .filter(Boolean);

  if (!blocks.length) return null;

  return (
    <div className="chartsCard">
      <div className="sectionTitle">
        <div>
          <h3>Visual breakdown</h3>
          <p>Charts generated straight from the computed analysis — real numbers, not illustrations.</p>
        </div>
      </div>
      <div className="chartsGrid">{blocks}</div>
    </div>
  );
}

function wrapAsBarProposal(title, xLabel, resultObj, idx, onExpandChart) {
  const labels = Object.keys(resultObj);
  const values = Object.values(resultObj).map(Number);
  const proposal = {
    chart_type: "bar",
    title,
    data: { labels, values, x_label: xLabel, y_label: "value" },
  };
  return (
    <div className="chartBlock" key={idx}>
      <h4>{title}</h4>
      <ChartRenderer proposal={proposal} onExpand={onExpandChart ? () => onExpandChart(proposal) : undefined} />
    </div>
  );
}

export default ChartRenderer;

