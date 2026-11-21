
const DAYS_PER_MONTH = 30;

// Calculate energy consumption of one appliance
export function calculateApplianceEnergy(appliance) {
  const {
    wattage = 0,
    quantity = 1,
    hoursPerDay = 0,
    daysPerWeek = 7,
  } = appliance;

  const dailyEnergy =
    (Number(wattage) *
      Number(quantity) *
      Number(hoursPerDay) *
      Number(daysPerWeek)) /
    7 /
    1000;

  return {
    daily: dailyEnergy,
    weekly: dailyEnergy * 7,
    monthly: dailyEnergy * DAYS_PER_MONTH,
  };
}

// Calculate complete household consumption
export function calculateHouseholdEnergy(appliances) {
  const result = appliances.reduce(
    (total, appliance) => {
      const energy = calculateApplianceEnergy(appliance);

      return {
        daily: total.daily + energy.daily,
        weekly: total.weekly + energy.weekly,
        monthly: total.monthly + energy.monthly,
      };
    },
    { daily: 0, weekly: 0, monthly: 0 }
  );

  return result;
}

// Estimate electricity bill
export function calculateElectricityBill(
  monthlyEnergy,
  ratePerKwh
) {
  return Number(monthlyEnergy) * Number(ratePerKwh);
}

// Calculate individual appliance contribution
export function calculateApplianceBreakdown(appliances) {
  const household = calculateHouseholdEnergy(appliances);

  return appliances.map((appliance) => {
    const energy = calculateApplianceEnergy(appliance);

    const percentage = household.daily > 0
      ? (energy.daily / household.daily) * 100
      : 0;

    return {
      ...appliance,
      ...energy,
      percentage,
    };
  });
}
