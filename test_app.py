# -*- coding: utf-8 -*-
"""
app.py（Web版の入口）の自動テスト。

Flask の「テスト用クライアント」を使うので、本物のサーバを起動しなくても
各画面（URL）をたたいて確認できる。

使い方：
  python test_app.py
  → 何もエラーが出ず「すべて合格」と表示されれば全テスト合格。

安全のための工夫：
  テストは profile.json / records.csv を書き換えてしまうため、
  実行前に本物を退避（バックアップ）し、終わったら元に戻す。
  （CLAUDE.md の「削除は退避で」の考え方に合わせ、本物のデータを壊さない）
"""

import os
import shutil

import app as appmod
from record import DEFAULT_RECORDS_CSV
from app import PROFILE_JSON

# 退避（バックアップ）する本物ファイルの一覧
_TARGETS = [PROFILE_JSON, DEFAULT_RECORDS_CSV]
_backups = {}


def backup_real_files():
    """本物の profile.json / records.csv があれば .testbak に退避する。"""
    for path in _TARGETS:
        if os.path.exists(path):
            bak = path + ".testbak"
            shutil.move(path, bak)
            _backups[path] = bak


def restore_real_files():
    """テストで作ったファイルを消し、退避した本物を元に戻す。"""
    for path in _TARGETS:
        if os.path.exists(path):
            os.remove(path)  # テスト中に作られたものを片づける
        if path in _backups:
            shutil.move(_backups[path], path)  # 本物を戻す


# Flask のテスト用クライアント（ブラウザの代わり）
client = appmod.app.test_client()


# =====================================================================
# テスト1：トップページが表示できるか
# =====================================================================
def test_index_ok():
    res = client.get("/")
    assert res.status_code == 200, f"トップが開けない: {res.status_code}"
    assert "デジトレ".encode() in res.data, "トップに見出しが無い"
    print("✓ テスト1：トップページが表示できる")


# =====================================================================
# テスト2：初期設定を送ると目標が計算され、profile.json が作られるか
# =====================================================================
def test_onboarding_creates_profile():
    res = client.post("/onboarding", data={
        "gender": "male", "age": "30", "height": "170", "weight": "70",
        "activity_level": "1.5", "goal_offset": "-500",
        "strategy": "③ダイエット特化",
    })
    assert res.status_code == 200, f"初期設定の送信に失敗: {res.status_code}"
    assert "目標カロリー".encode() in res.data, "結果画面に目標が出ていない"
    assert os.path.exists(PROFILE_JSON), "profile.json が作られていない"
    print("✓ テスト2：初期設定→目標計算→profile.json 作成")


# =====================================================================
# テスト3：食事を記録すると、残り許容量が表示され records.csv に保存されるか
# =====================================================================
def test_record_saves():
    # テスト2で profile.json が出来ている前提（順番に実行する）
    res = client.post("/record", data={
        "date": "2026-06-29",
        "weight": "70",
        "menu": "鶏むね定食",
        "meal": "ごはん（精白米） 200\n鶏むね肉（皮なし・生） 150\n卵（全卵・生） 50",
        "note": "",
    })
    assert res.status_code == 200, f"記録の送信に失敗: {res.status_code}"
    assert "残り許容量".encode() in res.data, "残り許容量が表示されていない"
    assert os.path.exists(DEFAULT_RECORDS_CSV), "records.csv が作られていない"
    print("✓ テスト3：食事記録→残り表示→records.csv 保存")


# =====================================================================
# テスト4：知らない食品名は、エラーメッセージで丁寧に知らせるか
# =====================================================================
def test_unknown_food_message():
    res = client.post("/record", data={
        "menu": "テスト", "meal": "存在しない食品 100", "note": "",
    })
    assert res.status_code == 200, "エラーでも画面は返すべき"
    assert "食品データにありません".encode() in res.data, "未知食品の案内が出ていない"
    print("✓ テスト4：知らない食品名は丁寧に知らせる")


# =====================================================================
# テスト5：記録一覧・グラフの画面が表示できるか
# =====================================================================
def test_records_and_charts():
    res = client.get("/records")
    assert res.status_code == 200, "記録一覧が開けない"
    assert "鶏むね定食".encode() in res.data, "一覧に記録が出ていない"

    # グラフ画面（記録が1件以上あるので画像を作って200で返るはず）
    res = client.get("/charts")
    assert res.status_code == 200, f"グラフ画面が開けない: {res.status_code}"
    assert os.path.exists(os.path.join(appmod.STATIC_DIR, "calories.png")), \
        "カロリーのグラフ画像が作られていない"
    print("✓ テスト5：記録一覧・グラフ画面が表示できる")


if __name__ == "__main__":
    print("===== Web版(app.py) 自動テスト開始 =====")
    backup_real_files()
    try:
        test_index_ok()
        test_onboarding_creates_profile()
        test_record_saves()
        test_unknown_food_message()
        test_records_and_charts()
        print("===== すべて合格 🎉 =====")
    finally:
        restore_real_files()
        # テストで作ったグラフ画像も片づける
        for name in ("calories.png", "protein.png"):
            p = os.path.join(appmod.STATIC_DIR, name)
            if os.path.exists(p):
                os.remove(p)
