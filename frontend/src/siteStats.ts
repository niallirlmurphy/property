import stats from "./data/site_stats.json";

// Headline register figures, regenerated after each PPR sync by
// scripts/generate_site_stats.py. Formatted by hand rather than with
// toLocaleString so the prerendered HTML and the hydrated client always agree.

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const thousands = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
const monthYear = (iso: string) => `${MONTHS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;

export const SITE_STATS = {
  ...stats,
  totalSales: thousands(stats.total_sales),
  // Rounded down to the nearest 5,000 for copy that shouldn't read as exact
  totalSalesRounded: thousands(Math.floor(stats.total_sales / 5000) * 5000),
  mappedPct: Math.round((stats.mapped_sales / stats.total_sales) * 100),
  firstMonth: monthYear(stats.first_sale_date),
  lastMonth: monthYear(stats.last_sale_date),
  firstYear: stats.first_sale_date.slice(0, 4),
  lastYear: stats.last_sale_date.slice(0, 4),
};
