import { useState, useEffect, useMemo } from "react";
import {
  Sliders,
  Play,
  RotateCcw,
  AlertTriangle,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { getAppliances, getHomeProfile } from "../services/householdStorage";
import { fetchSimulation } from "../services/recommendationApi";

function createInitialAdjustments(appList) {
  const initialMap = {};
  if (Array.isArray(appList)) {
    appList.forEach((app) => {
      initialMap[app.id] = {
        selected: false,
        proposed_hours_per_day: app.hoursPerDay ?? 1,
        proposed_days_per_week: app.daysPerWeek ?? 7,
      };
    });
  }
  return initialMap;
}

export default function EnergySavingsSimulator() {
  const [appliances, setAppliances] = useState(() => {
    const list = getAppliances();
    return Array.isArray(list) ? list : [];
  });
  const [electricityRate, setElectricityRate] = useState(() => {
    const profile = getHomeProfile();
    return profile?.electricityRate ?? null;
  });

  // adjustments keyed by appliance_id: { selected, proposed_hours_per_day, proposed_days_per_week }
  const [adjustments, setAdjustments] = useState(() =>
    createInitialAdjustments(getAppliances())
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);

  useEffect(() => {
    function handleHomeUpdate(event) {
      const profile = event?.detail || getHomeProfile();
      setElectricityRate(profile?.electricityRate ?? null);
    }

    function handleAppliancesUpdate(event) {
      const list = Array.isArray(event?.detail) ? event.detail : getAppliances();
      const validList = Array.isArray(list) ? list : [];
      setAppliances(validList);
      setAdjustments(createInitialAdjustments(validList));
      setSimulationResult(null);
    }

    window.addEventListener("gridpulse-home-updated", handleHomeUpdate);
    window.addEventListener("gridpulse-appliances-updated", handleAppliancesUpdate);
    return () => {
      window.removeEventListener("gridpulse-home-updated", handleHomeUpdate);
      window.removeEventListener("gridpulse-appliances-updated", handleAppliancesUpdate);
    };
  }, []);

  const selectedCount = useMemo(() => {
    return Object.values(adjustments).filter((item) => item.selected).length;
  }, [adjustments]);

  function toggleApplianceSelection(id) {
    setAdjustments((prev) => {
      const existing = prev[id] || {};
      return {
        ...prev,
        [id]: {
          ...existing,
          selected: !existing.selected,
        },
      };
    });
  }

  function handleHoursChange(id, value) {
    const numeric = parseFloat(value);
    const clamped = isNaN(numeric) ? 0 : Math.max(0, Math.min(24, numeric));
    setAdjustments((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        proposed_hours_per_day: clamped,
      },
    }));
  }

  function handleDaysChange(id, value) {
    const numeric = parseInt(value, 10);
    const clamped = isNaN(numeric) ? 1 : Math.max(1, Math.min(7, numeric));
    setAdjustments((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        proposed_days_per_week: clamped,
      },
    }));
  }

  function resetSingleAppliance(app) {
    setAdjustments((prev) => ({
      ...prev,
      [app.id]: {
        selected: false,
        proposed_hours_per_day: app.hoursPerDay ?? 1,
        proposed_days_per_week: app.daysPerWeek ?? 7,
      },
    }));
  }

  function resetAllAdjustments() {
    const latest = getAppliances();
    const list = Array.isArray(latest) ? latest : [];
    setAppliances(list);
    setAdjustments(createInitialAdjustments(list));
    setSimulationResult(null);
    setError(null);
  }

  async function runSimulation() {
    // Read the latest appliances from storage to ensure consistency
    const latestAppliances = getAppliances();
    const list = Array.isArray(latestAppliances) ? latestAppliances : [];
    setAppliances(list);

    const activeAdjustments = Object.entries(adjustments)
      .filter(([, adj]) => adj.selected)
      .map(([id, adj]) => ({
        appliance_id: id,
        proposed_hours_per_day: Number(adj.proposed_hours_per_day),
        proposed_days_per_week: Number(adj.proposed_days_per_week),
      }));

    if (activeAdjustments.length === 0) {
      setError("Please select at least one appliance to adjust before running a simulation.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetchSimulation(list, activeAdjustments, electricityRate);
      setSimulationResult(result);
    } catch (err) {
      setError(err.message || "Failed to execute simulation.");
      setSimulationResult(null);
    } finally {
      setLoading(false);
    }
  }

  const summary = simulationResult?.summary;
  const breakdown = simulationResult?.appliance_breakdown || [];
  const safetyWarnings = simulationResult?.safety_warnings || [];
  const adjustmentErrors = simulationResult?.adjustment_errors || [];

  return (
    <section className="panel section-panel" id="simulator">
      <div className="panel-heading">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Sliders size={20} style={{ color: "var(--accent)" }} />
            <h3>Personalised Energy Savings Simulator</h3>
          </div>
          <p>
            Simulate &ldquo;what-if&rdquo; runtime adjustments to explore prospective energy and cost savings.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            className="secondary-button"
            onClick={resetAllAdjustments}
            disabled={loading || selectedCount === 0}
            type="button"
            style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
            aria-label="Reset all adjustments"
          >
            <RotateCcw size={14} />
            Reset All
          </button>
        </div>
      </div>

      {/* EMPTY APPLIANCES STATE */}
      {appliances.length === 0 && (
        <div className="empty-state" style={{ marginTop: "16px" }}>
          <p>
            No appliances registered yet. Add appliances in My Appliances &amp; Energy Estimator
            to use the Energy Savings Simulator.
          </p>
        </div>
      )}

      {/* APPLIANCE ADJUSTMENT CONTROLS */}
      {appliances.length > 0 && (
        <div style={{ marginTop: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h4 style={{ margin: 0, fontSize: "14px", color: "var(--text)" }}>
              Select &amp; Adjust Appliance Scenarios ({selectedCount} of {appliances.length} selected)
            </h4>
            <span style={{ fontSize: "12px", color: "var(--muted)" }}>
              Baseline Rate: {electricityRate !== null ? `₹${Number(electricityRate).toFixed(2)}/kWh` : "Unavailable"}
            </span>
          </div>

          <div className="appliance-list">
            {appliances.map((app) => {
              const adj = adjustments[app.id] || {
                selected: false,
                proposed_hours_per_day: app.hoursPerDay,
                proposed_days_per_week: app.daysPerWeek,
              };
              const isContinuous = Number(app.hoursPerDay) >= 20;

              return (
                <div
                  key={app.id}
                  className="appliance-item"
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                    background: adj.selected ? "rgba(69, 214, 173, 0.04)" : "rgba(17, 31, 35, 0.6)",
                    border: adj.selected ? "1px solid var(--accent)" : "1px solid var(--border)",
                    transition: "all 150ms ease",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      width: "100%",
                      flexWrap: "wrap",
                      gap: "8px",
                    }}
                  >
                    <label
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        cursor: "pointer",
                        userSelect: "none",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={adj.selected}
                        onChange={() => toggleApplianceSelection(app.id)}
                        style={{
                          width: "16px",
                          height: "16px",
                          accentColor: "var(--accent)",
                          cursor: "pointer",
                        }}
                      />
                      <div>
                        <strong style={{ fontSize: "14px", color: "var(--text)" }}>
                          {app.name}
                        </strong>
                        <span style={{ marginLeft: "8px", fontSize: "12px", color: "var(--muted)" }}>
                          ({app.quantity} × {app.wattage}W)
                        </span>
                        <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "2px" }}>
                          Current: {app.hoursPerDay} hrs/day · {app.daysPerWeek} days/week
                        </div>
                      </div>
                    </label>

                    {adj.selected && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => resetSingleAppliance(app)}
                        style={{ fontSize: "11px", padding: "4px 8px" }}
                        title="Reset this appliance to baseline usage"
                      >
                        Reset
                      </button>
                    )}
                  </div>

                  {/* SLIDERS / NUMERIC INPUTS WHEN SELECTED */}
                  {adj.selected && (
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                        gap: "14px",
                        padding: "12px",
                        background: "rgba(11, 20, 23, 0.6)",
                        borderRadius: "8px",
                        border: "1px solid rgba(255, 255, 255, 0.05)",
                      }}
                    >
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                          <span style={{ color: "var(--text)" }}>Proposed Hours / Day</span>
                          <strong style={{ color: "var(--accent)" }}>{adj.proposed_hours_per_day} hrs</strong>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="24"
                          step="0.5"
                          value={adj.proposed_hours_per_day}
                          onChange={(e) => handleHoursChange(app.id, e.target.value)}
                          style={{ width: "100%", accentColor: "var(--accent)", cursor: "pointer" }}
                        />
                      </div>

                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                          <span style={{ color: "var(--text)" }}>Proposed Days / Week</span>
                          <strong style={{ color: "var(--accent)" }}>{adj.proposed_days_per_week} days</strong>
                        </div>
                        <input
                          type="range"
                          min="1"
                          max="7"
                          step="1"
                          value={adj.proposed_days_per_week}
                          onChange={(e) => handleDaysChange(app.id, e.target.value)}
                          style={{ width: "100%", accentColor: "var(--accent)", cursor: "pointer" }}
                        />
                      </div>

                      {isContinuous && adj.proposed_hours_per_day < app.hoursPerDay && (
                        <div
                          style={{
                            gridColumn: "1 / -1",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            fontSize: "11px",
                            color: "var(--blue)",
                          }}
                        >
                          <ShieldAlert size={14} style={{ flexShrink: 0 }} />
                          <span>Continuous load: Curtailing food preservation or essential load runtime may cause functional risk.</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              className="appliance-add-button"
              onClick={runSimulation}
              disabled={loading || selectedCount === 0}
              type="button"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 18px",
                opacity: selectedCount === 0 ? 0.5 : 1,
              }}
            >
              <Play size={16} />
              {loading ? "Calculating Simulation…" : `Run Simulation (${selectedCount} Adjusted)`}
            </button>
            {selectedCount === 0 && (
              <span style={{ fontSize: "12px", color: "var(--muted)" }}>
                Check one or more appliances above to customize hours/days.
              </span>
            )}
          </div>
        </div>
      )}

      {/* ERROR MESSAGE */}
      {error && (
        <div className="data-error" role="alert" style={{ marginTop: "16px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
            <AlertTriangle size={18} style={{ color: "var(--danger)", flexShrink: 0 }} />
            <div>
              <strong>Simulation Error</strong>
              <p style={{ margin: "4px 0 0 0", fontSize: "12px" }}>{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* SIMULATION RESULTS */}
      {simulationResult && summary && (
        <div style={{ marginTop: "24px" }}>
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: "18px" }}>
            <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "var(--text)" }}>
              Simulation Outcome Summary
            </h4>

            {/* SUMMARY CARDS */}
            <div className="appliance-summary">
              <div>
                <span>Baseline consumption</span>
                <strong>{summary.baseline_monthly_kwh?.toFixed(2)} kWh</strong>
              </div>
              <div>
                <span>Simulated consumption</span>
                <strong style={{ color: summary.net_monthly_savings_kwh > 0 ? "var(--accent)" : "inherit" }}>
                  {summary.simulated_monthly_kwh?.toFixed(2)} kWh
                </strong>
              </div>
              <div>
                <span>Net monthly impact</span>
                {summary.net_monthly_savings_kwh > 0 ? (
                  <strong style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: "4px" }}>
                    <TrendingDown size={16} /> -{summary.net_monthly_savings_kwh.toFixed(2)} kWh ({summary.percentage_reduction.toFixed(1)}%)
                  </strong>
                ) : summary.net_monthly_savings_kwh < 0 ? (
                  <strong style={{ color: "var(--danger)", display: "flex", alignItems: "center", gap: "4px" }}>
                    <TrendingUp size={16} /> +{Math.abs(summary.net_monthly_savings_kwh).toFixed(2)} kWh (+{Math.abs(summary.percentage_reduction).toFixed(1)}%)
                  </strong>
                ) : (
                  <strong>0.00 kWh (Unchanged)</strong>
                )}
              </div>
              <div>
                <span>Estimated cost savings</span>
                <strong>
                  {summary.net_monthly_cost_savings !== null ? (
                    summary.net_monthly_cost_savings > 0 ? (
                      <span style={{ color: "var(--accent)" }}>₹{summary.net_monthly_cost_savings.toFixed(2)}</span>
                    ) : summary.net_monthly_cost_savings < 0 ? (
                      <span style={{ color: "var(--danger)" }}>+₹{Math.abs(summary.net_monthly_cost_savings).toFixed(2)} (Cost increase)</span>
                    ) : (
                      "₹0.00"
                    )
                  ) : (
                    "Unavailable"
                  )}
                </strong>
              </div>
              <div>
                <span>Simulated monthly bill</span>
                <strong>
                  {summary.simulated_monthly_cost !== null
                    ? `₹${summary.simulated_monthly_cost.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`
                    : "Unavailable"}
                </strong>
              </div>
            </div>

            {/* SAFETY WARNINGS */}
            {safetyWarnings.length > 0 && (
              <div style={{ marginTop: "16px" }}>
                <h5 style={{ margin: "0 0 8px 0", color: "var(--blue)", fontSize: "13px" }}>
                  Operational Safety Warnings ({safetyWarnings.length})
                </h5>
                {safetyWarnings.map((warn, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "rgba(126, 171, 255, 0.08)",
                      border: "1px solid rgba(126, 171, 255, 0.25)",
                      borderRadius: "8px",
                      padding: "10px 14px",
                      marginBottom: "8px",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "10px",
                    }}
                  >
                    <ShieldAlert size={16} style={{ color: "var(--blue)", flexShrink: 0, marginTop: "2px" }} />
                    <span style={{ fontSize: "12px", color: "#d2e3fc" }}>{warn.warning}</span>
                  </div>
                ))}
              </div>
            )}

            {/* ADJUSTMENT ERRORS (IF ANY PARTIAL/ATOMIC REJECTIONS) */}
            {adjustmentErrors.length > 0 && (
              <div style={{ marginTop: "16px" }}>
                <h5 style={{ margin: "0 0 8px 0", color: "var(--danger)", fontSize: "13px" }}>
                  Adjustment Validation Rejections ({adjustmentErrors.length})
                </h5>
                {adjustmentErrors.map((rej, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "rgba(255, 154, 154, 0.08)",
                      border: "1px solid rgba(255, 154, 154, 0.25)",
                      borderRadius: "8px",
                      padding: "10px 14px",
                      marginBottom: "8px",
                      fontSize: "12px",
                      color: "#ffcdd2",
                    }}
                  >
                    Appliance #{rej.appliance_id || idx}: {rej.error}
                  </div>
                ))}
              </div>
            )}

            {/* DETAILED APPLIANCE BREAKDOWN TABLE */}
            <div style={{ marginTop: "20px" }}>
              <h5 style={{ margin: "0 0 10px 0", fontSize: "14px", color: "var(--text)" }}>
                Per-Appliance Simulation Breakdown
              </h5>
              <div className="appliance-list">
                {breakdown.map((item) => {
                  const isModified = item.status === "Modified";

                  return (
                    <div
                      key={item.appliance_id}
                      className="appliance-item"
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        borderLeft: isModified ? "3px solid var(--accent)" : "1px solid var(--border)",
                      }}
                    >
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <strong>{item.name}</strong>
                          <span
                            style={{
                              fontSize: "10px",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: isModified ? "var(--accent-soft)" : "rgba(255, 255, 255, 0.05)",
                              color: isModified ? "var(--accent)" : "var(--muted)",
                              fontWeight: "600",
                            }}
                          >
                            {item.status}
                          </span>
                        </div>
                        <p style={{ margin: "3px 0 0 0", color: "var(--muted)", fontSize: "12px" }}>
                          {item.baseline_usage} &rarr; <strong>{item.simulated_usage}</strong>
                        </p>
                      </div>

                      <div style={{ textAlign: "right" }}>
                        <span style={{ fontSize: "13px", fontWeight: "600" }}>
                          {item.simulated_monthly_kwh?.toFixed(2)} kWh/mo
                        </span>
                        <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "2px" }}>
                          {item.savings_kwh > 0 ? (
                            <span style={{ color: "var(--accent)" }}>-{item.savings_kwh.toFixed(2)} kWh saved</span>
                          ) : item.savings_kwh < 0 ? (
                            <span style={{ color: "var(--danger)" }}>+{Math.abs(item.savings_kwh).toFixed(2)} kWh extra</span>
                          ) : (
                            <span>No change</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FOOTNOTE DISCLAIMER */}
      <p className="panel-footnote" style={{ marginTop: "22px" }}>
        Simulation results are estimates based on the selected usage adjustments. Running a simulation
        does not change your saved appliance settings.
      </p>
    </section>
  );
}
