# -*- coding: utf-8 -*-
"""
record.py（記録）の自動テスト。

使い方：
  python test_record.py
  → 何もエラーが出ず「すべて合格」と表示されれば全テスト合格。
  → AssertionError が出たら、その行の条件が崩れている（＝バグの疑い）。

注意：テストでは本物の records.csv を汚さないよう、
      お試し用の一時ファイルに書き込み、最後に片づける（消す）。
"""

import os
from record import save_record, load_records, COLUMNS

# テスト専用のCSV（本番の records.csv とは別名にして混ざらないようにする）
_HERE = os.path.dirname(os.path.abspath(__file__))
TEST_CSV = os.path.join(_HERE, "records_test.csv")


def approx_equal(a, b, tol=0.01):
    """2つの数がほぼ等しいか（小数の極小誤差を許して比べる）。"""
    return abs(a - b) < tol


def cleanup():
    """テスト用CSVが残っていたら消して、まっさらな状態から始める。"""
    if os.path.exists(TEST_CSV):
        os.remove(TEST_CSV)


# テストで使い回す、ダミーの実績と目標（計算は他ファイルの担当なのでここでは固定値）
INTAKE = {"kcal": 1234.5, "P": 80.1, "F": 30.2, "C": 150.3}
TARGETS = {"Target Kcal": 1800.0, "P(g)": 135.0, "F(g)": 40.0, "C(g)": 225.0}


# =====================================================================
# テスト1：保存して読み戻すと、書いた値がそのまま取り出せるか
# =====================================================================
def test_save_and_load():
    cleanup()
    save_record("2026-06-29", 70.0, "鶏むね定食",
                INTAKE, TARGETS, note="目標内", csv_path=TEST_CSV)

    records = load_records(TEST_CSV)
    assert len(records) == 1, f"1件のはずが {len(records)} 件"

    r = records[0]
    assert r["日付"] == "2026-06-29",  f"日付がズレた: {r['日付']}"
    assert r["メニュー名"] == "鶏むね定食", f"メニュー名がズレた: {r['メニュー名']}"
    assert approx_equal(r["合計kcal"], 1234.5), f"実績kcalがズレた: {r['合計kcal']}"
    assert approx_equal(r["目標kcal"], 1800.0), f"目標kcalがズレた: {r['目標kcal']}"
    assert approx_equal(r["目標P(g)"], 135.0),  f"目標Pがズレた: {r['目標P(g)']}"
    assert r["判定/備考"] == "目標内",   f"備考がズレた: {r['判定/備考']}"
    print("✓ テスト1：保存→読み戻しで値が一致")


# =====================================================================
# テスト2：初回保存で見出し行（ヘッダ）が自動で付くか
# =====================================================================
def test_header_written():
    cleanup()
    save_record("2026-06-29", 70.0, "朝食",
                INTAKE, TARGETS, csv_path=TEST_CSV)

    # CSVの1行目を直接読んで、見出しが COLUMNS と一致するか確かめる
    with open(TEST_CSV, encoding="utf-8") as f:
        first_line = f.readline().strip()
    expected = ",".join(COLUMNS)
    assert first_line == expected, f"ヘッダが想定外: {first_line}"
    print("✓ テスト2：初回保存で見出し行が自動で付く")


# =====================================================================
# テスト3：続けて保存すると、記録が消えずに増えていくか（追記）
# =====================================================================
def test_append_grows():
    cleanup()
    save_record("2026-06-29", 70.0, "1日目", INTAKE, TARGETS, csv_path=TEST_CSV)
    save_record("2026-06-30", 69.8, "2日目", INTAKE, TARGETS, csv_path=TEST_CSV)
    save_record("2026-07-01", 69.7, "3日目", INTAKE, TARGETS, csv_path=TEST_CSV)

    records = load_records(TEST_CSV)
    assert len(records) == 3, f"3件のはずが {len(records)} 件"
    # 順番も保たれているか（追記なので入れた順に並ぶ）
    assert records[0]["メニュー名"] == "1日目"
    assert records[2]["メニュー名"] == "3日目"
    print("✓ テスト3：続けて保存すると記録が増える（追記）")


# =====================================================================
# テスト4：まだ一度も保存していなければ、読み込みは空リスト
# =====================================================================
def test_load_missing_returns_empty():
    cleanup()  # ファイルが無い状態にする
    records = load_records(TEST_CSV)
    assert records == [], f"記録ゼロなのに空でない: {records}"
    print("✓ テスト4：記録が無ければ空リストを返す")


if __name__ == "__main__":
    print("===== 記録 自動テスト開始 =====")
    try:
        test_save_and_load()
        test_header_written()
        test_append_grows()
        test_load_missing_returns_empty()
        print("===== すべて合格 🎉 =====")
    finally:
        # 合否にかかわらず、最後にテスト用CSVを片づける（散らかさない）
        cleanup()
