// =====================================================================
// デジトレ PWA版：画面の司令塔（PC版 app.py にあたる役目）
//
// PC版と同じく、このファイルは“画面とつなぐ”だけに徹する。
// 計算・保存・グラフの本体は各担当ファイル
// （targets/intake/consult/safety/storage/charts の各 .js）をそのまま呼ぶ。
//
// 画面の切り替えは「ハッシュ（URLの # から後ろの部分）」で行う。
//   例: index.html#record → 記録画面
// こうしておくと、ブラウザの「戻る」も自然に効く。
// =====================================================================

// ---------------------------------------------------------------------
// 表示用の丸め（エンジンは丸めず返すので、見せる瞬間にここで丸める）
// ---------------------------------------------------------------------
function fmt0(x) { return x.toFixed(0); }  // 整数で表示（PC版の %.0f と同じ）
function fmt1(x) { return x.toFixed(1); }  // 小数第1位まで（%.1f と同じ）
function fmtSigned1(x) { return (x >= 0 ? "+" : "") + x.toFixed(1); } // %+.1f と同じ

/** 今日の日付を "2026-07-06" の形で返す（端末の時計基準）。 */
function todayString() {
  const d = new Date();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

/** 文字をHTMLに埋め込むとき、タグとして解釈されないよう無害化する。 */
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------
// 一言メッセージ（PC版の flash と同じ役目）
// ---------------------------------------------------------------------
let pendingFlash = null; // 「次の画面で見せる」メッセージの置き場

/** いまの画面にすぐメッセージを出す（入力エラーなど、その場で知らせる用）。 */
function flashNow(message, isWarn) {
  const el = document.getElementById("flash");
  el.textContent = message;
  el.hidden = false;
  el.classList.toggle("warn", Boolean(isWarn));
  window.scrollTo(0, 0); // メッセージは画面上部に出るので、そこまで戻す
}

/** 次に切り替わった画面でメッセージを出す（「記録しました」など画面またぎ用）。 */
function flashNext(message, isWarn) {
  pendingFlash = { message: message, isWarn: Boolean(isWarn) };
}

// ---------------------------------------------------------------------
// 画面の切り替え（ルーター）
// ---------------------------------------------------------------------

// 存在する画面の一覧。ハッシュ名 → section の id に対応する。
const VIEWS = ["home", "onboarding", "result", "record", "record-done", "records", "charts"];

// 結果系の画面（result / record-done）は、直前の計算内容を覚えておいて表示する。
// ページを開き直すなどで内容が無いときは、ホームに戻す。
let lastResult = null; // { profile, targets, safety }
let lastDone = null;   // { menu, intake, remaining }

// タブバーの光らせ方：結果画面のときは「元になった入口のタブ」を光らせる
const SUB_VIEW_TAB = { "result": "onboarding", "record-done": "record" };

/** 指定した名前の画面だけを表示し、他は隠す。表示前に中身の準備もする。 */
function showView(name) {
  // 「次の画面で見せる」と頼まれていたメッセージがあれば出す。無ければ消す。
  if (pendingFlash !== null) {
    flashNow(pendingFlash.message, pendingFlash.isWarn);
    pendingFlash = null;
  } else {
    document.getElementById("flash").hidden = true;
  }

  // 各画面の描画準備（データを画面に流し込む）
  if (name === "home") renderHome();
  if (name === "onboarding") renderOnboardingForm();
  if (name === "result") renderResult();
  if (name === "record") renderRecordForm();
  if (name === "record-done") renderRecordDone();
  if (name === "records") renderRecordsView();

  // 画面の表示・非表示を切り替える
  for (const v of VIEWS) {
    document.getElementById("view-" + v).hidden = (v !== name);
  }

  // グラフは「画面を表示してから」描く（隠れたままのcanvasには正しく描けないため）
  if (name === "charts") renderChartsView();

  // タブバーの「いまここ」を光らせる
  const activeTab = SUB_VIEW_TAB[name] || name;
  document.querySelectorAll(".tabbar a").forEach((a) => {
    a.classList.toggle("active", a.dataset.view === activeTab);
  });

  window.scrollTo(0, 0); // 画面を切り替えたら先頭から見せる
}

/** URLのハッシュを見て、対応する画面を出す（戻る/進むボタンでも呼ばれる）。 */
function route() {
  let name = location.hash.replace("#", "") || "home";
  if (!VIEWS.includes(name)) name = "home";

  // 結果画面は「直前の計算」があるときだけ見せられる（無ければホームへ）
  if (name === "result" && lastResult === null) name = "home";
  if (name === "record-done" && lastDone === null) name = "home";

  // 記録・グラフは、先に初期設定が必要（PC版と同じ案内で誘導する）
  if (name === "record" && loadProfileData() === null) {
    flashNext("先に初期設定をして、1日の目標を決めましょう。");
    location.hash = "onboarding";
    return;
  }
  if (name === "charts" && loadRecords().length === 0) {
    flashNext("まだ記録がありません。先に食事を記録してください。");
    location.hash = "record";
    return;
  }

  showView(name);
}

// ---------------------------------------------------------------------
// 画面①：ホーム
// ---------------------------------------------------------------------
function renderHome() {
  const data = loadProfileData();
  const box = document.getElementById("home-summary");
  if (data === null) {
    box.innerHTML = "<p>まずは「初期設定」から、あなたの1日の栄養目標を計算しましょう。</p>";
    return;
  }
  const t = data.targets;
  box.innerHTML =
    "<p>現在の1日の目標（最後に設定した内容）：</p>" +
    `<p class="num">🔥 目標カロリー <strong>${fmt0(t["Target Kcal"])}</strong> kcal ／` +
    ` 🍗 P <strong>${fmt1(t["P(g)"])}</strong> g ／` +
    ` 🥑 F <strong>${fmt1(t["F(g)"])}</strong> g ／` +
    ` 🍚 C <strong>${fmt1(t["C(g)"])}</strong> g</p>` +
    `<p class="muted">戦略：${escapeHtml(data.profile.strategy)}</p>`;
}

// ---------------------------------------------------------------------
// 画面②：初期設定 → 計算 → 結果表示
// ---------------------------------------------------------------------

/** 初期設定フォームに、保存済みの内容を入れ直す（毎回打ち直さなくて済むように）。 */
function renderOnboardingForm() {
  const data = loadProfileData();
  if (data === null) return; // 初回は、HTMLに書いてある標準の値のまま

  const form = document.getElementById("onboarding-form");
  const p = data.profile;
  form.gender.value = p.gender;
  form.age.value = p.age;
  form.height.value = p.height;
  form.weight.value = p.weight;
  form.activity_level.value = p.activity_level;
  form.goal_offset.value = String(p.goal_offset);
  form.strategy.value = p.strategy;
}

/** 初期設定フォームの送信：目標を計算し、保存して、結果画面へ。 */
function handleOnboardingSubmit(event) {
  event.preventDefault(); // 本来のフォーム送信（ページ再読み込み）を止めて、JSで処理する
  const form = event.target;

  const profile = {
    gender: form.gender.value,
    age: parseInt(form.age.value, 10),
    height: parseFloat(form.height.value),
    weight: parseFloat(form.weight.value),
    activity_level: parseFloat(form.activity_level.value),
    goal_offset: parseInt(form.goal_offset.value, 10),
    strategy: form.strategy.value,
  };

  // 数字にできない入力があれば止める（PC版と同じ文言で知らせる）
  if ([profile.age, profile.height, profile.weight,
       profile.activity_level, profile.goal_offset].some((v) => !Number.isFinite(v))) {
    flashNow("入力に不備があります。すべての項目を正しく入れてください。", true);
    return;
  }

  // ② 目標の計算はエンジンに依頼（性別や戦略が変ならエラーが飛ぶ）
  let targets;
  try {
    targets = calculateDailyTargets(profile);
  } catch (e) {
    flashNow(e.message, true);
    return;
  }

  // ⑥ 安全判定（計算のみ）。極端な設定なら結果画面で警告を出す。
  const safety = evaluateSafety(profile.weight, profile.goal_offset);

  // 次回も使えるよう端末内に保存しておく。
  saveProfileData(profile, targets);

  lastResult = { profile: profile, targets: targets, safety: safety };
  location.hash = "result";
}

/** 結果画面に、計算した目標と安全チェックを流し込む。 */
function renderResult() {
  const { targets, safety } = lastResult;

  document.getElementById("r-bmr").textContent = fmt1(targets["BMR"]);
  document.getElementById("r-tdee").textContent = fmt1(targets["TDEE"]);
  document.getElementById("r-kcal").textContent = fmt0(targets["Target Kcal"]);
  document.getElementById("r-p").textContent = fmt1(targets["P(g)"]);
  document.getElementById("r-f").textContent = fmt1(targets["F(g)"]);
  document.getElementById("r-c").textContent = fmt1(targets["C(g)"]);

  const card = document.getElementById("safety-card");
  const text = document.getElementById("safety-text");
  const pct = fmt1(safety.percent);
  const kg = fmtSigned1(safety.monthly_change_kg);
  if (safety.is_extreme) {
    card.classList.add("flash", "warn");
    text.innerHTML = `⚠ 注意：この設定だと月の体重変化が約 <strong class="num">${pct}%</strong>` +
      `（${kg}kg）と大きめです。<br>体に負担がかかる可能性があります。` +
      `もう少しゆるやかな目標も検討しましょう。`;
  } else {
    card.classList.remove("flash", "warn");
    text.innerHTML = `✓ 体重変化は月 約 <strong class="num">${pct}%</strong>（${kg}kg）。無理のない範囲です。`;
  }
}

// ---------------------------------------------------------------------
// 画面③：食事を記録（③摂取量 → ④残り → ⑤保存 を1画面で）
// ---------------------------------------------------------------------

/** 記録フォームの準備：日付に今日を入れ、体重のヒントと食品名ボタンを用意する。 */
function renderRecordForm() {
  const data = loadProfileData(); // route() で設定済みを確認してから来る
  const form = document.getElementById("record-form");

  // 日付が空のときだけ「今日」を自動セット（入力途中の値は上書きしない）
  if (!form.date.value) form.date.value = todayString();

  // 体重欄のヒント（未入力なら初期設定の体重を使う、の案内）
  document.getElementById("record-weight-hint").textContent = data.profile.weight;
  form.weight.placeholder = data.profile.weight;

  // 食品名ボタン（タップで「食べたもの」欄に1行追加）を一覧から作る
  const list = document.getElementById("food-list");
  if (list.childElementCount === 0) { // 一度作れば十分
    for (const name of Object.keys(FOODS).sort()) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "food-name";
      btn.textContent = name;
      btn.addEventListener("click", () => {
        // グラム数はわざと入れない（勝手な量で記録される事故を防ぎ、続けて数字を打ってもらう）
        const box = form.meal;
        if (box.value && !box.value.endsWith("\n")) box.value += "\n";
        box.value += name + " ";
        box.focus(); // すぐグラム数を打てるよう、入力欄にカーソルを移す
      });
      li.appendChild(btn);
      list.appendChild(li);
    }
  }
}

