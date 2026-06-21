# -*- coding: utf-8 -*-
"""
デジトレ 計算エンジン：目標値の計算（機能②）

このファイルは「1日に取るべきカロリー・PFC（タンパク質P・脂質F・炭水化物C）の
目標値」を計算する、デジトレの心臓部です。
（もとは digitore.py という名前でした。中身を表す targets.py に改名しています）

設計方針：
  ・計算はすべてこのコードで行う（AIの暗算に頼らない＝毎回同じ結果でブレない）。
  ・「将来調整しうる数値（戦略の比率など）」は、ロジックに直書きせず
    “データ”としてファイル先頭にまとめる（＝関心の分離。後から増やしやすい）。
  ・エンジンは丸めず正確な数値を返す（丸めるのは表示する側の役目）。

くわしい仕様は同じフォルダの SPEC.md（第4章）を参照してください。
"""

import sys

# Windowsの画面（コンソール）は初期設定だと日本語用の古い文字コードで表示しようとし、
# Python が出す UTF-8 と食い違って文字化けすることがある。
# そこで「画面への出力は UTF-8 で」と最初に宣言して、文字化けを防ぐ。
# （reconfigure は Python 3.7 以降の機能。無い古い環境では何もしない＝安全）
# ★このファイルは main.py や test から最初に読み込まれるので、ここで設定すれば
#   アプリ全体で文字化けを防げる。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# =====================================================================
# 設定データ（ここの数値を変えれば挙動が変わる。ロジックは触らなくてよい）
# =====================================================================

# カロリー換算係数：栄養素1gあたりのkcal。栄養学で決まった固定値。
#   タンパク質P=4、脂質F=9、炭水化物C=4 kcal/g
KCAL_PER_GRAM = {"P": 4, "F": 9, "C": 4}

# PFC戦略の定義（データ）。
# 各栄養素を「計算方法」と「値」のペア（タプル）で持つ。
#   計算方法 method の意味:
#     "percent"   : 目標カロリーの割合で決める（値 0.15 = 15%）
#     "per_kg"    : 体重1kgあたりのグラム数で決める（値 1.2 など）
#     "remainder" : 残ったカロリーを全部わりあてる（値は使わないので None）
#
#  ★戦略を増やしたいときは、この辞書に1行足すだけ。下のロジックは変更不要。
STRATEGIES = {
    "①ウェルネス":     {"P": ("percent", 0.15), "F": ("percent", 0.25), "C": ("percent", 0.60)},
    "②ヘルスケア":     {"P": ("per_kg", 1.2),   "F": ("percent", 0.25), "C": ("remainder", None)},
    "③ダイエット特化": {"P": ("percent", 0.30), "F": ("percent", 0.20), "C": ("percent", 0.50)},
    "④筋肥大・競技者": {"P": ("per_kg", 2.0),   "F": ("percent", 0.20), "C": ("remainder", None)},
}


# =====================================================================
# ロジック（計算の手順。ここは戦略が増えても基本そのまま）
# =====================================================================

def _grams_for_macro(method, value, macro, target_kcal, weight, used_kcal):
    """
    1つの栄養素（P か F か C）のグラム数を、指定された「方法」で計算する小さな部品。
    関数名の先頭の _ は「このファイル内部用の補助関数」という慣習的な目印。

    引数:
        method     : 計算方法 "percent" / "per_kg" / "remainder"
        value      : その方法で使う数値（remainder のときは None）
        macro      : 栄養素の記号 "P" / "F" / "C"
        target_kcal: 1日の目標カロリー
        weight     : 体重(kg)
        used_kcal  : すでに他の栄養素で使ったカロリー（remainderの計算に使う）
    戻り値:
        その栄養素のグラム数
    """
    factor = KCAL_PER_GRAM[macro]  # この栄養素の 1gあたりkcal（P/C=4, F=9）

    if method == "percent":
        # 目標カロリーの割合(value) ÷ 1gあたりkcal → グラム数
        return (target_kcal * value) / factor
    elif method == "per_kg":
        # 体重 × 係数(value) → グラム数（カロリーは使わない）
        return weight * value
    elif method == "remainder":
        # 残りカロリー（目標 − すでに使った分）÷ 1gあたりkcal → グラム数
        return (target_kcal - used_kcal) / factor
    else:
        # 想定外の方法名が来たら、原因がすぐ分かるようにエラーで知らせる
        raise ValueError(f"未知の計算方法です: {method}")


