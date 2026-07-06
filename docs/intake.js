// =====================================================================
// デジトレ PWA版：摂取量の計算（機能③）
//
// PC版 intake.py の移植。食品データ（foods.js の FOODS）を使い、
// 食べたもの（食品名＋量g）から合計カロリー・PFCを計算する。
//   ・データ（FOODS）とロジック（この計算）は分けたまま。
//   ・計算結果は丸めない（丸めるのは表示する側の役目）。
// =====================================================================

/**
 * 食べたものの合計カロリー・PFCを計算して返す。
 *
 * 引数:
 *   items : 食べたもののリスト。各要素は [食品名, 量g] のペア。
 *           例: [["ごはん（精白米）", 200], ["卵（全卵・生）", 50]]
 *   foods : 食品データ（省略すると foods.js の FOODS を使う）
 * 戻り値: 合計のオブジェクト { kcal, P, F, C } ※丸めない
 */
function calculateIntake(items, foods) {
  if (foods === undefined) {
    foods = FOODS; // 渡されなければ標準の食品データを使う
  }

  // 合計を入れる箱。最初はすべて 0。
  const total = { kcal: 0.0, P: 0.0, F: 0.0, C: 0.0 };

  for (const [name, grams] of items) {
    // 知らない食品名なら、黙って無視せずエラーで知らせる（打ち間違いに気づける）。
    if (!(name in foods)) {
      throw new Error(`食品データにありません: ${name}`);
    }

    const per100 = foods[name];   // その食品の「100gあたり」の栄養
    const ratio = grams / 100;    // 食べた量を「100g基準」に対する倍率に直す

    // 各栄養を「100gあたりの値 × 倍率」で足し込む
    total.kcal += per100.kcal * ratio;
    total.P += per100.P * ratio;
    total.F += per100.F * ratio;
    total.C += per100.C * ratio;
  }

  return total;
}

/**
 * 食事入力欄のテキストを [食品名, グラム] のリストに直す。
 * （PC版 app.py の parse_meal_text の移植）
 *
 * 1行に1品。区切りはカンマでも空白でもよい（例：「ごはん（精白米） 200」）。
 * 空行は無視する。数字に直せない行はエラーで知らせる。
 *
 * ★iPhone向けの追加処理：日本語キーボードだと「全角スペース」「全角数字」に
 *   なりやすいので、先に半角へそろえてから解釈する（Python版には無い配慮）。
 */
function parseMealText(text) {
  const items = [];

  for (let line of text.split("\n")) {
    // 全角スペース→半角スペース、全角数字０-９→半角、全角の．－も半角へ
    line = line
      .replace(/　/g, " ")
      .replace(/[０-９]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xfee0))
      .replace(/．/g, ".")
      .replace(/－/g, "-");

    line = line.trim();
    if (!line) continue; // 空行は無視

    // カンマがあればカンマで、無ければ「最後の空白」で食品名と量に分ける。
    let name, grams;
    if (line.includes(",")) {
      const i = line.indexOf(",");
      name = line.slice(0, i);
      grams = line.slice(i + 1);
    } else {
      const i = line.lastIndexOf(" ");
      name = i === -1 ? "" : line.slice(0, i);
      grams = i === -1 ? line : line.slice(i + 1);
    }

    name = name.trim();
    grams = grams.trim();
    if (!name || !grams) {
      throw new Error(`「${line}」は『食品名 グラム』の形で入力してください。`);
    }

    // Number() は "200" → 200 に変換。数字でなければ NaN（＝数値にならない印）になる。
    const gramsValue = Number(grams);
    if (!Number.isFinite(gramsValue)) {
      throw new Error(`「${line}」の量を数字にできません。`);
    }

    items.push([name, gramsValue]);
  }

  return items;
}
