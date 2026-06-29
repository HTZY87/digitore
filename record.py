# -*- coding: utf-8 -*-
"""
デジトレ 記録（機能⑤）

このファイルは「1日分のデータをファイルに残す担当」です。
食べた実績（③intake）と、その日の目標（②targets）などを
records.csv に1行ずつ書きためていく。あとで段階⑥（可視化）が
このCSVを読んでグラフにする。

設計方針（SPEC §7）：
  ・保存先は records.csv（中身を目で見られる・コードが簡単）。
  ・1日分＝1行。列は決まった順番で並べる（下の COLUMNS を参照）。
  ・数値は丸めずそのまま保存する（丸めるのは表示・グラフ側の役目）。
  ・CSVの場所は __file__ 基準で決める（どこから実行しても見つけられる）。

くわしい仕様は SPEC.md（第7章）を参照してください。
"""

import sys
import os
import csv  # Python標準の「CSVファイルを読み書きする道具箱」

# Windowsの画面で日本語が文字化けしないように出力をUTF-8にする。
# （他ファイル先頭と同じおまじない。単体で動かす時のために入れておく）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# このファイルがある場所を基準に records.csv の場所を決める。
# こうしておくと、どの作業フォルダから実行してもCSVを見つけられる。
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RECORDS_CSV = os.path.join(_HERE, "records.csv")

# CSVの列の見出しと並び順（ここを“1か所の決まりごと”にしておく）。
# 保存も読み込みも、このリストを基準にすればズレない。
COLUMNS = [
    "日付", "体重", "メニュー名",
    "合計kcal", "P(g)", "F(g)", "C(g)",
    "目標kcal", "目標P(g)",
    "判定/備考",
]

# どの列が「数値」か（読み込み時に float() へ変換する対象）。
# 日付・メニュー名・判定/備考は文字のまま扱う。
_NUMERIC_COLUMNS = ["体重", "合計kcal", "P(g)", "F(g)", "C(g)", "目標kcal", "目標P(g)"]


# =====================================================================
# 1. 記録の保存（1日分を1行 追記する）
# =====================================================================

def save_record(date, weight, menu, intake, targets, note="",
                csv_path=DEFAULT_RECORDS_CSV):
    """
    1日分の記録を records.csv に1行 追記する。

    引数:
        date    : 日付の文字列（例 "2026-06-29"）
        weight  : その日の体重(kg)
        menu    : メニュー名（例 "鶏むね定食"）。食べた内容の呼び名。
        intake  : ③calculate_intake が返す実績の辞書（kcal/P/F/C）
        targets : ②calculate_daily_targets が返す目標の辞書
        note    : 判定や備考の文字列（省略可）
        csv_path: 保存先（省略すると records.csv）
    """
    # ファイルがまだ無い／中身が空なら、先に見出し行を書く必要がある。
    # （os.path.exists=ある？  os.path.getsize=中身の大きさが0でない？）
    need_header = (not os.path.exists(csv_path)) or os.path.getsize(csv_path) == 0

    # 列の決まり順（COLUMNS）どおりに、今回の1行ぶんの値を組み立てる。
    row = {
        "日付": date,
        "体重": weight,
        "メニュー名": menu,
        "合計kcal": intake["kcal"],
        "P(g)": intake["P"],
        "F(g)": intake["F"],
        "C(g)": intake["C"],
        "目標kcal": targets["Target Kcal"],
        "目標P(g)": targets["P(g)"],
        "判定/備考": note,
    }

    # "a"（append＝追記）で開く。既にある記録を消さず、末尾に足していく。
    # newline="" は CSV を書くときの定番のお作法（余計な空行を防ぐ）。
    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if need_header:
            writer.writeheader()      # 1行目に見出しを書く（初回だけ）
        writer.writerow(row)          # 今日の記録を1行 追記


# =====================================================================
# 2. 記録の読み込み（段階⑥の可視化が使う）
# =====================================================================

def load_records(csv_path=DEFAULT_RECORDS_CSV):
    """
    records.csv を読み、1行＝1辞書のリストにして返す。

    返す形（イメージ）:
        [
          {"日付": "2026-06-29", "体重": 70.0, "合計kcal": 1234.5, ...},
          ...
        ]
    数値の列は float() に変換して返す（グラフ計算でそのまま使えるように）。
    まだファイルが無いときは空リスト [] を返す（記録ゼロを素直に表す）。
    """
    if not os.path.exists(csv_path):
        return []  # まだ一度も保存していない → 記録ゼロ

    records = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 数値の列だけ float() に直す。中身が空のセルは None にしておく
            # （後でグラフ側が「値なし」を判別できるように）。
            for col in _NUMERIC_COLUMNS:
                value = row.get(col, "")
                row[col] = float(value) if value not in (None, "") else None
            records.append(row)

    return records


# =====================================================================
# 動作確認用（このファイルを直接実行したときだけ動く）
# =====================================================================
if __name__ == "__main__":
    # 他の担当から借りてきて、実際の流れで1件 保存してみる。
    from targets import calculate_daily_targets   # ② 目標
    from intake import calculate_intake           # ③ 実績

    targets = calculate_daily_targets(
        gender="male", age=30, height=170, weight=70,
        activity_level=1.5, goal_offset=-500, strategy="③ダイエット特化",
    )
    eaten = calculate_intake([
        ("ごはん（精白米）", 200),
        ("鶏むね肉（皮なし・生）", 150),
        ("卵（全卵・生）", 50),
    ])

    # 動作確認では本物の records.csv を汚さないよう、お試し用ファイルに書く。
    demo_csv = os.path.join(_HERE, "records_demo.csv")
    save_record(
        date="2026-06-29", weight=70, menu="鶏むね定食",
        intake=eaten, targets=targets, note="目標内", csv_path=demo_csv,
    )
    print("===== 記録を1件 保存しました（お試し用ファイル） =====")
    print(f" 保存先: {demo_csv}")
    print("-------------------------------------------")
    for rec in load_records(demo_csv):
        print(f" {rec['日付']} / {rec['メニュー名']} / "
              f"実績{rec['合計kcal']:.0f}kcal ・ 目標{rec['目標kcal']:.0f}kcal")
    print("===========================================")