/** 記録フォームの送信：摂取量→残りを計算し、端末に保存して結果画面へ。 */
function handleRecordSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const data = loadProfileData();
  const targets = data.targets;

  const menuName = form.menu.value.trim() || "食事";
  const date = form.date.value.trim() || "(日付未入力)";
  let note = form.note.value.trim();

  // 食事テキストを [食品名, グラム] に変換。間違いは丁寧に知らせてやり直し。
  // （SPA＝1枚ページ方式なので、エラーでも入力内容はそのまま画面に残る）
  let items;
  try {
    items = parseMealText(form.meal.value);
  } catch (e) {
    flashNow(e.message, true);
    return;
  }
  if (items.length === 0) {
    flashNow("食べたものを1品以上入力してください。", true);
    return;
  }

  // ③ 摂取量の計算（知らない食品名はエラーで知らせる）
  let intake;
  try {
    intake = calculateIntake(items);
  } catch (e) {
    flashNow(e.message, true);
    return;
  }

  // ④ 残り許容量 ＝ 目標 − 実績
  const remaining = calculateRemaining(targets, intake);

  // 体重は未入力なら初期設定の値を使う（PC版と同じ扱い）
  const weightRaw = form.weight.value.trim();
  let weight = weightRaw === "" ? data.profile.weight : parseFloat(weightRaw);
  if (!Number.isFinite(weight)) weight = data.profile.weight;

  // ⑤ 保存。判定/備考が空ならカロリーの過不足を自動で添える。
  if (!note) note = remaining.kcal >= 0 ? "目標内" : "オーバー";
  appendRecord(date, weight, menuName, intake, targets, note);

  // 次の1食をすぐ入力できるよう、食事の内容だけ空に戻す（日付・体重は残す）
  form.menu.value = "";
  form.meal.value = "";
  form.note.value = "";

  lastDone = { menu: menuName, intake: intake, remaining: remaining };
  flashNext("記録しました。グラフはタブの「グラフ」から確認できます。");
  location.hash = "record-done";
}

