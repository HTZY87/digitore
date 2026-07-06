// =====================================================================
// デジトレ PWA版：記録の保存（機能⑤）と CSV入出力
//
// PC版 record.py の役目を、ブラウザの localStorage（＝端末内にデータを
// 残せる保存領域。サーバーに送られない）で置き換えたもの。
//   ・プロフィール（初期設定＋目標）と記録は、すべて iPhone/PC の端末内だけに残る。
//   ・PC版の records.csv と行き来できるよう、同じ列並びのCSVを
//     書き出し（エクスポート）／取り込み（インポート）できる。
//
// 注意：localStorage は「Safariのデータを消去」などで消えることがある。
//       大事な記録は、ときどきCSVエクスポートで控えを取っておくのが安全。
// =====================================================================

// localStorage に保存するときの名前（キー）。他アプリとぶつからないよう接頭辞つき。
const PROFILE_KEY = "digitore.profile";
const RECORDS_KEY = "digitore.records";

// CSVの列の見出しと並び順（PC版 record.py の COLUMNS と同じにする）。
// 保存も読み込みも、このリストを基準にすればズレない。
const COLUMNS = [
  "日付", "体重", "メニュー名",
  "合計kcal", "P(g)", "F(g)", "C(g)",
  "目標kcal", "目標P(g)",
  "判定/備考",
];

// どの列が「数値」か（CSV取り込み時に数値へ変換する対象）。
const NUMERIC_COLUMNS = ["体重", "合計kcal", "P(g)", "F(g)", "C(g)", "目標kcal", "目標P(g)"];


// =====================================================================
// 1. プロフィール（初期設定の内容＋計算済み目標）の保存・読み込み
// =====================================================================

/** 初期設定の内容と計算結果（目標）を端末内に保存する。 */
function saveProfileData(profile, targets) {
  // JSON.stringify＝オブジェクトを文字列に変換（localStorage は文字列しか持てないため）
  localStorage.setItem(PROFILE_KEY, JSON.stringify({ profile: profile, targets: targets }));
}

/** 保存済みのプロフィールを読む。まだ初期設定していなければ null を返す。 */
function loadProfileData() {
  const text = localStorage.getItem(PROFILE_KEY);
  if (text === null) return null;
  try {
    return JSON.parse(text); // 文字列 → オブジェクトに戻す
  } catch (e) {
    return null; // 壊れたデータは「未設定」として扱う（アプリを止めない）
  }
}


// =====================================================================
// 2. 記録の保存・読み込み（1食分＝1件のオブジェクト）
// =====================================================================

/** 保存済みの記録すべてを読む。まだ無ければ空のリスト [] を返す。 */
function loadRecords() {
  const text = localStorage.getItem(RECORDS_KEY);
  if (text === null) return [];
  try {
    const records = JSON.parse(text);
    return Array.isArray(records) ? records : [];
  } catch (e) {
    return [];
  }
}

/** 記録のリスト全体を保存し直す（取り込みや追記の土台になる共通処理）。 */
function saveAllRecords(records) {
  localStorage.setItem(RECORDS_KEY, JSON.stringify(records));
}

/**
 * 1食分の記録を末尾に追記する（PC版 save_record と同じ役目）。
 *
 * 引数（record.py の save_record と同じ材料）:
 *   date    : 日付の文字列（例 "2026-07-06"）
 *   weight  : その日の体重(kg)
 *   menu    : メニュー名（例 "鶏むね定食"）
 *   intake  : ③calculateIntake が返す実績 { kcal, P, F, C }
 *   targets : ②calculateDailyTargets が返す目標
 *   note    : 判定や備考の文字列
 */
