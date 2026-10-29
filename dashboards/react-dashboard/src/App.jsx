
import "./App.css";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  BatteryCharging,
  CalendarDays,
  ChevronDown,
  House,
  LayoutDashboard,
  Leaf,
  Menu,
  Settings,
  X,
  Zap,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { loadEnergyData } from "./services/energyData";

const number = (value, digits = 2) =>
  Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: digits,
  });

const compact = (value) => {
  const n = Number(value || 0);
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(2)}K`;
  return number(n);
};

const dateLabel = (value) => {
  if (!value) return "—";
  return new Date(`${value}T12:00:00`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

const monthLabel = (value) => {
  if (!value) return "—";
  return new Date(`${value.slice(0, 7)}-02T12:00:00`).toLocaleDateString(
    "en-IN",
    { month: "short", year: "2-digit" }
  );
};

const sections = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "consumption", label: "Consumption", icon: BarChart3 },
  { id: "tariffs", label: "Tariff analysis", icon: Zap },
  { id: "households", label: "Households", icon: House },
  { id: "forecast", label: "Forecasting", icon: Activity },
  { id: "settings", label: "Settings", icon: Settings },
];

function Sidebar({ activeSection, setActiveSection, mobileOpen, setMobileOpen }) {
  return (
    <>
      {mobileOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-icon"><Zap size={23} /></div>
          <div>
            <h2>GRID_PULSE</h2>
            <span>ENERGY INTELLIGENCE</span>
          </div>
          <button
            className="mobile-close icon-button"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav className="navigation" aria-label="Main navigation">
          {sections.map(({ id, label, icon: Icon }) => (
            <a
              key={id}
              className={`nav-item ${activeSection === id ? "active" : ""}`}
              href={`#${id}`}
              onClick={() => {
                setActiveSection(id);
                setMobileOpen(false);
              }}
            >
              <Icon size={19} />
              {label}
            </a>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="eco-card">
            <Leaf size={21} />
            <strong>Smarter energy insights</strong>
            <p>Explore consumption patterns and make data-informed decisions.</p>
          </div>
          <span className="sidebar-version">GRID_PULSE · Analytics</span>
        </div>
      </aside>
    </>
  );
}

function MetricCard({ title, value, unit, caption, icon: Icon }) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span>{title}</span>
        <div className="metric-icon"><Icon size={19} /></div>
      </div>
      <div className="metric-value">
        {value}<span>{unit}</span>
      </div>
      <p className="metric-caption">{caption}</p>
    </article>
  );
}

function PanelHeading({ title, subtitle, children }) {
  return (
    <div className="panel-heading">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

function EnergyTooltip({ active, payload, label, period }) {
  if (!active || !payload?.length) return null;

  const displayedLabel =
    period === "Monthly" ? monthLabel(label) : dateLabel(label);

  return (
    <div className="chart-tooltip">
      <strong>{displayedLabel}</strong>
      <p>{number(payload[0].value)} kWh</p>
    </div>
  );
}

function TrendChart({ data, period }) {
  if (!data.length) {
    return <div className="empty-state">No data is available for this selection.</div>;
  }

  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        <span className="legend-dot" />
        Energy consumption
        <span className="chart-note">Processed dataset</span>
      </div>

      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height="100%">
          {period === "Monthly" ? (
            <AreaChart data={data} margin={{ top: 10, right: 12, left: 4, bottom: 4 }}>
              <defs>
                <linearGradient id="energyFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#45d6ad" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#45d6ad" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#25383d" strokeDasharray="3 3" />
              <XAxis
                dataKey="month"
                tickFormatter={monthLabel}
                tick={{ fill: "#91a9ae", fontSize: 11 }}
                minTickGap={14}
              />
              <YAxis
                tickFormatter={(value) => compact(value)}
                tick={{ fill: "#91a9ae", fontSize: 11 }}
                width={55}
              />
              <Tooltip content={<EnergyTooltip period={period} />} />
              <Area
                type="monotone"
                dataKey="monthly_energy_kwh"
                name="Energy"
                stroke="#45d6ad"
                strokeWidth={2.5}
                fill="url(#energyFill)"
                activeDot={{ r: 5, fill: "#45d6ad" }}
              />
            </AreaChart>
          ) : (
            <BarChart data={data} margin={{ top: 10, right: 12, left: 4, bottom: 4 }}>
              <CartesianGrid stroke="#25383d" strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) =>
                  new Date(`${value}T12:00:00`).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                  })
                }
                tick={{ fill: "#91a9ae", fontSize: 11 }}
                minTickGap={18}
              />
              <YAxis
                tickFormatter={(value) => compact(value)}
                tick={{ fill: "#91a9ae", fontSize: 11 }}
                width={55}
              />
              <Tooltip content={<EnergyTooltip period={period} />} />
              <Bar
                dataKey="total_energy_kwh"
                name="Energy"
                fill="#45d6ad"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      <p className="chart-caption">
        {period === "Monthly"
          ? "Monthly totals in kWh. Incomplete months reflect available dates."
          : "Daily totals in kWh. Use the date filter to change the period."}
      </p>
    </div>
  );
}

