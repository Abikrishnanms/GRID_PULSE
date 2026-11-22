
import { useEffect, useMemo, useState } from "react";
import {
  getAppliances,
  saveAppliances,
  getHomeProfile,
  saveHomeProfile,
} from "../services/householdStorage";
import {
  calculateHouseholdEnergy,
  calculateElectricityBill,
  calculateApplianceBreakdown,
} from "../services/energyCalculator";

const initialAppliance = {
  name: "",
  wattage: "",
  quantity: 1,
  hoursPerDay: 1,
  daysPerWeek: 7,
};

export default function ApplianceManager() {
  const [appliances, setAppliances] = useState(getAppliances);
  const [home, setHome] = useState(getHomeProfile);
  useEffect(() => {
  function handleHomeUpdate(event) {
    setHome(event.detail);
  }

  window.addEventListener(
    "gridpulse-home-updated",
    handleHomeUpdate
  );

  return () => {
    window.removeEventListener(
      "gridpulse-home-updated",
      handleHomeUpdate
    );
  };
}, []);
  const [form, setForm] = useState(initialAppliance);
  const [message, setMessage] = useState("");

  const totals = useMemo(
    () => calculateHouseholdEnergy(appliances),
    [appliances]
  );

  const breakdown = useMemo(
    () => calculateApplianceBreakdown(appliances),
    [appliances]
  );

  const bill = calculateElectricityBill(
    totals.monthly,
    home.electricityRate
  );

  function addAppliance(event) {
    event.preventDefault();

    const name = form.name.trim();
    const wattage = Number(form.wattage);
    const quantity = Number(form.quantity);
    const hoursPerDay = Number(form.hoursPerDay);
    const daysPerWeek = Number(form.daysPerWeek);

    if (
      !name ||
      !Number.isFinite(wattage) || wattage <= 0 ||
      !Number.isInteger(quantity) || quantity < 1 ||
      !Number.isFinite(hoursPerDay) ||
      hoursPerDay < 0 || hoursPerDay > 24 ||
      !Number.isInteger(daysPerWeek) ||
      daysPerWeek < 1 || daysPerWeek > 7
    ) {
      setMessage("Please enter valid appliance details.");
      return;
    }

    const updated = [
      ...appliances,
      {
        id: crypto.randomUUID(),
        name,
        wattage,
        quantity,
        hoursPerDay,
        daysPerWeek,
      },
    ];

    if (!saveAppliances(updated)) {
      setMessage("Could not save appliances in this browser.");
      return;
    }

    setAppliances(updated);
    setForm({ ...initialAppliance });
    setMessage("Appliance added successfully.");
    window.dispatchEvent(
      new CustomEvent("gridpulse-appliances-updated", {
        detail: updated,
      })
    );
  }

  function removeAppliance(id) {
    const updated = appliances.filter((item) => item.id !== id);

    if (!saveAppliances(updated)) {
      setMessage("Could not save the change.");
      return;
    }

    setAppliances(updated);
    setMessage("Appliance removed.");
    window.dispatchEvent(
      new CustomEvent("gridpulse-appliances-updated", {
        detail: updated,
      })
    );
  }

  function updateRate(value) {
    const rate = Number(value);

    if (!Number.isFinite(rate) || rate < 0) return;

    const updated = { ...home, electricityRate: rate };

    if (saveHomeProfile(updated)) {
      setHome(updated);
      window.dispatchEvent(
        new CustomEvent("gridpulse-home-updated", {
          detail: updated,
        })
      );
      setMessage("");
    } else {
      setMessage("Could not save the electricity rate.");
    }
  }

  return (
    <section className="panel appliance-section" id="appliances">
      <div className="panel-heading">
        <div>
          <h3>My Appliances & Energy Estimator</h3>
          <p>
            Add your home appliances to estimate electricity usage
            and monthly cost.
          </p>
        </div>
      </div>

      <div className="appliance-summary">
        <div>
          <span>Estimated daily usage</span>
          <strong>{totals.daily.toFixed(2)} kWh</strong>
        </div>
        <div>
          <span>Estimated weekly usage</span>
          <strong>{totals.weekly.toFixed(2)} kWh</strong>
        </div>
        <div>
          <span>Estimated monthly usage</span>
          <strong>{totals.monthly.toFixed(2)} kWh</strong>
        </div>
        <div>
          <span>Estimated monthly cost</span>
          <strong>₹{bill.toLocaleString("en-IN", {
            maximumFractionDigits: 2,
          })}</strong>
        </div>
      </div>

      <div className="appliance-rate">
        <label htmlFor="electricity-rate">
          Electricity rate (₹ per kWh)
        </label>
        <input
          id="electricity-rate"
          type="number"
          min="0"
          step="0.01"
          value={home.electricityRate}
          onChange={(event) => updateRate(event.target.value)}
        />
      </div>

      <form className="appliance-form" onSubmit={addAppliance}>
        <label>
          Appliance name
          <input
            required
            placeholder="e.g. Air Conditioner"
            value={form.name}
            onChange={(event) =>
              setForm({ ...form, name: event.target.value })
            }
          />
        </label>

        <label>
          Power (watts)
          <input
            required
            type="number"
            min="0.01"
            step="any"
            value={form.wattage}
            onChange={(event) =>
              setForm({ ...form, wattage: event.target.value })
            }
          />
        </label>

        <label>
          Quantity
          <input
            required
            type="number"
            min="1"
            step="1"
            value={form.quantity}
            onChange={(event) =>
              setForm({ ...form, quantity: event.target.value })
            }
          />
        </label>

        <label>
          Hours per day
          <input
            required
            type="number"
            min="0"
            max="24"
            step="0.5"
            value={form.hoursPerDay}
            onChange={(event) =>
              setForm({ ...form, hoursPerDay: event.target.value })
            }
          />
        </label>

        <label>
          Days per week
          <input
            required
            type="number"
            min="1"
            max="7"
            step="1"
            value={form.daysPerWeek}
            onChange={(event) =>
              setForm({ ...form, daysPerWeek: event.target.value })
            }
          />
        </label>

        <button className="appliance-add-button" type="submit">
          + Add Appliance
        </button>
      </form>

      {message && <p className="appliance-message" role="status">{message}</p>}

      <div className="appliance-list">
        <h4>Registered appliances ({appliances.length})</h4>

        {appliances.length === 0 ? (
          <p>No appliances added yet. Start by adding one above.</p>
        ) : (
          breakdown.map((item) => (
            <div className="appliance-item" key={item.id}>
              <div>
                <strong>{item.name}</strong>
                <p>
                  {item.quantity} × {item.wattage} W ·
                  {" "}{item.hoursPerDay} h/day ·
                  {" "}{item.daysPerWeek} days/week
                </p>
                <small>
                  {item.monthly.toFixed(2)} kWh/month ·
                  {" "}{item.percentage.toFixed(1)}% of estimated usage
                </small>
              </div>
              <button
                className="appliance-remove"
                onClick={() => removeAppliance(item.id)}
                type="button"
              >
                Remove
              </button>
            </div>
          ))
        )}
      </div>

      <p className="panel-footnote">
        Estimates use appliance wattage, usage hours, and a 30-day
        month. Costs use your custom ₹/kWh rate and exclude fixed
        charges, taxes, and other billing adjustments.
      </p>
    </section>
  );
}
