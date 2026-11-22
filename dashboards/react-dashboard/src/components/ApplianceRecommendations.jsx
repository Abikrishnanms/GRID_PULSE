import { useState, useEffect, useCallback } from "react";
import {
  Sparkles,
  RefreshCw,
  AlertTriangle,
  Info,
  ShieldAlert,
} from "lucide-react";

import { getAppliances, getHomeProfile } from "../services/householdStorage";
import { fetchRecommendations } from "../services/recommendationApi";

export default function ApplianceRecommendations() {
  const [appliances, setAppliances] = useState(() => {
    const initial = getAppliances();
    return Array.isArray(initial) ? initial : [];
  });
  const [loading, setLoading] = useState(() => {
    const initial = getAppliances();
    return Array.isArray(initial) && initial.length > 0;
  });
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = useCallback(() => {
    const current = getAppliances();
    const list = Array.isArray(current) ? current : [];
    setAppliances(list);

    if (list.length === 0) {
      setReport(null);
      setError(null);
      setLoading(false);
    } else {
      setLoading(true);
      setError(null);
    }
    setRefreshKey((prev) => prev + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const currentAppliances = getAppliances();
    const currentProfile = getHomeProfile();
    const rate = currentProfile?.electricityRate ?? null;
    const applianceList = Array.isArray(currentAppliances) ? currentAppliances : [];

    if (applianceList.length === 0) {
      return () => {
        cancelled = true;
      };
    }

    fetchRecommendations(applianceList, rate)
      .then((data) => {
        if (!cancelled) {
          setAppliances(applianceList);
          setReport(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load appliance recommendations.");
          setReport(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    function handleHomeUpdate() {
      const updated = getAppliances();
      const list = Array.isArray(updated) ? updated : [];
      setAppliances(list);
      if (list.length > 0) {
        setLoading(true);
      } else {
        setReport(null);
        setError(null);
        setLoading(false);
      }
      setRefreshKey((prev) => prev + 1);
    }

    function handleAppliancesUpdate(event) {
      const list = Array.isArray(event?.detail) ? event.detail : getAppliances();
      const validList = Array.isArray(list) ? list : [];
      setAppliances(validList);
      if (validList.length > 0) {
        setLoading(true);
      } else {
        setReport(null);
        setError(null);
        setLoading(false);
      }
      setRefreshKey((prev) => prev + 1);
    }

    window.addEventListener("gridpulse-home-updated", handleHomeUpdate);
    window.addEventListener("gridpulse-appliances-updated", handleAppliancesUpdate);

    return () => {
      cancelled = true;
      window.removeEventListener("gridpulse-home-updated", handleHomeUpdate);
      window.removeEventListener("gridpulse-appliances-updated", handleAppliancesUpdate);
    };
  }, [refreshKey]);

  const summary = report?.summary;
  const ranked = report?.ranked_appliances || [];
  const actionables = report?.actionable_recommendations || [];
  const suppressed = report?.suppressed_or_informational || [];

  return (
    <section className="panel section-panel" id="recommendations">
      <div className="panel-heading">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Sparkles size={20} style={{ color: "var(--accent)" }} />
            <h3>Personalised Appliance Recommendations</h3>
          </div>
          <p>
            Data-driven energy rankings and safe, hypothetical usage-reduction scenarios.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={handleRefresh}
          disabled={loading}
          type="button"
          style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
          aria-label="Refresh recommendations"
        >
          <RefreshCw size={15} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
          Refresh Recommendations
        </button>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="loading-message">
          Analyzing appliance consumption and generating recommendations…
        </div>
      )}

      {/* ERROR / BACKEND OFFLINE STATE */}
      {!loading && error && (
        <div className="data-error" role="alert" style={{ marginTop: "16px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
            <AlertTriangle size={20} style={{ color: "var(--danger)", flexShrink: 0 }} />
            <div>
              <strong>Unable to generate recommendations</strong>
              <p style={{ margin: "4px 0 8px 0" }}>{error}</p>
              <button
                className="secondary-button"
                onClick={handleRefresh}
                type="button"
                style={{ marginTop: "6px" }}
              >
                Retry Request
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && !error && appliances.length === 0 && (
        <div className="empty-state" style={{ marginTop: "16px" }}>
          <p>
            No appliances added yet. Add appliances in My Appliances &amp; Energy Estimator
            to receive personalised recommendations.
          </p>
        </div>
      )}

      {/* REPORT CONTENT */}
      {!loading && !error && report && appliances.length > 0 && (
        <>
          {/* A. SUMMARY CARDS */}
          {summary && (
            <div className="appliance-summary" style={{ marginTop: "16px" }}>
              <div>
                <span>Monthly consumption</span>
                <strong>{summary.total_monthly_kwh?.toFixed(2)} kWh</strong>
              </div>
              <div>
                <span>Estimated monthly cost</span>
                <strong>
                  {summary.total_monthly_cost !== null
                    ? `₹${summary.total_monthly_cost.toLocaleString("en-IN", {
                        maximumFractionDigits: 2,
                      })}`
                    : "Unavailable"}
                </strong>
              </div>
              <div>
                <span>Potential monthly savings</span>
                <strong style={{ color: "var(--accent)" }}>
                  {summary.total_hypothetical_savings_kwh?.toFixed(2)} kWh
                </strong>
              </div>
              <div>
                <span>Potential cost savings</span>
                <strong style={{ color: "var(--accent)" }}>
                  {summary.total_hypothetical_cost_savings !== null
                    ? `₹${summary.total_hypothetical_cost_savings.toLocaleString("en-IN", {
                        maximumFractionDigits: 2,
                      })}`
                    : "Unavailable"}
                </strong>
              </div>
              <div>
                <span>Potential reduction</span>
                <strong style={{ color: "var(--accent)" }}>
                  {summary.potential_reduction_percent?.toFixed(1)}%
                </strong>
              </div>
            </div>
          )}

          {/* B. APPLIANCE CONSUMPTION RANKING */}
          <div style={{ marginTop: "24px" }}>
            <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "var(--text)" }}>
              Appliance Consumption Ranking ({ranked.length})
            </h4>
            <div className="appliance-list">
              {ranked.map((item) => (
                <div
                  className="appliance-item"
                  key={item.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <span
                      style={{
                        display: "inline-grid",
                        placeItems: "center",
                        width: "28px",
                        height: "28px",
                        borderRadius: "8px",
                        background:
                          item.rank === 1
                            ? "rgba(69, 214, 173, 0.2)"
                            : "rgba(255, 255, 255, 0.06)",
                        color: item.rank === 1 ? "var(--accent)" : "var(--muted)",
                        fontWeight: "700",
                        fontSize: "12px",
                      }}
                    >
                      #{item.rank}
                    </span>
                    <div>
                      <strong>{item.name}</strong>
                      <p style={{ margin: "2px 0 0 0", color: "var(--muted)", fontSize: "12px" }}>
                        {item.monthly_kwh?.toFixed(2)} kWh/month ·{" "}
                        {item.percentage_of_total?.toFixed(1)}% of total
                      </p>
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <strong style={{ fontSize: "14px" }}>
                      {item.monthly_cost !== null
                        ? `₹${item.monthly_cost.toLocaleString("en-IN", {
                            maximumFractionDigits: 2,
                          })}`
                        : "Rate unavailable"}
                    </strong>
                    <div style={{ fontSize: "11px", color: "var(--muted)" }}>
                      {item.daily_kwh?.toFixed(2)} kWh/day
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* C. ACTIONABLE RECOMMENDATIONS */}
          <div style={{ marginTop: "28px" }}>
            <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "var(--text)" }}>
              Actionable Usage-Reduction Suggestions ({actionables.length})
            </h4>

            {actionables.length === 0 ? (
              <p style={{ color: "var(--muted)", fontSize: "13px" }}>
                No runtime reductions recommended at this time. All registered loads are
                either continuous food-preservation appliances or already below the low-impact threshold.
              </p>
            ) : (
              <div style={{ display: "grid", gap: "12px" }}>
                {actionables.map((rec) => (
                  <div
                    key={rec.appliance_id}
                    style={{
                      background: "rgba(17, 31, 35, 0.8)",
                      border: "1px solid var(--border)",
                      borderLeft: "4px solid var(--accent)",
                      borderRadius: "10px",
                      padding: "16px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        flexWrap: "wrap",
                        gap: "8px",
                      }}
                    >
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <strong style={{ fontSize: "14px", color: "var(--text)" }}>
                            {rec.appliance_name}
                          </strong>
                          <span
                            style={{
                              fontSize: "11px",
                              padding: "2px 8px",
                              borderRadius: "6px",
                              background: "var(--accent-soft)",
                              color: "var(--accent)",
                              fontWeight: "600",
                            }}
                          >
                            {rec.action_title}
                          </span>
                        </div>
                        <p style={{ margin: "6px 0 0 0", fontSize: "12px", color: "var(--muted)" }}>
                          <strong>Current:</strong> {rec.current_usage} &rarr;{" "}
                          <strong>Proposed:</strong> {rec.proposed_usage}
                        </p>
                      </div>

                      <div style={{ textAlign: "right" }}>
                        <span
                          style={{
                            color: "var(--accent)",
                            fontWeight: "700",
                            fontSize: "14px",
                            display: "block",
                          }}
                        >
                          -{rec.hypothetical_savings_kwh?.toFixed(2)} kWh/mo
                        </span>
                        {rec.hypothetical_cost_savings !== null && (
                          <span style={{ fontSize: "12px", color: "var(--muted)" }}>
                            Save ~₹{rec.hypothetical_cost_savings?.toFixed(2)}/mo
                          </span>
                        )}
                      </div>
                    </div>

                    <p
                      style={{
                        margin: "10px 0 0 0",
                        fontSize: "12px",
                        lineHeight: "1.5",
                        color: "var(--text)",
                      }}
                    >
                      {rec.action_detail}
                    </p>
                  </div>
                ))}
              </div>
            )}
            <small
              style={{
                display: "block",
                marginTop: "8px",
                color: "var(--muted)",
                fontSize: "11px",
              }}
            >
              * Suggested scenarios are hypothetical estimates based on average wattage and do not alter appliance configurations automatically.
            </small>
          </div>

          {/* D. SUPPRESSED & SAFETY INFORMATIONAL ITEMS */}
          {suppressed.length > 0 && (
            <div style={{ marginTop: "28px" }}>
              <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "var(--text)" }}>
                Safety &amp; Threshold Suppressions ({suppressed.length})
              </h4>
              <div style={{ display: "grid", gap: "10px" }}>
                {suppressed.map((item) => (
                  <div
                    key={item.appliance_id}
                    style={{
                      background: "rgba(14, 26, 29, 0.7)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                      padding: "12px 14px",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "10px",
                    }}
                  >
                    {item.status === "No Runtime Reduction" ? (
                      <ShieldAlert
                        size={18}
                        style={{ color: "var(--blue)", flexShrink: 0, marginTop: "2px" }}
                      />
                    ) : (
                      <Info
                        size={18}
                        style={{ color: "var(--muted)", flexShrink: 0, marginTop: "2px" }}
                      />
                    )}
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <strong style={{ fontSize: "13px" }}>{item.appliance_name}</strong>
                        <span
                          style={{
                            fontSize: "10px",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background:
                              item.status === "No Runtime Reduction"
                                ? "rgba(126, 171, 255, 0.12)"
                                : "rgba(255, 255, 255, 0.06)",
                            color:
                              item.status === "No Runtime Reduction"
                                ? "var(--blue)"
                                : "var(--muted)",
                            fontWeight: "600",
                          }}
                        >
                          {item.status}
                        </span>
                      </div>
                      <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "var(--muted)" }}>
                        {item.reason}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="panel-footnote" style={{ marginTop: "20px" }}>
            Recommendations are calculated using a 30-day billing month and your saved electricity rate.
            Monetary savings are omitted if no rate is registered.
          </p>
        </>
      )}
    </section>
  );
}
