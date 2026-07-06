// =====================================================================
// デジトレ PWA版：食事コンサル（機能④）
//
// PC版 consult.py の移植。「目標と実績を引き算して、残りを出す担当」。
//   残り許容量 ＝ 目標(②targets) − 実績(③intake)
//
// 注意：目標(targets)と実績(intake)でキー名が違うので、ここで対応づける。
//   目標 targets:  "Target Kcal" / "P(g)" / "F(g)" / "C(g)"
//   実績 intake :  "kcal"        / "P"    / "F"    / "C"
// =====================================================================

/**
 * 目標から実績を引いて「残り許容量」を計算して返す。
 *
 * 戻り値: { kcal, P, F, C }
 *   プラス＝まだ食べてよい量／不足分、マイナス＝すでに超過（食べ過ぎ）。
 *   ※丸めない（丸めるのは表示する側の役目）。
 */
function calculateRemaining(targets, intake) {
  return {
    kcal: targets["Target Kcal"] - intake.kcal,
    P: targets["P(g)"] - intake.P,
    F: targets["F(g)"] - intake.F,
    C: targets["C(g)"] - intake.C,
  };
}
