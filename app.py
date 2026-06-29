# -*- coding: utf-8 -*-
"""
デジトレ Web版の入口（機能⑦：見た目／UI）

このファイルは「ブラウザで使えるようにする司令塔」です。
ターミナル版の main.py と同じ考え方で、自分では計算せず、
各担当ファイルから関数を借りてきて、画面（HTML）とつなぐだけ。

  動かし方：  python app.py
  → 画面に出るアドレス（http://127.0.0.1:5000/）をブラウザで開く。

役割分担（どのファイルが何をするか）：
  ・targets.py   … ② 目標カロリー・PFCの計算
  ・intake.py    … ③ 食べたものの合計（foods.csv）
  ・consult.py   … ④ 残り許容量（目標 − 実績）
  ・record.py    … ⑤ records.csv への保存・読み込み
  ・visualize.py … ⑥ 記録をグラフ画像にする
  ・safety.py    … ⑥(警告) 設定が極端すぎないか判定

設計の核（SPEC §0）：計算・記録は「本物のコード」、画面はここ（app.py）が担当する。
  → このファイルは“つなぐ”だけ。計算ロジックは各担当に置いたままにする。
"""

import os
import json

from flask import Flask, render_template, request, redirect, url_for, flash

# 各担当から必要な関数を借りてくる（計算・記録・可視化の本体には触らない）。
from targets import calculate_daily_targets        # ② 目標
from intake import load_foods, calculate_intake    # ③ 実績
from consult import calculate_remaining            # ④ 残り
from record import save_record, load_records       # ⑤ 記録
from safety import evaluate_safety                 # ⑥ 安全判定（計算のみ）
from visualize import make_calorie_chart, make_protein_chart  # ⑥ グラフ

_HERE = os.path.dirname(os.path.abspath(__file__))

# 最新のプロフィール（初期設定の内容）と計算済み目標を残すファイル。
# こうしておけば、ブラウザを閉じても次に開いたとき目標が残っている。
PROFILE_JSON = os.path.join(_HERE, "profile.json")

# グラフ画像はブラウザから読めるよう static フォルダに出す。
STATIC_DIR = os.path.join(_HERE, "static")

app = Flask(__name__)
# flash（画面上の一言メッセージ）に必要な合言葉。ローカル利用なので固定でよい。
app.secret_key = "digitore-local-secret"


# =====================================================================
# プロフィール（初期設定の内容＋目標）の保存・読み込み
# =====================================================================

def save_profile(profile, targets):
    """初期設定の内容と、その計算結果（目標）を profile.json に保存する。"""
    data = {"profile": profile, "targets": targets}
    with open(PROFILE_JSON, "w", encoding="utf-8") as f:
        # ensure_ascii=False で日本語をそのまま読める形で保存する。
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_profile():
    """profile.json を読む。まだ初期設定していなければ None を返す。"""
    if not os.path.exists(PROFILE_JSON):
        return None
    with open(PROFILE_JSON, encoding="utf-8") as f:
        return json.load(f)


# =====================================================================
# 食事入力のテキストを (食品名, グラム) のリストに変換する小さな部品
# =====================================================================

def parse_meal_text(text):
    """
    食事入力欄のテキストを (食品名, グラム) のリストに直す。
    1行に1品。区切りはカンマでも空白でもよい（例：「ごはん（精白米） 200」）。
    空行は無視する。数字に直せない行はエラーで知らせる。
    """
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # カンマがあればカンマで、無ければ空白で「食品名」と「量」に分ける。
        if "," in line:
            name, _, grams = line.partition(",")
        else:
            name, _, grams = line.rpartition(" ")
        name = name.strip()
        grams = grams.strip()
        if not name or not grams:
            raise ValueError(f"「{line}」は『食品名 グラム』の形で入力してください。")
        try:
            grams_value = float(grams)
        except ValueError:
            raise ValueError(f"「{line}」の量を数字にできません。")
        items.append((name, grams_value))
    return items


# =====================================================================
# 画面①：トップ（メニュー）
# =====================================================================

@app.route("/")
def index():
    # 初期設定が済んでいるかどうかで、案内の出し方を変える。
    data = load_profile()
    return render_template("index.html", data=data)


# =====================================================================
# 画面②：初期設定（オンボーディング）→ 目標を計算して表示
# =====================================================================

