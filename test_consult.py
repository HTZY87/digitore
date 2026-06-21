# -*- coding: utf-8 -*-
"""
consult.py（食事コンサル＝残り許容量の計算）の自動テスト。

使い方：
  python test_consult.py
  → 何もエラーが出ず「すべて合格」なら全テスト合格。
"""

from consult import calculate_remaining


def approx_equal(a, b, tol=0.01):
    """2つの数がほぼ等しいか（小数の極小誤差を許して比べる）。"""
    return abs(a - b) < tol


# テスト用の「目標」と「実績」を手作りで用意する（他の計算には依存させない＝純粋に引き算だけ検証）
# 目標 targets は calculate_daily_targets と同じキー名にそろえる
TARGETS = {"Target Kcal": 2000.0, "P(g)": 150.0, "F(g)": 50.0, "C(g)": 250.0}


# =====================================================================
# テスト1：基本の引き算（目標 − 実績）が正しいか
# =====================================================================
# 実績が 目標の一部 のとき、残りは「目標 − 実績」になるはず。
def test_basic_remaining():
    intake = {"kcal": 1200.0, "P": 90.0, "F": 30.0, "C": 150.0}
    r = calculate_remaining(TARGETS, intake)
    assert approx_equal(r["kcal"], 800.0), f"kcal残り想定外: {r['kcal']}"
    assert approx_equal(r["P"], 60.0),     f"P残り想定外: {r['P']}"
    assert approx_equal(r["F"], 20.0),     f"F残り想定外: {r['F']}"
    assert approx_equal(r["C"], 100.0),    f"C残り想定外: {r['C']}"
    print("✓ テスト1：基本の残り許容量（目標−実績）が正しい")


# =====================================================================
# テスト2：食べ過ぎ（実績＞目標）なら残りはマイナスになるか
# =====================================================================
def test_over_eating_is_negative():
    intake = {"kcal": 2300.0, "P": 100.0, "F": 70.0, "C": 280.0}
    r = calculate_remaining(TARGETS, intake)
    assert r["kcal"] < 0, f"超過なのにkcalがマイナスでない: {r['kcal']}"
    assert approx_equal(r["kcal"], -300.0), f"超過kcal想定外: {r['kcal']}"
    assert approx_equal(r["F"], -20.0),     f"超過F想定外: {r['F']}"
    print("✓ テスト2：食べ過ぎは残りがマイナス（超過）で表せる")


# =====================================================================
# テスト3：まだ何も食べていない（実績ゼロ）なら、残り＝目標そのまま
# =====================================================================
def test_nothing_eaten_equals_targets():
    intake = {"kcal": 0.0, "P": 0.0, "F": 0.0, "C": 0.0}
    r = calculate_remaining(TARGETS, intake)
    assert approx_equal(r["kcal"], TARGETS["Target Kcal"]), f"kcal想定外: {r['kcal']}"
    assert approx_equal(r["P"], TARGETS["P(g)"]),           f"P想定外: {r['P']}"
    print("✓ テスト3：何も食べていなければ残り＝目標そのまま")


if __name__ == "__main__":
    print("===== 食事コンサル 自動テスト開始 =====")
    test_basic_remaining()
    test_over_eating_is_negative()
    test_nothing_eaten_equals_targets()
    print("===== すべて合格 🎉 =====")