function appendRecord(date, weight, menu, intake, targets, note) {
  const records = loadRecords();
  // 列の決まり（COLUMNS）と同じキー名で1件を組み立てる。
  // 数値は丸めずそのまま保存する（丸めるのは表示・グラフ側の役目）。
  records.push({
    "日付": date,
    "体重": weight,
    "メニュー名": menu,
    "合計kcal": intake.kcal,
    "P(g)": intake.P,
    "F(g)": intake.F,
    "C(g)": intake.C,
    "目標kcal": targets["Target Kcal"],
    "目標P(g)": targets["P(g)"],
    "判定/備考": note,
  });
  saveAllRecords(records);
}


// =====================================================================
// 3. CSV 書き出し（エクスポート）
//    PC版 records.csv と同じ形式にする（PCのPython側でもそのまま読める）。
// =====================================================================

/** CSVの1マス分の文字列を作る。カンマや引用符を含むときは "..." で囲む決まり。 */
function csvEscape(value) {
  const s = value === null || value === undefined ? "" : String(value);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    // 中の " は "" に二重化するのがCSVのルール
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

/** 記録のリストを、records.csv と同じ形式のCSV文字列にする。 */
function recordsToCsv(records) {
  const lines = [COLUMNS.map(csvEscape).join(",")]; // 1行目は見出し
  for (const rec of records) {
    lines.push(COLUMNS.map((col) => csvEscape(rec[col])).join(","));
  }
  // 改行は \r\n（PythonのCSV標準と同じ）。最後にも改行を1つ付ける。
  return lines.join("\r\n") + "\r\n";
}


// =====================================================================
// 4. CSV 取り込み（インポート）
// =====================================================================

/**
 * CSV文字列を「行ごとのマスのリスト」に分解する小さな部品。
 * "..." で囲まれたマス（中にカンマや改行があるもの）も正しく扱う。
 */
function parseCsv(text) {
  const rows = [];
  let field = "";      // いま読んでいるマス
  let row = [];        // いま読んでいる行
  let inQuotes = false; // "..." の中かどうか

  // 先頭に BOM（＝ファイル先頭に付くことがある見えない印）があれば外す
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } // "" は " 1文字の意味
        else inQuotes = false;                            // 囲みの終わり
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field); field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++; // \r\n はまとめて1つの改行
      row.push(field); field = "";
      rows.push(row); row = [];
    } else {
      field += ch;
    }
  }
  // 最後の行（末尾に改行が無い場合）も忘れずに拾う
  if (field !== "" || row.length > 0) { row.push(field); rows.push(row); }

  // 完全な空行は捨てる
  return rows.filter((r) => !(r.length === 1 && r[0] === ""));
}

/**
 * CSV文字列を記録のリストに変換する（PC版 load_records と同じ役目）。
 * 1行目の見出しが COLUMNS と一致するかを確かめ、違えばエラーで知らせる。
 * 数値の列は数値に変換する（空のマスは null＝「値なし」にする）。
 */
function csvToRecords(text) {
  const rows = parseCsv(text);
  if (rows.length === 0) {
    throw new Error("CSVが空です。records.csv の中身を貼り付けてください。");
  }

  // 見出し行の確認（列がズレたまま取り込む事故を防ぐ）
  const header = rows[0].map((h) => h.trim());
  if (header.join(",") !== COLUMNS.join(",")) {
    throw new Error(
      "CSVの見出しが records.csv の形式と違います。\n" +
      `想定: ${COLUMNS.join(",")}\n実際: ${header.join(",")}`
    );
  }

  const records = [];
  for (const row of rows.slice(1)) {
    const rec = {};
    COLUMNS.forEach((col, i) => {
      let value = row[i] === undefined ? "" : row[i];
      if (NUMERIC_COLUMNS.includes(col)) {
        // 数値の列は数値へ。空のマスは null（＝値なし）にしておく。
        if (value === "") {
          value = null;
        } else {
          const n = Number(value);
          if (!Number.isFinite(n)) {
            throw new Error(`「${col}」の値を数字にできません: ${value}`);
          }
          value = n;
        }
      }
      rec[col] = value;
    });
    records.push(rec);
  }
  return records;
}