function TariffCard({ tariffs }) {
  const [showDetails, setShowDetails] = useState(false);
  const standard = tariffs.find((row) => row.tariff_type === "Std");
  const tou = tariffs.find((row) => row.tariff_type === "ToU");

  const rows = [
    { row: standard, label: "Standard tariff", type: "standard" },
    { row: tou, label: "Time-of-use tariff", type: "tou" },
  ];

  return (
    <section className="panel" id="tariffs">
      <PanelHeading
        title="Tariff distribution"
        subtitle="Share of recorded energy consumption"
      >
        <button
          className="icon-button"
          aria-label={showDetails ? "Hide tariff details" : "Show tariff details"}
          aria-expanded={showDetails}
          onClick={() => setShowDetails((value) => !value)}
        >
          <ChevronDown className={showDetails ? "rotate-icon" : ""} size={19} />
        </button>
      </PanelHeading>

      {rows.map(({ row, label, type }) => {
        const share = Number(row?.energy_share_percent || 0);
        return (
          <div className="tariff-row" key={type}>
            <div className="tariff-label">
              <span className={`tariff-dot ${type}`} />
              <span>{label}</span>
              <strong>{share.toFixed(2)}%</strong>
            </div>
            <div
              className="progress-track"
              role="progressbar"
              aria-label={label}
              aria-valuenow={share}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className={`progress-fill ${type}-fill`}
                style={{ width: `${Math.max(0, Math.min(100, share))}%` }}
              />
            </div>
          </div>
        );
      })}

      {showDetails && (
        <div className="tariff-details">
          {rows.map(({ row, label, type }) => (
            <div key={type} className="detail-row">
              <span>{label} energy</span>
              <strong>{number(row?.total_energy_kwh)} kWh</strong>
            </div>
          ))}
          <p>
            Shares describe energy recorded under each tariff. They do not
            establish that one tariff causes higher or lower consumption.
          </p>
        </div>
      )}

      <p className="panel-footnote">
        Based on the full processed tariff summary.
      </p>
    </section>
  );
}

