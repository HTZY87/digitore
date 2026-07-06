// =====================================================================
// デジトレ PWA版：安全警告（機能⑥）
//
// PC版 safety.py の移植。「その設定、極端すぎませんか？」を見張る担当。
// 1日のカロリー増減から「1か月の体重変化（予測）」を計算し、
// それが現体重の5%を超えるなら警告する。
// =====================================================================

// 体重1kgの増減に相当する、おおよそのカロリー（体脂肪ベースの一般値）。
const KCAL_PER_KG_BODY = 7200;

/**
 * 安全判定の“計算だけ”を行う（表示は画面側 app.js の役目）。
 *
 * 戻り値:
 *   {
 *     monthly_change_kg: 月の予測変化(kg),
 *     percent:           現体重に対する割合(%),
 *     is_extreme:        5%を超えていれば true（＝警告すべき）,
 *   }
 */
function evaluateSafety(weight, goalOffset) {
  // 月の予測変化(kg) = 1日の増減 × 30日 ÷ (1kgあたりのカロリー)
  const monthlyChangeKg = (goalOffset * 30) / KCAL_PER_KG_BODY;
  // 現体重に対する割合(%)。Math.abs は絶対値（符号を外して大きさだけ見る）
  const percent = (Math.abs(monthlyChangeKg) / weight) * 100;
  return {
    monthly_change_kg: monthlyChangeKg,
    percent: percent,
    is_extreme: percent > 5,
  };
}