/** 「記録しました」画面に、実績と残り許容量を流し込む。 */
function renderRecordDone() {
  const { menu, intake, remaining } = lastDone;
  document.getElementById("done-title").textContent = `記録しました：${menu}`;

  document.getElementById("done-kcal-in").textContent = `${fmt0(intake.kcal)} kcal`;
  document.getElementById("done-p-in").textContent = `${fmt1(intake.P)} g`;
  document.getElementById("done-f-in").textContent = `${fmt1(intake.F)} g`;
  document.getElementById("done-c-in").textContent = `${fmt1(intake.C)} g`;

  // 言い回しはPC版と同じ：「あと◯◯／◯◯オーバー」（Pだけ不足を強調）
  document.getElementById("done-kcal-rem").textContent =
    remaining.kcal >= 0 ? `あと ${fmt0(remaining.kcal)} kcal` : `${fmt0(-remaining.kcal)} kcal オーバー`;
  document.getElementById("done-p-rem").textContent =
    remaining.P > 0 ? `あと ${fmt1(remaining.P)} g` : `目標達成（${fmt1(-remaining.P)} g 超過）`;
  document.getElementById("done-f-rem").textContent =
    remaining.F >= 0 ? `あと ${fmt1(remaining.F)} g` : `${fmt1(-remaining.F)} g オーバー`;
  document.getElementById("done-c-rem").textContent =
    remaining.C >= 0 ? `あと ${fmt1(remaining.C)} g` : `${fmt1(-remaining.C)} g オーバー`;
}