@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if request.method == "GET":
        # 入力フォームを見せる（選択肢はターミナル版 dialogue.py と同じ並び）。
        return render_template("onboarding.html")

    # --- ここから送信(POST)の処理 ---
    try:
        profile = {
            "gender": request.form["gender"],
            "age": int(request.form["age"]),
            "height": float(request.form["height"]),
            "weight": float(request.form["weight"]),
            "activity_level": float(request.form["activity_level"]),
            "goal_offset": int(request.form["goal_offset"]),
            "strategy": request.form["strategy"],
        }
    except (KeyError, ValueError):
        flash("入力に不備があります。すべての項目を正しく入れてください。")
        return redirect(url_for("onboarding"))

    # ② 目標の計算はエンジンに依頼（性別が変なら ValueError が飛ぶ）。
    try:
        targets = calculate_daily_targets(**profile)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("onboarding"))

    # ⑥ 安全判定（計算のみ）。極端な設定なら結果画面で警告を出す。
    safety = evaluate_safety(profile["weight"], profile["goal_offset"])

    # 次回も使えるよう保存しておく。
    save_profile(profile, targets)

    return render_template("result.html", profile=profile,
                           targets=targets, safety=safety)


# =====================================================================
# 画面③：食事を記録（③摂取量 → ④残り → ⑤保存 を1画面で）
# =====================================================================

@app.route("/record", methods=["GET", "POST"])
def record():
    data = load_profile()
    # 目標が無いと「残り」を出せないので、まず初期設定へ案内する。
    if data is None:
        flash("先に初期設定をして、1日の目標を決めましょう。")
        return redirect(url_for("onboarding"))

    targets = data["targets"]
    # 入力の参考になるよう、登録済みの食品名一覧を画面に渡す。
    food_names = sorted(load_foods().keys())

    if request.method == "GET":
        return render_template("record.html", food_names=food_names,
                               profile=data["profile"])

    # --- 送信(POST)の処理 ---
    meal_text = request.form.get("meal", "")
    menu_name = request.form.get("menu", "").strip() or "食事"
    weight_raw = request.form.get("weight", "").strip()
    date = request.form.get("date", "").strip()
    note = request.form.get("note", "").strip()

    # 食事テキストを (食品名, グラム) に変換。間違いは丁寧に知らせて戻す。
    try:
        items = parse_meal_text(meal_text)
    except ValueError as e:
        flash(str(e))
        return render_template("record.html", food_names=food_names,
                               profile=data["profile"])
    if not items:
        flash("食べたものを1品以上入力してください。")
        return render_template("record.html", food_names=food_names,
                               profile=data["profile"])

    # ③ 摂取量の計算（知らない食品名は ValueError）。
    try:
        intake = calculate_intake(items)
    except ValueError as e:
        flash(str(e))
        return render_template("record.html", food_names=food_names,
                               profile=data["profile"])

    # ④ 残り許容量 ＝ 目標 − 実績。
    remaining = calculate_remaining(targets, intake)

    # 体重は未入力なら初期設定の値を使う。
    try:
        weight = float(weight_raw) if weight_raw else data["profile"]["weight"]
    except ValueError:
        weight = data["profile"]["weight"]

    # ⑤ records.csv に保存。判定/備考が空ならカロリーの過不足を自動で添える。
    if not note:
        note = "目標内" if remaining["kcal"] >= 0 else "オーバー"
    save_record(date or "(日付未入力)", weight, menu_name,
                intake, targets, note=note)

    flash("記録しました。グラフはメニューの「グラフを見る」から確認できます。")
    return render_template("record_done.html", menu=menu_name, intake=intake,
                           remaining=remaining, targets=targets)


# =====================================================================
# 画面④：記録の一覧（保存した records.csv を表で見る）
# =====================================================================

@app.route("/records")
def records():
    rows = load_records()
    return render_template("records.html", rows=rows)


# =====================================================================
# 画面⑤：グラフを見る（記録から画像を作って表示）
# =====================================================================

@app.route("/charts")
def charts():
    rows = load_records()
    if not rows:
        flash("まだ記録がありません。先に食事を記録してください。")
        return redirect(url_for("record"))

    # 画像は static フォルダに出して、ブラウザから読み込めるようにする。
    os.makedirs(STATIC_DIR, exist_ok=True)
    cal_png = os.path.join(STATIC_DIR, "calories.png")
    pro_png = os.path.join(STATIC_DIR, "protein.png")
    make_calorie_chart(rows, out_path=cal_png)
    make_protein_chart(rows, out_path=pro_png)

    # url_for で画像のアドレスを作る（キャッシュ対策に件数を付ける）。
    version = len(rows)
    return render_template(
        "charts.html",
        calorie_url=url_for("static", filename="calories.png", v=version),
        protein_url=url_for("static", filename="protein.png", v=version),
    )


if __name__ == "__main__":
    # ローカル（自分のPC）で使う前提の起動。
    #   host=127.0.0.1 … 自分のPCからだけアクセスできる（外には公開しない＝安全）。
    #   debug=True     … 入力ミスや不具合の原因が画面に出て直しやすい。
    print("ブラウザで http://127.0.0.1:5000/ を開いてください。")
    app.run(host="127.0.0.1", port=5000, debug=True)
