
const DATA_PATH = "/data/";

async function loadCsv(filename) {
  const response = await fetch(`${DATA_PATH}${filename}`);

  if (!response.ok) {
    throw new Error(`Could not load ${filename}: ${response.status}`);
  }

  const csvText = await response.text();
  const lines = csvText.trim().split(/\r?\n/);

  if (lines.length < 2) {
    throw new Error(`${filename} has no data rows.`);
  }

  const headers = lines[0].split(",").map((header) => header.trim());

  return lines.slice(1).map((line) => {
    const values = line.split(",");

    return Object.fromEntries(
      headers.map((header, index) => {
        const value = values[index]?.trim() ?? "";

        if (value === "") return [header, null];

        const numericValue = Number(value);

        return [
          header,
          Number.isFinite(numericValue) ? numericValue : value,
        ];
      }),
    );
  });
}

export async function loadEnergyData() {
  const [daily, monthly, tariffs] = await Promise.all([
    loadCsv("daily_energy_summary.csv"),
    loadCsv("monthly_comparison.csv"),
    loadCsv("tariff_summary.csv"),
  ]);

  return {
    daily: daily.sort((a, b) => a.date.localeCompare(b.date)),
    monthly: monthly.sort((a, b) => a.month.localeCompare(b.month)),
    tariffs,
  };
}