// ---------------------------------------------------------------------
// 画面④：記録の一覧＋CSV入出力
// ---------------------------------------------------------------------
function renderRecordsView() {
  const records = loadRecords();
  const box = document.getElementById("records-container");

  if (records.length === 0) {
    box.innerHTML = '<p>まだ記録がありません。<a href="#record">食事を記録</a>してみましょう。</p>';
    return;
  }

  // 表を組み立てる（数値は表示の瞬間に丸める）
  let html = '<div class="table-wrap"><table><tr>' +
    '<th class="text">日付</th><th>体重</th><th class="text">メニュー</th>' +
    "<th>実績kcal</th><th>P</th><th>F</th><th>C</th>" +
    '<th>目標kcal</th><th>目標P</th><th class="text">判定/備考</th></tr>';
  for (const r of records) {
    html += "<tr>" +
      `<td class="text">${escapeHtml(r["日付"])}</td>` +
      `<td class="num">${r["体重"] === null ? "" : fmt1(r["体重"])}</td>` +
      `<td class="text">${escapeHtml(r["メニュー名"])}</td>` +
      `<td class="num">${fmt0(r["合計kcal"])}</td>` +
      `<td class="num">${fmt1(r["P(g)"])}</td>` +
      `<td class="num">${fmt1(r["F(g)"])}</td>` +
      `<td class="num">${fmt1(r["C(g)"])}</td>` +
      `<td class="num">${fmt0(r["目標kcal"])}</td>` +
      `<td class="num">${fmt1(r["目標P(g)"])}</td>` +
      `<td class="text">${escapeHtml(r["判定/備考"])}</td></tr>`;
  }
  html += "</table></div>" +
    `<p class="muted">全 ${records.length} 件。データはこの端末の中だけに保存されています。</p>`;
  box.innerHTML = html;
}

