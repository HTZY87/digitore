// =====================================================================
// デジトレ PWA版：可視化（機能⑧）
//
// PC版 visualize.py（matplotlibでPNG画像を作る）の置き換え。
// ブラウザでは Chart.js（vendor/chart.umd.js に同梱。オフラインでも動く）を
// 使って、画面の <canvas>（＝お絵かき用の領域）に直接グラフを描く。
//
// 作るグラフは PC版と同じ2つ：
//   ① カロリー：実績 vs 目標（棒グラフ）
//   ② タンパク質(P)の達成度（折れ線・100%の目安線つき）
// 達成度の割り算はコード側で計算する（数値はブレさせない）。
// =====================================================================

// 作ったグラフを覚えておく箱。描き直すときに前のグラフを消すために使う。
// （消さずに重ね書きすると、Chart.js は同じcanvasを二重に使えずエラーになる）
let calorieChart = null;
let proteinChart = null;

/** ① カロリー：実績 vs 目標（棒グラフ）を canvas に描く。 */
function renderCalorieChart(canvas, records) {
  const labels = records.map((r) => r["日付"]);
  const actual = records.map((r) => r["合計kcal"]);
  const target = records.map((r) => r["目標kcal"]);

  if (calorieChart !== null) calorieChart.destroy(); // 前回の描画を消す

  calorieChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        { label: "実績 kcal", data: actual, backgroundColor: "#4a90d9" },
        { label: "目標 kcal", data: target, backgroundColor: "#c5d9ee" },
      ],
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, title: { display: true, text: "kcal" } } },
    },
  });
}

/** ② タンパク質(P)の達成度（実績P ÷ 目標P × 100%）を折れ線で描く。 */
function renderProteinChart(canvas, records) {
  const labels = records.map((r) => r["日付"]);
  // 達成度(%)。目標Pが0や値なしの行は計算できないので null（＝点を打たない）にする。
  const percent = records.map((r) => {
    const goal = r["目標P(g)"];
    const actual = r["P(g)"];
    if (goal === null || actual === null || goal === 0) return null;
    return (actual / goal) * 100;
  });
  // 100%の目安線（全ての日で100の直線を重ねて描く）
  const guide = records.map(() => 100);

  if (proteinChart !== null) proteinChart.destroy();

  proteinChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "P達成度 (%)",
          data: percent,
          borderColor: "#2e9e5b",
          backgroundColor: "#2e9e5b",
          tension: 0, // 点と点はまっすぐ結ぶ（値を素直に見せる）
        },
        {
          label: "目標 (100%)",
          data: guide,
          borderColor: "#e07a7a",
          borderDash: [6, 4], // 破線にして目安線だと分かるようにする
          pointRadius: 0,     // 点は描かない（線だけ）
        },
      ],
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, title: { display: true, text: "%" } } },
    },
  });
}
