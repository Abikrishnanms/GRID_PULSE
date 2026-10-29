
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
  Settings,
  Zap,
} from "lucide-react";
import { loadEnergyData } from "./services/energyData";

const formatNumber = (value, digits = 2) =>
  Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });

const formatCompact = (value) => {
  const number = Number(value || 0);

  if (Math.abs(number) >= 1_000_000) {
    return `${(number / 1_000_000).toFixed(2)}M`;
  }

  if (Math.abs(number) >= 1_000) {
    return `${(number / 1_000).toFixed(2)}K`;
  }

  return formatNumber(number);
};

const formatDate = (dateString) =>
  new Date(`${dateString}T12:00:00`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <Zap size={23} />
        </div>
        <div>
          <h2>GRID_PULSE</h2>
          <span>ENERGY INTELLIGENCE</span>
        </div>
      </div>

      <div className="nav-label">WORKSPACE</div>

      <nav className="navigation">
        <a className="nav-item active" href="#overview">
          <LayoutDashboard size={19} /> Overview
        </a>
        <a className="nav-item" href="#consumption">
          <BarChart3 size={19} /> Consumption
        </a>
        <a className="nav-item" href="#tariffs">
          <Zap size={19} /> Tariff analysis
        </a>
        <a className="nav-item" href="#households">
          <House size={19} /> Households
        </a>
        <a className="nav-item" href="#forecast">
          <Activity size={19} /> Forecasting
        </a>
      </nav>

      <div className="sidebar-bottom">
        <div className="eco-card">
          <Leaf size={21} />
          <strong>Smarter energy insights</strong>
          <p>
            Explore consumption patterns and make data-informed decisions.
          </p>
        </div>

        <a className="nav-item" href="#settings">
          <Settings size={19} /> Settings
        </a>
      </div>
    </aside>
  );
}

function MetricCard({ metric }) {
  const Icon = metric.icon;

  return (
    <article className="metric-card">
      <div className="metric-top">
        <span>{metric.title}</span>
        <div className="metric-icon">
          <Icon size={19} />
        </div>
      </div>

      <div className="metric-value">
        {metric.value}
        <span>{metric.unit}</span>
      </div>

      <p className="metric-caption">{metric.change}</p>
    </article>
  );
}

function TrendChart({ dailyData, monthlyData, chartPeriod }) {
  const chartData = useMemo(() => {
    if (chartPeriod === "Daily") {
      return dailyData.map((item) => ({
        label: item.date,
        displayLabel: new Date(
          `${item.date}T12:00:00`
        ).toLocaleDateString("en-IN", {
          day: "numeric",
          month: "short",
        }),
        energy: Number(item.total_energy_kwh || 0),
      }));
    }

    return monthlyData.map((item) => ({
      label: item.month,
      displayLabel: new Date(
        `${item.month.slice(0, 7)}-02T12:00:00`
      ).toLocaleDateString("en-IN", {
        month: "short",
        year: "2-digit",
      }),
      energy: Number(item.monthly_energy_kwh || 0),
    }));
  }, [dailyData, monthlyData, chartPeriod]);

  const visibleData = chartData.slice(-12);

  if (visibleData.length === 0) {
    return <p className="chart-note">No energy data available.</p>;
  }

  const maxEnergy = Math.max(
    ...visibleData.map((item) => item.energy),
    1
  );

  const points = visibleData.map((item, index) => {
    const x =
      visibleData.length === 1
        ? 250
        : 12 + (index * 476) / (visibleData.length - 1);

    const y = 150 - (item.energy / maxEnergy) * 110;

    return { ...item, x, y };
  });

  const linePoints = points.map((point) => `${point.x},${point.y}`).join(" ");
  const areaPoints = `12,150 ${linePoints} 488,150`;

  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        <span className="legend-dot" />
        Energy consumption
        <span className="chart-note">Real dataset</span>
      </div>

      <svg
        className="trend-chart"
        viewBox="0 0 500 180"
        role="img"
        aria-label={`${chartPeriod} energy consumption trend`}
      >
        {[35, 70, 105, 140].map((y) => (
          <line
            key={y}
            x1="10"
            y1={y}
            x2="490"
            y2={y}
            className="grid-line"
          />
        ))}

        <polygon points={areaPoints} className="chart-area" />
        <polyline points={linePoints} className="chart-line" />

        {points.map((point, index) => (
          <circle
            key={`${point.label}-${index}`}
            cx={point.x}
            cy={point.y}
            r="3.5"
            className="chart-point"
          >
            <title>
              {point.label}: {formatNumber(point.energy)} kWh
            </title>
          </circle>
        ))}
      </svg>

      <div className="chart-months">
        {points.map((point, index) => (
          <span key={`${point.label}-${index}`}>
            {point.displayLabel}
          </span>
        ))}
      </div>
    </div>
  );
}

