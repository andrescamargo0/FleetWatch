// chart.js
// Draws the "Problems" bar chart on the dashboard with the Chart.js library,
// and switches it between "By building" and "By cart" when you click the buttons.

// The numbers come from Python and puts them in a tag as JSON
const chartData = JSON.parse(document.getElementById("chart-data").textContent);

// One entry per problem type: the column name from analysis.py, its label, and its color name in style.css
const PROBLEMS = [
  { key: "stale", label: "Stale", color: "--series-stale" },
  { key: "outdated_os", label: "Outdated OS", color: "--series-outdated-os" },
  { key: "low_battery", label: "Low battery", color: "--series-low-battery" },
];

// Read a color variable from style.css, so the chart matches light or dark mode
function cssColor(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// Turn the rows for one grouping (buildings or carts) into what Chart.js expects
function buildData(group) {
  const rows = chartData[group];
  return {
    labels: rows.map((row) => row[group]),
    datasets: PROBLEMS.map((problem) => ({
      label: problem.label,
      data: rows.map((row) => row[problem.key]),
      backgroundColor: cssColor(problem.color),
      borderRadius: 4,
      maxBarThickness: 28,
      // How much of each building's or cart's space its bars fill. With only 2 buildings,
      // a smaller number keeps each group's 3 bars together instead of spread far apart.
      categoryPercentage: group === "building" ? 0.25 : 0.7,
    })),
  };
}

// Use the page's font and quiet gray text and grid lines, like the rest of the site.
Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
Chart.defaults.color = cssColor("--text-secondary");

const chart = new Chart(document.getElementById("problems-chart"), {
  type: "bar",
  data: buildData("building"),
  options: {
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        align: "start",
        labels: { usePointStyle: true, pointStyle: "circle", boxWidth: 8, boxHeight: 8 },
      },
      tooltip: { mode: "index", intersect: false },
    },
    scales: {
      x: { grid: { display: false } },
      y: {
        beginAtZero: true,
        ticks: { precision: 0 },
        grid: { color: cssColor("--separator") },
        title: { display: true, text: "Laptops" },
      },
    },
  },
});

// When a button is clicked, mark it as pressed and redraw the chart with that grouping
const buttons = document.querySelectorAll(".segmented button");
buttons.forEach((button) => {
  button.addEventListener("click", () => {
    buttons.forEach((b) => b.setAttribute("aria-pressed", b === button ? "true" : "false"));
    chart.data = buildData(button.dataset.group);
    chart.update();
  });
});