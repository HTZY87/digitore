# -*- coding: utf-8 -*-
"""
デジトレ 日本語フォントの準備（段階⑥の下ごしらえ）

このスクリプトは「グラフに日本語を表示するためのフォントを用意する担当」です。
段階⑥（可視化）のグラフに日本語（タイトル・軸ラベル等）を出すには、
日本語フォントが必要です。多くの最小環境（Dockerの箱など）には
日本語フォントが入っていないため、ここで1つダウンロードして置きます。

  使い方：  python setup_font.py
  → assets/fonts/ipaexg.ttf が用意できれば成功。

なぜこの形か：
  ・フォント本体（数MB）はリポジトリには入れない（履歴が重くなるため）。
    → .gitignore で除外し、必要な人がこのスクリプトで取得する。
  ・置き場所は /project 配下なので、箱を作り直さない限り消えない。

使うフォント：IPAexゴシック（情報処理推進機構IPA・IPAフォントライセンス v1.0）。
  日本語表示の定番で、商用利用も可能。ライセンス全文も一緒に保存する。
"""

import os
import sys
import io
import zipfile
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 配布元（IPA公式の配布ページにあるZIP）。中に ipaexg.ttf とライセンス文が入っている。
FONT_ZIP_URL = "https://moji.or.jp/wp-content/ipafont/IPAexfont/ipaexg00401.zip"

_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(_HERE, "assets", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "ipaexg.ttf")
LICENSE_PATH = os.path.join(FONT_DIR, "IPA_Font_License_Agreement_v1.0.txt")


def setup_font():
    """日本語フォント(ipaexg.ttf)を assets/fonts/ に用意する。"""
    # すでにある場合は何もしない（二重取得を避ける）。
    if os.path.exists(FONT_PATH):
        print(f"✓ すでにフォントがあります: {FONT_PATH}")
        return FONT_PATH

    os.makedirs(FONT_DIR, exist_ok=True)
    print("日本語フォント（IPAexゴシック）をダウンロードしています…")

    req = urllib.request.Request(FONT_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        zip_bytes = r.read()

    # ダウンロードしたZIPをメモリ上で開き、必要なファイルだけ取り出す。
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            lower = name.lower()
            if lower.endswith("ipaexg.ttf"):
                with open(FONT_PATH, "wb") as f:
                    f.write(z.read(name))
            elif "license" in lower and lower.endswith(".txt"):
                # 再配布の作法として、ライセンス全文も一緒に保存しておく。
                with open(LICENSE_PATH, "wb") as f:
                    f.write(z.read(name))

    if not os.path.exists(FONT_PATH):
        raise RuntimeError("ZIPの中に ipaexg.ttf が見つかりませんでした。")

    print(f"✓ フォントを用意しました: {FONT_PATH}")
    print(f"  ライセンス全文       : {LICENSE_PATH}")
    return FONT_PATH


if __name__ == "__main__":
    setup_font()