/** CSVエクスポート：記録を records.csv と同じ形式のファイルにして端末に保存する。 */
function handleExportCsv() {
  const records = loadRecords();
  if (records.length === 0) {
    flashNow("まだ記録がありません。先に食事を記録してください。");
    return;
  }
  // Blob＝メモリ上に作った“ファイルのもと”。それへのリンクを作って自動クリックする。
  const blob = new Blob([recordsToCsv(records)], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `digitore-records-${todayString()}.csv`;
  a.click();
  URL.revokeObjectURL(a.href); // 使い終わったリンクは片づける
}

/** CSVインポート：貼り付け（またはファイル選択）した中身で記録を置き換える。 */
function handleImportCsv() {
  const text = document.getElementById("import-text").value;
  if (!text.trim()) {
    flashNow("取り込むCSVを貼り付けるか、ファイルを選択してください。", true);
    return;
  }

  let records;
  try {
    records = csvToRecords(text);
  } catch (e) {
    flashNow(e.message, true);
    return;
  }

  // 置き換え＝今の記録が消える操作なので、実行前に必ず確認を取る
  const current = loadRecords().length;
  const ok = confirm(
    `${records.length}件の記録を取り込み、今この端末にある記録（${current}件）と置き換えます。よろしいですか？`
  );
  if (!ok) return;

  saveAllRecords(records);
  document.getElementById("import-text").value = "";
  flashNow(`${records.length}件の記録を取り込みました。`);
  renderRecordsView(); // 一覧をすぐ描き直す
}

// ---------------------------------------------------------------------
// 画面⑤：グラフ
// ---------------------------------------------------------------------
function renderChartsView() {
  const records = loadRecords(); // route() で「0件なら記録画面へ」誘導済み
  renderCalorieChart(document.getElementById("chart-calories"), records);
  renderProteinChart(document.getElementById("chart-protein"), records);
}

// ---------------------------------------------------------------------
// 起動処理：イベント（ボタンや画面切り替え）と部品をつなぐ
// ---------------------------------------------------------------------
document.getElementById("onboarding-form").addEventListener("submit", handleOnboardingSubmit);
document.getElementById("record-form").addEventListener("submit", handleRecordSubmit);
document.getElementById("export-csv").addEventListener("click", handleExportCsv);
document.getElementById("import-btn").addEventListener("click", handleImportCsv);

// CSVファイルを選んだら、その中身を貼り付け欄に読み込む（取り込み実行はボタンで）
document.getElementById("import-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader(); // ファイルの中身を読む道具
  reader.onload = () => { document.getElementById("import-text").value = reader.result; };
  reader.readAsText(file, "utf-8");
});

// ハッシュ（#record など）が変わったら画面を切り替える。開いた直後も1回実行。
window.addEventListener("hashchange", route);
route();

// ---------------------------------------------------------------------
// Service Worker（オフライン対応）の登録
// 一度開けば部品一式が端末に保存され、電波が無くても起動できるようになる。
// ---------------------------------------------------------------------
if ("serviceWorker" in navigator &&
    (location.protocol === "https:" || ["localhost", "127.0.0.1"].includes(location.hostname))) {
  navigator.serviceWorker.register("./sw.js");
}