function TariffCard({ tariffs }) {
  const standard = tariffs.find((item) => item.tariff_type === "Std");
  const tou = tariffs.find((item) => item.tariff_type === "ToU");

  const standardShare = Number(standard?.energy_share_percent || 0);
  const touShare = Number(tou?.energy_share_percent || 0);

  return (
    <section className="panel" id="tariffs">
      <div className="panel-heading">
        <div>
          <h3>Tariff distribution</h3>
          <p>Share of recorded energy consumption</p>
        </div>
        <ChevronDown size={18} />
      </div>

      <div className="tariff-row">
        <div className="tariff-label">
          <span className="tariff-dot standard" />
          <span>Standard tariff</span>
          <strong>{standardShare.toFixed(2)}%</strong>
        </div>

        <div className="progress-track">
          <div
            className="progress-fill standard-fill"
            style={{ width: `${standardShare}%` }}
          />
        </div>
      </div>

      <div className="tariff-row">
        <div className="tariff-label">
          <span className="tariff-dot tou" />
          <span>Time-of-use tariff</span>
          <strong>{touShare.toFixed(2)}%</strong>
        </div>

        <div className="progress-track">
          <div
            className="progress-fill tou-fill"
            style={{ width: `${touShare}%` }}
          />
        </div>
      </div>

      <p className="panel-footnote">
        Shares reflect the processed dataset, not a causal comparison of
        tariff effects.
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

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        const data = await loadEnergyData();

        if (!cancelled) {
          setEnergyData(data);
          setDataError("");
        }
      } catch (error) {
        if (!cancelled) {
          setDataError(error.message || "Unable to load energy data.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredDaily = useMemo(() => {
    const daily = energyData.daily;

    if (dateRange === "Full dataset" || daily.length === 0) {
      return daily;
    }

    const latestDate = new Date(`${daily[daily.length - 1].date}T12:00:00`);
    const days = dateRange === "Last 30 days" ? 30 : 90;

    if (dateRange === "Last 12 months") {
      const cutoff = new Date(latestDate);
      cutoff.setFullYear(cutoff.getFullYear() - 1);

      return daily.filter(
        (item) => new Date(`${item.date}T12:00:00`) >= cutoff
      );
    }

    const cutoff = new Date(latestDate);
    cutoff.setDate(cutoff.getDate() - days + 1);

    return daily.filter(
      (item) => new Date(`${item.date}T12:00:00`) >= cutoff
    );
  }, [energyData.daily, dateRange]);

  const filteredMonthly = useMemo(() => {
    if (dateRange === "Full dataset") {
      return energyData.monthly;
    }

    const dailyDates = filteredDaily;

    if (dailyDates.length === 0) {
      return [];
    }

    const firstMonth = dailyDates[0].date.slice(0, 7);
    const lastMonth = dailyDates[dailyDates.length - 1].date.slice(0, 7);

    return energyData.monthly.filter((item) => {
      const month = item.month.slice(0, 7);
      return month >= firstMonth && month <= lastMonth;
    });
  }, [energyData.monthly, filteredDaily, dateRange]);

  const totalEnergy = useMemo(
    () =>
      energyData.daily.reduce(
        (sum, item) => sum + Number(item.total_energy_kwh || 0),
        0
      ),
    [energyData.daily]
  );

  const averageDailyEnergy =
    energyData.daily.length > 0 ? totalEnergy / energyData.daily.length : 0;

  const averageHouseholds =
    energyData.daily.length > 0
      ? energyData.daily.reduce(
          (sum, item) => sum + Number(item.households || 0),
          0
        ) / energyData.daily.length
      : 0;

  const totalReadings = energyData.daily.reduce(
    (sum, item) => sum + Number(item.total_readings || 0),
    0
  );

  const highestDay = energyData.daily.reduce(
    (highest, item) =>
      !highest ||
      Number(item.total_energy_kwh) > Number(highest.total_energy_kwh)
        ? item
        : highest,
    null
  );

  const lowestDay = energyData.daily.reduce(
    (lowest, item) =>
      !lowest ||
      Number(item.total_energy_kwh) < Number(lowest.total_energy_kwh)
        ? item
        : lowest,
    null
  );

  const metrics = [
    {
      title: "Total energy",
      value: formatCompact(totalEnergy),
      unit: "kWh",
      change: "Dataset total",
      icon: Zap,
    },
    {
      title: "Average daily energy",
      value: formatCompact(averageDailyEnergy),
      unit: "kWh",
      change: `Across ${energyData.daily.length} dates`,
      icon: Activity,
    },
    {
      title: "Households per day",
      value: formatNumber(averageHouseholds, 0),
      unit: "average",
      change: "Represented households",
      icon: House,
    },
    {
      title: "Raw readings",
      value: formatCompact(totalReadings),
      unit: "records",
      change: "Half-hour measurements",
      icon: BatteryCharging,
    },
  ];

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> Overview
          </div>

          <div className="topbar-right">
            <span className="status-dot" />
            {loading ? "Loading data" : dataError ? "Data unavailable" : "Live dataset"}
            <div className="avatar">GP</div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <p className="eyebrow">ENERGY ANALYTICS PLATFORM</p>
            <h1>Energy overview</h1>
            <p className="page-description">
              Understand consumption patterns across the available household
              energy data.
            </p>
          </div>

          <div className="date-filter">
            <CalendarDays size={17} />
            <select
              className="dashboard-select"
              value={dateRange}
              onChange={(event) => setDateRange(event.target.value)}
              aria-label="Filter dashboard date range"
            >
              <option>Full dataset</option>
              <option>Last 30 days</option>
              <option>Last 90 days</option>
              <option>Last 12 months</option>
            </select>
            <ChevronDown size={16} />
          </div>
        </section>

        {dataError && (
          <div className="data-error" role="alert">
            <strong>Could not load energy data.</strong>
            <p>{dataError}</p>
            Check that all three CSV files are inside
            <code> public/data/</code> and that the development server is running.
          </div>
        )}

        {loading ? (
          <div className="loading-message">Loading energy analytics...</div>
        ) : !dataError ? (
          <>
            <section className="metrics-grid">
              {metrics.map((metric) => (
                <MetricCard key={metric.title} metric={metric} />
              ))}
            </section>

            <section className="content-grid" id="consumption">
              <div className="panel trend-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Consumption trends</h3>
                    <p>
                      {chartPeriod === "Monthly"
                        ? "Monthly energy overview"
                        : "Daily energy overview"}
                    </p>
                  </div>

                  <div className="period-filter">
                    <select
                      className="dashboard-select"
                      value={chartPeriod}
                      onChange={(event) => setChartPeriod(event.target.value)}
                      aria-label="Select chart period"
                    >
                      <option>Monthly</option>
                      <option>Daily</option>
                    </select>
                    <ChevronDown size={15} />
                  </div>
                </div>

                <TrendChart
                  dailyData={filteredDaily}
                  monthlyData={filteredMonthly}
                  chartPeriod={chartPeriod}
                />
              </div>

              <TariffCard tariffs={energyData.tariffs} />
            </section>

            <section className="bottom-grid">
              <div className="insight-panel">
                <div className="insight-icon">
                  <ArrowUpRight size={21} />
                </div>
                <div>
                  <span className="insight-label">
                    HIGHEST RECORDED DAILY ENERGY
                  </span>
                  <h3>
                    {formatNumber(highestDay?.total_energy_kwh)} kWh
                  </h3>
                  <p>
                    {highestDay
                      ? `${formatDate(highestDay.date)} · Dataset-wide daily total`
                      : "No daily data available"}
                  </p>
                </div>
              </div>

              <div className="insight-panel">
                <div className="insight-icon muted">
                  <ArrowDownRight size={21} />
                </div>
                <div>
                  <span className="insight-label">
                    LOWEST RECORDED DAILY ENERGY
                  </span>
                  <h3>
                    {formatNumber(lowestDay?.total_energy_kwh)} kWh
                  </h3>
                  <p>
                    {lowestDay
                      ? `${formatDate(lowestDay.date)} · Check coverage for this date`
                      : "No daily data available"}
                  </p>
                </div>
              </div>
            </section>

            <section id="households" className="dashboard-info-section">
              <h3>Household coverage</h3>
              <p>
                Average daily households represented in the processed data:{" "}
                <strong>{formatNumber(averageHouseholds, 0)}</strong>.
              </p>
            </section>

            <section id="forecast" className="dashboard-info-section">
              <h3>Forecasting</h3>
              <p>
                Forecasting is not yet connected. This section can later display
                predicted energy consumption from your forecasting model.
              </p>
            </section>

            <section id="settings" className="dashboard-info-section">
              <h3>Settings</h3>
              <p>
                Dashboard date filter: <strong>{dateRange}</strong>. Chart
                frequency: <strong>{chartPeriod}</strong>.
              </p>
            </section>
          </>
        ) : null}

        <footer className="footer">
          <span>
            <Zap size={14} /> GRID_PULSE
          </span>
          <span>Data engineering · Energy intelligence</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
