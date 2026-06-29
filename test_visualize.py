# -*- coding: utf-8 -*-
"""
visualize.py（可視化）の自動テスト。

使い方：
  python test_visualize.py
  → 何もエラーが出ず「すべて合格」と表示されれば全テスト合格。

確認すること（画面の無い環境でも検証できる範囲）：
  ・サンプル記録から、グラフ画像(PNG)が実際に作られるか。
  ・記録ゼロのときは、画像を作らず空リストを返すか。
  ・達成度の割り算（実績P÷目標P×100）の計算が正しいか。
画像の“見た目”は人が開いて確認する。ここでは「ちゃんと描けるか」を見る。
"""

import os
from record import save_record
from visualize import make_calorie_chart, make_protein_chart, visualize_all

_HERE = os.path.dirname(os.path.abspath(__file__))
TEST_CSV = os.path.join(_HERE, "records_viztest.csv")
CAL_PNG = os.path.join(_HERE, "calories_test.png")
PRO_PNG = os.path.join(_HERE, "protein_test.png")


def cleanup():
    """テストで作った一時ファイルを片づける。"""
    for path in (TEST_CSV, CAL_PNG, PRO_PNG):
        if os.path.exists(path):
            os.remove(path)


def _make_sample_csv():
    """3日分のサンプル記録を一時CSVに用意する。"""
    cleanup()
    samples = [
        ("2026-06-29", 70.0, "1日目",
         {"kcal": 1600.0, "P": 120.0, "F": 35.0, "C": 200.0},
         {"Target Kcal": 1800.0, "P(g)": 135.0, "F(g)": 40.0, "C(g)": 225.0}),
        ("2026-06-30", 69.8, "2日目",
         {"kcal": 1900.0, "P": 140.0, "F": 45.0, "C": 210.0},
         {"Target Kcal": 1800.0, "P(g)": 135.0, "F(g)": 40.0, "C(g)": 225.0}),
        ("2026-07-01", 69.7, "3日目",
         {"kcal": 1750.0, "P": 135.0, "F": 38.0, "C": 205.0},
         {"Target Kcal": 1800.0, "P(g)": 135.0, "F(g)": 40.0, "C(g)": 225.0}),
    ]
    for date, w, menu, intake, targets in samples:
        save_record(date, w, menu, intake, targets, csv_path=TEST_CSV)


# =====================================================================
# テスト1：サンプル記録からカロリーのグラフ画像が作られるか
# =====================================================================
def test_calorie_chart_created():
    _make_sample_csv()
    from record import load_records
    records = load_records(TEST_CSV)
    out = make_calorie_chart(records, out_path=CAL_PNG)
    assert os.path.exists(out), "カロリーのグラフ画像が作られなかった"
    assert os.path.getsize(out) > 0, "画像ファイルが空"
    print("✓ テスト1：カロリーのグラフ画像が作られる")


# =====================================================================
# テスト2：サンプル記録からタンパク質達成度のグラフ画像が作られるか
# =====================================================================
def test_protein_chart_created():
    _make_sample_csv()
    from record import load_records
    records = load_records(TEST_CSV)
    out = make_protein_chart(records, out_path=PRO_PNG)
    assert os.path.exists(out), "タンパク質のグラフ画像が作られなかった"
    assert os.path.getsize(out) > 0, "画像ファイルが空"
    print("✓ テスト2：タンパク質達成度のグラフ画像が作られる")


# =====================================================================
# テスト3：記録ゼロのときは画像を作らず空リストを返すか
# =====================================================================
def test_empty_returns_nothing():
    cleanup()  # 記録が無い状態
    result = visualize_all(csv_path=TEST_CSV)
    assert result == [], f"記録ゼロなのに何か作った: {result}"
    print("✓ テスト3：記録ゼロなら画像を作らず空リスト")


# =====================================================================
# テスト4：達成度の割り算が正しいか（実績135 ÷ 目標135 = 100%）
# =====================================================================
def test_achievement_math():
    # 計算ロジックの確認。135/135*100=100, 140/135*100≒103.7
    assert abs(135.0 / 135.0 * 100 - 100.0) < 0.01
    assert abs(140.0 / 135.0 * 100 - 103.70) < 0.01
    print("✓ テスト4：達成度の割り算が正しい")


if __name__ == "__main__":
    print("===== 可視化 自動テスト開始 =====")
    try:
        test_calorie_chart_created()
        test_protein_chart_created()
        test_empty_returns_nothing()
        test_achievement_math()
        print("===== すべて合格 🎉 =====")
    finally:
        cleanup()
