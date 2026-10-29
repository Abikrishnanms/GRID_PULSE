
const DATA_PATH = "/data/";

async function loadCsv(filename) {
  const response = await fetch(`${DATA_PATH}${filename}`);

  if (!response.ok) {
    throw new Error(
      `Could not load ${filename}. HTTP status: ${response.status}`
    );
  }

  const text = await response.text();
  const lines = text.trim().split(/\r?\n/);

  if (lines.length < 2) {
    throw new Error(`${filename} contains no data rows.`);
  }

  // CSV fields in these summary files do not contain embedded commas.
  const headers = lines[0]
    .replace(/^\uFEFF/, "")
    .split(",")
    .map((header) => header.trim());

  return lines.slice(1).filter(Boolean).map((line, rowIndex) => {
    const values = line.split(",");

    if (values.length !== headers.length) {
      throw new Error(
        `Invalid CSV row ${rowIndex + 2} in ${filename}.`
      );
    }

    return Object.fromEntries(
      headers.map((header, index) => {
        const value = values[index]?.trim() ?? "";

        if (value === "") return [header, null];

        const numericValue = Number(value);

        return [
          header,
          Number.isFinite(numericValue) ? numericValue : value,
        ];
      })
    );
  });
}

function requireColumns(rows, columns, filename) {
  if (!rows.length) {
    throw new Error(`${filename} has no usable rows.`);
  }

  const missing = columns.filter(
    (column) => !(column in rows[0])
  );

  if (missing.length) {
    throw new Error(
      `${filename} is missing required columns: ${missing.join(", ")}`
    );
  }
}

export async function loadEnergyData() {
  const [daily, monthly, tariffs] = await Promise.all([
    loadCsv("daily_energy_summary.csv"),
    loadCsv("monthly_comparison.csv"),
    loadCsv("tariff_summary.csv"),
  ]);

  requireColumns(
    daily,
    ["date", "total_energy_kwh", "households", "total_readings",
      "energy_per_household_kwh"],
    "daily_energy_summary.csv"
  );

  requireColumns(
    monthly,
    ["month", "monthly_energy_kwh", "days_present",
      "average_daily_energy_kwh", "energy_per_household_day_kwh"],
    "monthly_comparison.csv"
  );

  requireColumns(
    tariffs,
    ["tariff_type", "total_energy_kwh", "energy_share_percent"],
    "tariff_summary.csv"
  );

  daily.sort((a, b) => a.date.localeCompare(b.date));
  monthly.sort((a, b) => a.month.localeCompare(b.month));

  return { daily, monthly, tariffs };
}
