# -*- coding: utf-8 -*-
"""
intake.py（摂取量の計算）の自動テスト。

使い方：
  python test_intake.py
  → 何もエラーが出ず「すべて合格」と表示されれば全テスト合格。
  → AssertionError が出たら、その行の条件が崩れている（＝バグの疑い）。
"""

from intake import load_foods, calculate_intake


def approx_equal(a, b, tol=0.01):
    """2つの数がほぼ等しいか（小数の極小誤差を許して比べる）。"""
    return abs(a - b) < tol


# テスト全体で使う食品データを一度だけ読み込んでおく
FOODS = load_foods()


# =====================================================================
# テスト1：ちょうど100g なら、CSVの「100gあたりの値」とぴったり一致するはず
# =====================================================================
def test_exactly_100g():
    r = calculate_intake([("ごはん（精白米）", 100)], FOODS)
    assert approx_equal(r["kcal"], 156), f"kcal想定外: {r['kcal']}"
    assert approx_equal(r["P"], 2.5),    f"P想定外: {r['P']}"
    assert approx_equal(r["F"], 0.3),    f"F想定外: {r['F']}"
    assert approx_equal(r["C"], 37.1),   f"C想定外: {r['C']}"
    print("✓ テスト1：ちょうど100gはCSVの値と一致")


# =====================================================================
# テスト2：複数食品の合計が手計算と合うか
# =====================================================================
# ごはん200g（倍率2）＋ 卵50g（倍率0.5）
#   ごはん: kcal 156*2=312, P 2.5*2=5.0, F 0.3*2=0.6, C 37.1*2=74.2
#   卵    : kcal 142*0.5=71, P 12.2*0.5=6.1, F 10.2*0.5=5.1, C 0.4*0.5=0.2
#   合計  : kcal 383, P 11.1, F 5.7, C 74.4
def test_combined_meal():
    meal = [("ごはん（精白米）", 200), ("卵（全卵・生）", 50)]
    r = calculate_intake(meal, FOODS)
    assert approx_equal(r["kcal"], 383), f"kcal想定外: {r['kcal']}"
    assert approx_equal(r["P"], 11.1),   f"P想定外: {r['P']}"
    assert approx_equal(r["F"], 5.7),    f"F想定外: {r['F']}"
    assert approx_equal(r["C"], 74.4),   f"C想定外: {r['C']}"
    print("✓ テスト2：複数食品の合計が手計算と一致")


# =====================================================================
# テスト3：知らない食品名は ValueError で弾けるか
# =====================================================================
def test_unknown_food_raises():
    raised = False
    try:
        calculate_intake([("存在しない食品", 100)], FOODS)
    except ValueError:
        raised = True
    assert raised, "知らない食品名なのにエラーが出なかった"
    print("✓ テスト3：知らない食品名は ValueError で弾ける")


# =====================================================================
# テスト4：何も食べていない（空のリスト）なら合計はすべて0
# =====================================================================
def test_empty_meal():
    r = calculate_intake([], FOODS)
    assert r == {"kcal": 0.0, "P": 0.0, "F": 0.0, "C": 0.0}, f"空なのに0でない: {r}"
    print("✓ テスト4：何も食べていなければ合計は0")


if __name__ == "__main__":
    print("===== 摂取量計算 自動テスト開始 =====")
    test_exactly_100g()
    test_combined_meal()
    test_unknown_food_raises()
    test_empty_meal()
    print("===== すべて合格 🎉 =====")