def calculate_daily_targets(gender, age, height, weight, activity_level, goal_offset, strategy):
    """
    体の情報から、1日の目標カロリーとPFC（グラム数）を計算して返す関数。

    引数（＝この関数に渡す材料）:
        gender        : 性別 'male'（男性）/ 'female'（女性）
        age           : 年齢（歳）
        height        : 身長（cm）
        weight        : 現在の体重（kg）
        activity_level: 生活活動強度 1.2（低い）〜 1.9（高い）
        goal_offset   : 目的によるカロリー増減（減量 -500 など、維持 0、増量 +250 など）
        strategy      : PFC戦略の名前（STRATEGIES のキーのどれか）
    戻り値:
        BMR・TDEE・目標カロリー・P・F・C をまとめた辞書
    """

    # --- 性別が正しいか先に確認 ---
    # 'male' / 'female' 以外（打ち間違いなど）は、黙って女性扱いにせず
    # エラーで止めて知らせる。間違ったまま計算が進むのを防ぐため。
    if gender not in ("male", "female"):
        raise ValueError(f"未知の性別です: {gender} / 選べるのは 'male' か 'female'")

    # --- 戦略名が正しいか先に確認（打ち間違いなどをすぐ気づけるように）---
    if strategy not in STRATEGIES:
        raise ValueError(f"未知の戦略です: {strategy} / 選べるのは {list(STRATEGIES.keys())}")

    # === 1. BMR（基礎代謝量＝何もしなくても消費するカロリー）===
    # Mifflin-St Jeor 式。広く使われる確立した式なので、係数はそのまま使う。
    # 性別で最後に足す数だけ変わる（男性 +5 / 女性 -161）。
    # 上で male/female を検証済みなので、ここは安心して二択にできる。
    s = 5 if gender == "male" else -161
    bmr = 10 * weight + 6.25 * height - 5 * age + s

    # === 2. TDEE（総消費カロリー）と 目標カロリー ===
    tdee = bmr * activity_level          # 活動量を反映した実際の1日消費
    target_kcal = tdee + goal_offset     # 目的の増減を足したものが目標

    # === 3. 戦略データを読んで P・F・C のグラム数を計算 ===
    rule = STRATEGIES[strategy]          # 選ばれた戦略の定義を取り出す
    used_kcal = 0                        # ここまでに使ったカロリーの合計
    grams = {}                           # 計算結果を入れる箱（P/F/Cのグラム）

    # P → F → C の順で計算する。
    # （C が "remainder" の戦略があるため、先に P と F を確定させる必要がある）
    for macro in ("P", "F", "C"):
        method, value = rule[macro]      # その栄養素の「方法」と「値」
        g = _grams_for_macro(method, value, macro, target_kcal, weight, used_kcal)
        grams[macro] = g
        used_kcal += g * KCAL_PER_GRAM[macro]  # 使ったカロリーを足していく

    # === 4. 結果を辞書にまとめて返す ===
    # ここでは“丸めない”（＝正確な数値のまま返す）のが大事なポイント。
    # 丸めた数字を後の計算（摂取量・残り許容量など）に使うと誤差が積み重なるため、
    # 丸めるのは「画面に見せる瞬間」だけにする（＝計算と表示の責任を分ける）。
    return {
        "BMR": bmr,
        "TDEE": tdee,
        "Target Kcal": target_kcal,
        "P(g)": grams["P"],
        "F(g)": grams["F"],
        "C(g)": grams["C"],
    }


# =====================================================================
# 動作確認用（このファイルを直接実行したときだけ動く）
# =====================================================================
# 下の if 文は「python targets.py と直接動かしたときだけ中を実行」という意味。
# 他のファイルが calculate_daily_targets を借りるときは動かない（じゃまをしない）。
if __name__ == "__main__":
    # テスト用の人物：30歳・男性・170cm・70kg・活動やや高め・1日500kcal減量・ダイエット特化
    result = calculate_daily_targets(
        gender="male",
        age=30,
        height=170,
        weight=70,
        activity_level=1.5,
        goal_offset=-500,
        strategy="③ダイエット特化",
    )

    # 結果を見やすい表っぽい形で画面に表示する。
    # エンジンは丸めず正確な数値を返すので、“見せる瞬間”にここで丸める。
    #   :.1f = 小数第1位まで表示 ／ :.0f = 整数で表示
    print("===== デジトレ 目標値の計算結果（テスト） =====")
    print(f" BMR（基礎代謝量）  : {result['BMR']:.1f} kcal")
    print(f" TDEE（総消費）     : {result['TDEE']:.1f} kcal")
    print(f" 目標カロリー       : {result['Target Kcal']:.0f} kcal")
    print("-------------------------------------------")
    print(f" P タンパク質       : {result['P(g)']:.1f} g")
    print(f" F 脂質             : {result['F(g)']:.1f} g")
    print(f" C 炭水化物         : {result['C(g)']:.1f} g")
    print("===========================================")