function App() {
  const [energyData, setEnergyData] = useState({
    daily: [],
    monthly: [],
    tariffs: [],
  });
  const [loading, setLoading] = useState(true);
  const [dataError, setDataError] = useState("");
  const [dateRange, setDateRange] = useState("Full dataset");
  const [chartPeriod, setChartPeriod] = useState("Monthly");
  const [activeSection, setActiveSection] = useState("overview");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    loadEnergyData()
      .then((data) => {
        if (!cancelled) setEnergyData(data);
      })
      .catch((error) => {
        if (!cancelled) setDataError(error.message || "Unable to load CSV data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredDaily = useMemo(() => {
    const daily = energyData.daily;
    if (!daily.length || dateRange === "Full dataset") return daily;

    const lastDate = new Date(`${daily[daily.length - 1].date}T12:00:00`);
    const cutoff = new Date(lastDate);

    if (dateRange === "Last 12 months") {
      cutoff.setFullYear(cutoff.getFullYear() - 1);
    } else {
      cutoff.setDate(
        cutoff.getDate() - (dateRange === "Last 30 days" ? 30 : 90) + 1
      );
    }

    return daily.filter(
      (row) => new Date(`${row.date}T12:00:00`) >= cutoff
    );
  }, [energyData.daily, dateRange]);

  const filteredMonthly = useMemo(() => {
    if (dateRange === "Full dataset") return energyData.monthly;
    if (!filteredDaily.length) return [];

    const firstMonth = filteredDaily[0].date.slice(0, 7);
    const lastMonth = filteredDaily[filteredDaily.length - 1].date.slice(0, 7);

    return energyData.monthly.filter((row) => {
      const month = row.month.slice(0, 7);
      return month >= firstMonth && month <= lastMonth;
    });
  }, [energyData.monthly, filteredDaily, dateRange]);

  const chartData = chartPeriod === "Monthly" ? filteredMonthly : filteredDaily;

  const totalEnergy = filteredDaily.reduce(
    (sum, row) => sum + Number(row.total_energy_kwh || 0),
    0
  );

  const averageDailyEnergy = filteredDaily.length
    ? totalEnergy / filteredDaily.length
    : 0;

  const averageHouseholds = filteredDaily.length
    ? filteredDaily.reduce(
        (sum, row) => sum + Number(row.households || 0),
        0
      ) / filteredDaily.length
    : 0;

  const totalReadings = filteredDaily.reduce(
    (sum, row) => sum + Number(row.total_readings || 0),
    0
  );

  const highestDay = filteredDaily.reduce(
    (best, row) =>
      !best || row.total_energy_kwh > best.total_energy_kwh ? row : best,
    null
  );

  const lowestDay = filteredDaily.reduce(
    (best, row) =>
      !best || row.total_energy_kwh < best.total_energy_kwh ? row : best,
    null
  );

  const metrics = [
    {
      title: "Total energy",
      value: compact(totalEnergy),
      unit: "kWh",
      caption: dateRange,
      icon: Zap,
    },
    {
      title: "Average daily energy",
      value: compact(averageDailyEnergy),
      unit: "kWh",
      caption: `Across ${filteredDaily.length} available dates`,
      icon: Activity,
    },
    {
      title: "Households per day",
      value: number(averageHouseholds, 0),
      unit: "average",
      caption: "Represented households",
      icon: House,
    },
    {
      title: "Raw readings",
      value: compact(totalReadings),
      unit: "records",
      caption: "Counts from daily summaries",
      icon: BatteryCharging,
    },
  ];

  return (
    <div className="app-shell">
      <Sidebar
        activeSection={activeSection}
        setActiveSection={setActiveSection}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={21} />
            </button>
            Workspace <span>/</span> {sections.find((s) => s.id === activeSection)?.label}
          </div>
          <div className="topbar-right">
            <span className={`status-dot ${dataError ? "status-error" : ""}`} />
            {loading ? "Loading data" : dataError ? "Data unavailable" : "Processed dataset"}
            <div className="avatar">GP</div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <p className="eyebrow">ENERGY ANALYTICS PLATFORM</p>
            <h1>Energy overview</h1>
            <p className="page-description">
              Understand consumption patterns across the available household energy data.
            </p>
          </div>

          <div className="date-filter">
            <CalendarDays size={17} />
            <select
              className="dashboard-select"
              aria-label="Select date range"
              value={dateRange}
              onChange={(event) => setDateRange(event.target.value)}
            >
              <option>Full dataset</option>
              <option>Last 30 days</option>
              <option>Last 90 days</option>
              <option>Last 12 months</option>
            </select>
            <ChevronDown size={16} />
          </div>
        </section>

        {loading && <div className="loading-message">Loading energy analytics…</div>}

        {dataError && (
          <div className="data-error" role="alert">
            <strong>Unable to load dashboard data</strong>
            <p>{dataError}</p>
            <p>Check the files in public/data and refresh the page.</p>
          </div>
        )}

        {!loading && !dataError && (
          <>
            <section className="metrics-grid">
              {metrics.map((metric) => (
                <MetricCard key={metric.title} {...metric} />
              ))}
            </section>

            <section className="content-grid" id="consumption">
              <div className="panel trend-panel">
                <PanelHeading
                  title="Consumption trends"
                  subtitle={chartPeriod === "Monthly"
                    ? "Monthly energy totals"
                    : "Daily energy totals"}
                >
                  <div className="period-filter">
                    <select
                      className="dashboard-select"
                      value={chartPeriod}
                      aria-label="Select chart frequency"
                      onChange={(event) => setChartPeriod(event.target.value)}
                    >
                      <option>Monthly</option>
                      <option>Daily</option>
                    </select>
                    <ChevronDown size={15} />
                  </div>
                </PanelHeading>
                <TrendChart data={chartData} period={chartPeriod} />
              </div>

              <TariffCard tariffs={energyData.tariffs} />
            </section>

            <section className="bottom-grid">
              <div className="insight-panel">
                <div className="insight-icon"><ArrowUpRight size={21} /></div>
                <div>
                  <span className="insight-label">HIGHEST DAILY ENERGY IN SELECTION</span>
                  <h3>{number(highestDay?.total_energy_kwh)} kWh</h3>
                  <p>{highestDay ? dateLabel(highestDay.date) : "No data available"}</p>
                </div>
              </div>
              <div className="insight-panel">
                <div className="insight-icon muted"><ArrowDownRight size={21} /></div>
                <div>
                  <span className="insight-label">LOWEST DAILY ENERGY IN SELECTION</span>
                  <h3>{number(lowestDay?.total_energy_kwh)} kWh</h3>
                  <p>
                    {lowestDay
                      ? `${dateLabel(lowestDay.date)} · Check coverage for partial dates`
                      : "No data available"}
                  </p>
                </div>
              </div>
            </section>

            <section className="panel section-panel" id="households">
              <PanelHeading
                title="Household analytics"
                subtitle="Coverage and average daily energy per household"
              />
              <div className="household-grid">
                <div className="household-stat">
                  <span>Average households per day</span>
                  <strong>{number(averageHouseholds, 0)}</strong>
                </div>
                <div className="household-stat">
                  <span>Average energy per household</span>
                  <strong>
                    {number(
                      filteredDaily.length
                        ? filteredDaily.reduce(
                            (sum, row) =>
                              sum + Number(row.energy_per_household_kwh || 0),
                            0
                          ) / filteredDaily.length
                        : 0
                    )} kWh
                  </strong>
                </div>
                <div className="household-stat">
                  <span>Dates represented</span>
                  <strong>{filteredDaily.length}</strong>
                </div>
              </div>
              <p className="panel-footnote">
                Household averages are calculated from the daily summary rows.
                They are not individual household profiles.
              </p>
            </section>

            <section className="panel section-panel" id="forecast">
              <PanelHeading
                title="Forecasting"
                subtitle="Forecast readiness"
              />
              <div className="forecast-status">
                <div className="forecast-icon"><Activity size={24} /></div>
                <div>
                  <h4>No forecast model connected</h4>
                  <p>
                    This dashboard currently displays historical observations.
                    Connect a trained forecasting model or export its predictions
                    to a forecast dataset before displaying predicted values.
                  </p>
                </div>
              </div>
            </section>

            <section className="panel section-panel" id="settings">
              <PanelHeading
                title="Dashboard settings"
                subtitle="Current view and dataset details"
              />
              <div className="settings-grid">
                <div>
                  <span>Date range</span>
                  <strong>{dateRange}</strong>
                </div>
                <div>
                  <span>Chart frequency</span>
                  <strong>{chartPeriod}</strong>
                </div>
                <div>
                  <span>Daily summary rows</span>
                  <strong>{energyData.daily.length}</strong>
                </div>
                <div>
                  <span>Monthly summary rows</span>
                  <strong>{energyData.monthly.length}</strong>
                </div>
              </div>
              <button
                className="secondary-button"
                onClick={() => {
                  setDateRange("Full dataset");
                  setChartPeriod("Monthly");
                }}
              >
                Reset filters
              </button>
            </section>
          </>
        )}

        <footer className="footer">
          <span><Zap size={14} /> GRID_PULSE</span>
          <span>Data engineering · Energy intelligence</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
