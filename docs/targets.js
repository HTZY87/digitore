// =====================================================================
// デジトレ PWA版：目標値の計算（機能②）
//
// PC版 targets.py を JavaScript に移植したもの。計算式・数値は
// Python版と完全に同じにする（両者のテストで一致を守る）。
//   ・計算はすべてコードで行う（AIの暗算に頼らない＝毎回同じ結果）。
//   ・エンジンは丸めず正確な数値を返す（丸めるのは表示する側の役目）。
// =====================================================================

// カロリー換算係数：栄養素1gあたりのkcal（栄養学で決まった固定値）。
const KCAL_PER_GRAM = { P: 4, F: 9, C: 4 };

// PFC戦略の定義（データ）。各栄養素を [計算方法, 値] のペアで持つ。
//   "percent"   : 目標カロリーの割合で決める（0.15 = 15%）
//   "per_kg"    : 体重1kgあたりのグラム数で決める（1.2 など）
//   "remainder" : 残ったカロリーを全部わりあてる（値は使わないので null）
// ★戦略を増やしたいときは、ここに1行足すだけ（下のロジックは変更不要）。
const STRATEGIES = {
  "①ウェルネス":     { P: ["percent", 0.15], F: ["percent", 0.25], C: ["percent", 0.60] },
  "②ヘルスケア":     { P: ["per_kg", 1.2],   F: ["percent", 0.25], C: ["remainder", null] },
  "③ダイエット特化": { P: ["percent", 0.30], F: ["percent", 0.20], C: ["percent", 0.50] },
  "④筋肥大・競技者": { P: ["per_kg", 2.0],   F: ["percent", 0.20], C: ["remainder", null] },
};

/**
 * 1つの栄養素（P/F/C）のグラム数を、指定された「方法」で計算する小さな部品。
 * （Python版の _grams_for_macro と同じ）
 */
function gramsForMacro(method, value, macro, targetKcal, weight, usedKcal) {
  const factor = KCAL_PER_GRAM[macro]; // この栄養素の1gあたりkcal（P/C=4, F=9）

  if (method === "percent") {
    // 目標カロリーの割合(value) ÷ 1gあたりkcal → グラム数
    return (targetKcal * value) / factor;
  } else if (method === "per_kg") {
    // 体重 × 係数(value) → グラム数（カロリーは使わない）
    return weight * value;
  } else if (method === "remainder") {
    // 残りカロリー（目標 − すでに使った分）÷ 1gあたりkcal → グラム数
    return (targetKcal - usedKcal) / factor;
  }
  // 想定外の方法名が来たら、原因がすぐ分かるようにエラーで知らせる
  throw new Error(`未知の計算方法です: ${method}`);
}

/**
 * 体の情報から、1日の目標カロリーとPFC（グラム数）を計算して返す。
 *
 * 引数 profile の中身（Python版の引数と同じ）:
 *   gender         : 性別 'male'（男性）/ 'female'（女性）
 *   age            : 年齢（歳）
 *   height         : 身長（cm）
 *   weight         : 現在の体重（kg）
 *   activity_level : 生活活動強度 1.2（低い）〜 1.9（高い）
 *   goal_offset    : 目的によるカロリー増減（減量 -500 など）
 *   strategy       : PFC戦略の名前（STRATEGIES のキーのどれか）
 * 戻り値: BMR・TDEE・目標カロリー・P・F・C をまとめたオブジェクト
 *         （キー名も Python 版とそろえる："Target Kcal" など）
 */
function calculateDailyTargets(profile) {
  const { gender, age, height, weight, activity_level, goal_offset, strategy } = profile;

  // --- 性別が正しいか先に確認（間違ったまま計算が進むのを防ぐ）---
  if (gender !== "male" && gender !== "female") {
    throw new Error(`未知の性別です: ${gender} / 選べるのは 'male' か 'female'`);
  }

  // --- 戦略名が正しいか先に確認 ---
  if (!(strategy in STRATEGIES)) {
    throw new Error(`未知の戦略です: ${strategy} / 選べるのは ${Object.keys(STRATEGIES).join(", ")}`);
  }

  // === 1. BMR（基礎代謝量）を Mifflin-St Jeor 式で計算 ===
  // 性別で最後に足す数だけ変わる（男性 +5 / 女性 -161）。
  const s = gender === "male" ? 5 : -161;
  const bmr = 10 * weight + 6.25 * height - 5 * age + s;

  // === 2. TDEE（総消費カロリー）と 目標カロリー ===
  const tdee = bmr * activity_level;       // 活動量を反映した1日の消費
  const targetKcal = tdee + goal_offset;   // 目的の増減を足したものが目標

  // === 3. 戦略データを読んで P・F・C のグラム数を計算 ===
  const rule = STRATEGIES[strategy];
  let usedKcal = 0;      // ここまでに使ったカロリーの合計
  const grams = {};      // 計算結果を入れる箱

  // P → F → C の順で計算（C が "remainder" の戦略があるため順番が大事）
  for (const macro of ["P", "F", "C"]) {
    const [method, value] = rule[macro];
    const g = gramsForMacro(method, value, macro, targetKcal, weight, usedKcal);
    grams[macro] = g;
    usedKcal += g * KCAL_PER_GRAM[macro];
  }

  // === 4. 結果をまとめて返す ===
  // ここでは“丸めない”のが大事なポイント（丸めるのは画面に見せる瞬間だけ）。
  return {
    "BMR": bmr,
    "TDEE": tdee,
    "Target Kcal": targetKcal,
    "P(g)": grams.P,
    "F(g)": grams.F,
    "C(g)": grams.C,
  };
}
