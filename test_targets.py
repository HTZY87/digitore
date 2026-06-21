# -*- coding: utf-8 -*-
"""
targets.py（目標値の計算エンジン）の自動テスト。

このファイルの目的：
  「結果を画面に出して人間が目で確かめる」のではなく、assert（＝「条件が
  成り立たなければその場でエラーを出して止める」命令）で合否を自動判定する。

使い方：
  python test_targets.py
  → 何もエラーが出ず「すべて合格」と表示されれば、全テスト合格。
  → 途中で AssertionError が出たら、その行の条件が崩れている（＝バグの疑い）。

（もとは test_strategies.py という名前で、digitore.py を対象にしていました。
  分割に合わせて targets.py を対象とする test_targets.py に改名しています）
"""

# targets.py から「計算関数」「換算係数」「戦略一覧」を借りてくる
from targets import calculate_daily_targets, KCAL_PER_GRAM, STRATEGIES


# =====================================================================
# テスト用の小さな部品
# =====================================================================

def approx_equal(a, b, tol=0.01):
    """
    2つの数 a と b が「ほぼ等しい」かを判定する。
    コンピュータの小数計算には極小の誤差がつきもの（例:0.1+0.2≠0.3）なので、
    == ではなく「差が tol（許容誤差）より小さければ等しいとみなす」で比べる。
    """
    return abs(a - b) < tol


# 共通のテスト人物（戦略だけ4通りに変えて比べる）
person = dict(
    gender="male",
    age=30,
    height=170,
    weight=70,
    activity_level=1.5,
    goal_offset=-500,
)


# =====================================================================
# テスト1：具体的な数値が想定どおりか（代表として③ダイエット特化を検証）
# =====================================================================
# 期待値は、SPECの式どおりに手計算で確かめた基準。
#   BMR  = 10*70 + 6.25*170 - 5*30 + 5      = 1617.5
#   TDEE = 1617.5 * 1.5                      = 2426.25
#   目標 = 2426.25 - 500                     = 1926.25
#   P = 1926.25*0.30/4, F = 1926.25*0.20/9, C = 1926.25*0.50/4

def test_diet_values():
    r = calculate_daily_targets(strategy="③ダイエット特化", **person)

    assert approx_equal(r["BMR"], 1617.5),         f"BMRが想定外: {r['BMR']}"
    assert approx_equal(r["TDEE"], 2426.25),       f"TDEEが想定外: {r['TDEE']}"
    assert approx_equal(r["Target Kcal"], 1926.25), f"目標kcalが想定外: {r['Target Kcal']}"
    assert approx_equal(r["P(g)"], 144.46875),     f"Pが想定外: {r['P(g)']}"
    assert approx_equal(r["F(g)"], 42.80555556),   f"Fが想定外: {r['F(g)']}"
    assert approx_equal(r["C(g)"], 240.78125),     f"Cが想定外: {r['C(g)']}"
    print("✓ テスト1：③ダイエット特化の数値は想定どおり")


# =====================================================================
# テスト2：全戦略で PFC のつじつまが合うか（P×4 + F×9 + C×4 ≒ 目標kcal）
# =====================================================================
# 配分の方法（percent/per_kg/remainder）が何であっても、グラムから逆算した
# カロリーは目標カロリーと（ほぼ）一致するはず。誤差が大きければ配分のバグ。

def test_all_strategies_balance():
    for strategy in STRATEGIES:
        r = calculate_daily_targets(strategy=strategy, **person)
        kcal_from_pfc = (
            r["P(g)"] * KCAL_PER_GRAM["P"]
            + r["F(g)"] * KCAL_PER_GRAM["F"]
            + r["C(g)"] * KCAL_PER_GRAM["C"]
        )
        assert approx_equal(kcal_from_pfc, r["Target Kcal"], tol=0.1), (
            f"{strategy}: PFC逆算{kcal_from_pfc:.1f} と 目標{r['Target Kcal']:.1f} がズレている"
        )
    print("✓ テスト2：全4戦略で PFC のカロリーが目標と一致")


# =====================================================================
# テスト3：おかしな入力はエラーで弾けるか（②性別検証の確認）
# =====================================================================
# 'male'/'female' 以外の性別を渡したら、黙って計算せず ValueError で
# 止まるのが正しい。ここでは「ちゃんとエラーが出ること」自体をテストする。

def test_invalid_gender_raises():
    raised = False  # エラーが出たかどうかの記録
    try:
        calculate_daily_targets(strategy="①ウェルネス", **{**person, "gender": "Male"})
    except ValueError:
        raised = True  # 想定どおりエラーが出た
    assert raised, "不正な性別 'Male' なのにエラーが出なかった"
    print("✓ テスト3：不正な性別は ValueError で弾ける")


# =====================================================================
# 実行：上のテストを順に呼び、最後まで来たら全部合格
# =====================================================================
if __name__ == "__main__":
    print("===== デジトレ 自動テスト開始 =====")
    test_diet_values()
    test_all_strategies_balance()
    test_invalid_gender_raises()
    print("===== すべて合格 🎉 =====")
