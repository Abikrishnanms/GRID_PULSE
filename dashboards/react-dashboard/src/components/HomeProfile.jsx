
import { useState } from "react";
import { getHomeProfile, saveHomeProfile } from "../services/householdStorage";
import { House, Save } from "lucide-react";

export default function HomeProfile() {
  const [profile, setProfile] = useState(() => getHomeProfile());
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function updateField(event) {
    const { name, value } = event.target;

    setProfile((previous) => ({
      ...previous,
      [name]: value,
    }));

    setMessage("");
    setError("");
  }

  function handleSubmit(event) {
    event.preventDefault();

    const members = Number(profile.members);
    const rate = Number(profile.electricityRate);
    const area = Number(profile.area || 0);

    if (!profile.homeName.trim()) {
      setError("Please enter a home name.");
      return;
    }

    if (!Number.isInteger(members) || members < 1 || members > 100) {
      setError("Enter a valid number of household members.");
      return;
    }

    if (!Number.isFinite(rate) || rate < 0) {
      setError("Enter a valid electricity rate.");
      return;
    }

    if (!Number.isFinite(area) || area < 0) {
      setError("Enter a valid home area.");
      return;
    }

    const updatedProfile = {
      ...profile,
      homeName: profile.homeName.trim(),
      members,
      electricityRate: rate,
      area,
    };

    const saved = saveHomeProfile(updatedProfile);

    if (!saved) {
      setError("Unable to save your home details.");
      return;
    }

    // Notify other components in the same browser tab.
    window.dispatchEvent(
      new CustomEvent("gridpulse-home-updated", {
        detail: updatedProfile,
      })
    );

    setProfile(updatedProfile);
    setMessage("Home profile saved successfully!");
    setError("");
  }

  return (
    <section className="panel section-panel" id="home">
      <div className="panel-heading">
        <div>
          <h3>My Home</h3>
          <p>
            Register your household to personalise your energy estimates.
          </p>
        </div>
        <House size={23} />
      </div>

      <form className="home-profile-form" onSubmit={handleSubmit}>
        <label>
          Home name
          <input
            name="homeName"
            value={profile.homeName}
            onChange={updateField}
            placeholder="e.g. My Home"
            required
          />
        </label>

        <label>
          Household type
          <select
            name="householdType"
            value={profile.householdType}
            onChange={updateField}
          >
            <option>Independent house</option>
            <option>Apartment</option>
          </select>
        </label>

        <label>
          Number of family members
          <input
            name="members"
            type="number"
            min="1"
            max="100"
            step="1"
            value={profile.members}
            onChange={updateField}
            required
          />
        </label>

        <label>
          City
          <input
            name="city"
            value={profile.city}
            onChange={updateField}
            placeholder="e.g. Thiruvananthapuram"
          />
        </label>

        <label>
          State
          <input
            name="state"
            value={profile.state}
            onChange={updateField}
            placeholder="e.g. Kerala"
          />
        </label>

        <label>
          Home area (sq. ft.)
          <input
            name="area"
            type="number"
            min="0"
            step="any"
            value={profile.area ?? ""}
            onChange={updateField}
            placeholder="e.g. 1500"
          />
        </label>

        <label className="home-rate-field">
          Electricity rate (₹ per kWh)
          <input
            name="electricityRate"
            type="number"
            min="0"
            step="0.01"
            value={profile.electricityRate}
            onChange={updateField}
            required
          />
        </label>

        <div className="home-form-actions">
          <button type="submit" className="appliance-add-button">
            <Save size={17} />
            Save Home Details
          </button>
        </div>
      </form>

      {error && (
        <p className="home-error" role="alert">
          {error}
        </p>
      )}

      {message && (
        <p className="home-success" role="status">
          {message}
        </p>
      )}

      <p className="panel-footnote">
        Your household information is saved locally in this browser.
      </p>
    </section>
  );
}
