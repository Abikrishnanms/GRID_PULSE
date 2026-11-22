import { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  Info,
  CalendarDays,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

const FORECAST_CSV_URL = "/data/forecast_30_days.csv";

const formatDateLabel = (value) => {
  if (!value) return "—";
  return new Date(`${value}T12:00:00`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

const formatShortDate = (value) => {
  if (!value) return "—";
  return new Date(`${value}T12:00:00`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
};

function ForecastTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const value = Number(payload[0].value || 0);

  return (
    <div className="chart-tooltip">
      <strong>{formatDateLabel(label)}</strong>
      <p style={{ margin: "4px 0 0 0", color: "var(--accent)" }}>
        {value.toFixed(2)} kWh / household
      </p>
    </div>
  );
}

export default function HistoricalForecastChart() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadForecastData() {
      try {
        const response = await fetch(FORECAST_CSV_URL);
        if (!response.ok) {
          throw new Error(
            `Unable to fetch forecast file (${FORECAST_CSV_URL}). HTTP ${response.status}: ${response.statusText}`
          );
        }

        const text = await response.text();
        const lines = text.trim().split(/\r?\n/);
        if (lines.length < 2) {
          throw new Error("Forecast CSV contains no data rows.");
        }

        const headers = lines[0]
          .replace(/^\uFEFF/, "")
          .split(",")
          .map((h) => h.trim());

        const dateIdx = headers.indexOf("date");
        const valIdx = headers.indexOf("predicted_energy_per_household_kwh");

        if (dateIdx === -1 || valIdx === -1) {
          throw new Error(
            "Forecast CSV is missing required columns ('date', 'predicted_energy_per_household_kwh')."
          );
        }

        const parsedRows = [];
        for (let i = 1; i < lines.length; i++) {
          const line = lines[i].trim();
          if (!line) continue;
          const parts = line.split(",").map((p) => p.trim());
          if (parts.length < headers.length) continue;

          const rawDate = parts[dateIdx];
          const rawVal = parseFloat(parts[valIdx]);

          if (rawDate && !isNaN(rawVal)) {
            parsedRows.push({
              date: rawDate,
              predicted_energy_per_household_kwh: Number(rawVal.toFixed(4)),
            });
          }
        }

        if (parsedRows.length === 0) {
          throw new Error("No valid forecast observations found in dataset.");
        }

        if (!cancelled) {
          setData(parsedRows);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Failed to load historical forecast dataset.");
          setData([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadForecastData();

    return () => {
      cancelled = true;
    };
  }, []);

  // Compute summary metrics dynamically from the loaded records
  const stats = (() => {
    if (!data.length) return null;

    let minRow = data[0];
    let maxRow = data[0];
    let sum = 0;

    data.forEach((row) => {
      const val = row.predicted_energy_per_household_kwh;
      sum += val;
      if (val < minRow.predicted_energy_per_household_kwh) minRow = row;
      if (val > maxRow.predicted_energy_per_household_kwh) maxRow = row;
    });

    const mean = sum / data.length;

    return {
      daysCount: data.length,
      firstDate: data[0].date,
      lastDate: data[data.length - 1].date,
      minVal: minRow.predicted_energy_per_household_kwh,
      minDate: minRow.date,
      maxVal: maxRow.predicted_energy_per_household_kwh,
      maxDate: maxRow.date,
      meanVal: mean,
      totalVal: sum,
    };
  })();

  return (
    <section className="panel section-panel" id="forecast">
      <div className="panel-heading">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Activity size={20} style={{ color: "var(--accent)" }} />
            <h3>Historical Energy Forecasting</h3>
          </div>
          <p>
            30-day recursive forecast evaluated using Random Forest regression.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--muted)", fontSize: "12px" }}>
          <CalendarDays size={15} />
          <span>30-Day Evaluation Horizon</span>
        </div>
      </div>

      {/* HISTORICAL DEMONSTRATION WARNING BANNER */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "12px",
          padding: "14px 16px",
          background: "rgba(126, 171, 255, 0.08)",
          border: "1px solid rgba(126, 171, 255, 0.25)",
          borderRadius: "10px",
          marginTop: "16px",
        }}
      >
        <Info size={18} style={{ color: "var(--blue)", flexShrink: 0, marginTop: "2px" }} />
        <div style={{ fontSize: "12px", lineHeight: "1.6", color: "#d2e3fc" }}>
          <strong>Historical Demonstration Context:</strong> Historical 30-day forecast demonstration based on data
          available up to 27 February 2014. These predictions are not current household energy forecasts.
        </div>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="loading-message" style={{ marginTop: "16px" }}>
          Loading historical 30-day forecast observations…
        </div>
      )}

      {/* ERROR STATE */}
      {!loading && error && (
        <div className="data-error" role="alert" style={{ marginTop: "16px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
            <AlertTriangle size={18} style={{ color: "var(--danger)", flexShrink: 0 }} />
            <div>
              <strong>Unable to render forecast chart</strong>
              <p style={{ margin: "4px 0 0 0", fontSize: "12px" }}>{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* EMPTY DATA STATE */}
      {!loading && !error && data.length === 0 && (
        <div className="empty-state" style={{ marginTop: "16px" }}>
          No forecast data available in /data/forecast_30_days.csv.
        </div>
      )}

      {/* CHART & STATS CONTENT */}
      {!loading && !error && data.length > 0 && stats && (
        <>
          {/* SUMMARY STATS GRID */}
          <div className="appliance-summary" style={{ marginTop: "18px" }}>
            <div>
              <span>Forecast horizon</span>
              <strong>{stats.daysCount} days</strong>
            </div>
            <div>
              <span>Forecast range</span>
              <strong style={{ fontSize: "12px" }}>
                {formatShortDate(stats.firstDate)} – {formatShortDate(stats.lastDate)}
              </strong>
            </div>
            <div>
              <span>Average projected</span>
              <strong style={{ color: "var(--accent)" }}>
                {stats.meanVal.toFixed(2)} kWh/day
              </strong>
            </div>
            <div>
              <span>Minimum projected</span>
              <strong style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <TrendingDown size={14} style={{ color: "var(--muted)" }} />
                {stats.minVal.toFixed(2)} kWh
              </strong>
              <small style={{ color: "var(--muted)", fontSize: "10px" }}>
                on {formatShortDate(stats.minDate)}
              </small>
            </div>
            <div>
              <span>Maximum projected</span>
              <strong style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <TrendingUp size={14} style={{ color: "var(--accent)" }} />
                {stats.maxVal.toFixed(2)} kWh
              </strong>
              <small style={{ color: "var(--muted)", fontSize: "10px" }}>
                on {formatShortDate(stats.maxDate)}
              </small>
            </div>
          </div>

          {/* RECHARTS AREA / LINE CHART */}
          <div className="chart-wrap" style={{ marginTop: "20px" }}>
            <div className="chart-legend">
              <span className="legend-dot" style={{ background: "var(--accent)" }} />
              Predicted daily energy (kWh / household)
              <span className="chart-note">
                Trained on London SmartMeter 821-day historical summary
              </span>
            </div>

            <div className="chart-canvas" style={{ height: "280px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={data}
                  margin={{
                    top: 10,
                    right: 16,
                    left: 0,
                    bottom: 4,
                  }}
                >
                  <defs>
                    <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#45d6ad" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#45d6ad" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>

                  <CartesianGrid stroke="#25383d" strokeDasharray="3 3" />

                  <XAxis
                    dataKey="date"
                    tickFormatter={formatShortDate}
                    tick={{
                      fill: "#91a9ae",
                      fontSize: 11,
                    }}
                    minTickGap={16}
                  />

                  <YAxis
                    domain={["dataMin - 0.2", "dataMax + 0.2"]}
                    tickFormatter={(val) => Number(val).toFixed(1)}
                    tick={{
                      fill: "#91a9ae",
                      fontSize: 11,
                    }}
                    width={48}
                  />

                  <Tooltip content={<ForecastTooltip />} />

                  <Area
                    type="monotone"
                    dataKey="predicted_energy_per_household_kwh"
                    name="Predicted Energy"
                    stroke="#45d6ad"
                    strokeWidth={2.5}
                    fill="url(#forecastFill)"
                    activeDot={{
                      r: 5,
                      fill: "#45d6ad",
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <p className="chart-caption">
              Daily predictions generated recursively using Member 3&apos;s Random Forest model with lag-1, lag-7, and 7-day rolling features.
            </p>
          </div>
        </>
      )}

      <p className="panel-footnote" style={{ marginTop: "18px" }}>
        Model backtesting achieved an overall MAE of 0.65 kWh/day and MAPE of 6.01% across 5 rolling evaluation origins.
      </p>
    </section>
  );
}
