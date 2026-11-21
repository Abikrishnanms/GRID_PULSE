
const STORAGE_KEYS = {
  home: "gridpulse_home",
  appliances: "gridpulse_appliances",
  settings: "gridpulse_settings",
};

// Read information from browser storage
function readStorage(key, fallback) {
  try {
    const savedData = localStorage.getItem(key);
    return savedData ? JSON.parse(savedData) : fallback;
  } catch (error) {
    console.error("Unable to read saved data:", error);
    return fallback;
  }
}

// Save information to browser storage
function saveStorage(key, data) {
  try {
    localStorage.setItem(key, JSON.stringify(data));
    return true;
  } catch (error) {
    console.error("Unable to save data:", error);
    return false;
  }
}


export function getHomeProfile() {
  return {
    homeName: "",
    householdType: "Independent house",
    members: 1,
    city: "",
    state: "Kerala",
    area: "",
    electricityRate: 8,
  };
}


export function saveHomeProfile(profile) {
  return saveStorage(STORAGE_KEYS.home, profile);
}

// APPLIANCES
export function getAppliances() {
  return readStorage(STORAGE_KEYS.appliances, []);
}

export function saveAppliances(appliances) {
  return saveStorage(STORAGE_KEYS.appliances, appliances);
}

// SETTINGS
export function getSettings() {
  return readStorage(STORAGE_KEYS.settings, {
    currency: "INR",
    symbol: "₹",
    theme: "light",
    energyUnit: "kWh",
  });
}

export function saveSettings(settings) {
  return saveStorage(STORAGE_KEYS.settings, settings);
}

// RESET USER DATA
export function resetHouseholdData() {
  try {
    Object.values(STORAGE_KEYS).forEach((key) => {
      localStorage.removeItem(key);
    });
    return true;
  } catch (error) {
    console.error("Unable to reset data:", error);
    return false;
  }
}
