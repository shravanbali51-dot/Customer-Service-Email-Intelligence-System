const revealItems = document.querySelectorAll(".reveal");

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("visible"));
}

if (window.analyticsData && window.Chart) {
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        labels: { color: "#344054" },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: "#667085", precision: 0 },
        grid: { color: "#e5e7eb" },
      },
      x: {
        ticks: { color: "#667085" },
        grid: { display: false },
      },
    },
  };

  const statusCanvas = document.getElementById("statusChart");
  if (statusCanvas) {
    new Chart(statusCanvas, {
      type: "bar",
      data: {
        labels: window.analyticsData.status.labels,
        datasets: [{
          label: "Tickets",
          data: window.analyticsData.status.values,
          backgroundColor: ["#f4c542", "#3b82f6", "#16a34a", "#0f766e", "#6b7280"],
          borderRadius: 8,
        }],
      },
      options: chartOptions,
    });
  }

  const sentimentCanvas = document.getElementById("sentimentChart");
  if (sentimentCanvas) {
    new Chart(sentimentCanvas, {
      type: "doughnut",
      data: {
        labels: window.analyticsData.sentiment.labels,
        datasets: [{
          data: window.analyticsData.sentiment.values,
          backgroundColor: ["#16a34a", "#3b82f6", "#dc2626"],
          borderColor: "#ffffff",
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            labels: { color: "#344054" },
          },
        },
      },
    });
  }
}
