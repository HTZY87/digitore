# -*- coding: utf-8 -*-
"""
デジトレ 可視化（機能⑧ / 段階⑥）

このファイルは「貯めた記録をグラフにして見せる担当」です。
record.py が残した records.csv を読み込み、2種類のグラフを画像（PNG）に保存する。

  グラフ1：カロリー 実績 vs 目標（棒グラフ）   → calories.png
  グラフ2：タンパク質(P) の達成度（折れ線）   → protein.png

設計メモ（なぜ画面に出さず画像に保存するか）：
  ・このアプリは画面の無い環境（Dockerの箱）でも動かすため、
    matplotlib を「画像ファイルに書き出すモード（Agg）」で使う。
  ・できた PNG をあとから開けば、どんな環境でもグラフを確認できる。

設計メモ（グラフの日本語表示）：
  ・グラフに日本語を出すには日本語フォントが必要。
    assets/fonts/ipaexg.ttf があればそれを使って日本語ラベルで描く。
    （フォントが無い環境では → python setup_font.py で用意できる）
  ・万一フォントが見つからないときは、文字化け（豆腐□）を避けるため
    自動で英語ラベルに切り替えて描く（グラフ自体は必ず作れる）。

くわしい仕様は SPEC.md（第9-2章）を参照してください。
"""

import sys
import os

import matplotlib
# ★重要：グラフを画面に出さず画像ファイルに書き出す設定。
#   import pyplot より前に必ず指定する（後だと効かない）。
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from record import load_records, DEFAULT_RECORDS_CSV

# Windowsの画面で日本語が文字化けしないように出力をUTF-8にする（他ファイルと同じ）。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# できた画像の保存先も __file__ 基準で決める（どこから実行しても同じ場所に出る）。
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CALORIE_PNG = os.path.join(_HERE, "calories.png")
DEFAULT_PROTEIN_PNG = os.path.join(_HERE, "protein.png")

# 日本語フォントの置き場所（setup_font.py が用意する場所と合わせる）。
FONT_PATH = os.path.join(_HERE, "assets", "fonts", "ipaexg.ttf")


# =====================================================================
# 0. 日本語フォントの準備（あれば日本語ラベル／無ければ英語ラベル）
# =====================================================================

def _setup_font():
    """
    日本語フォントが使えるよう matplotlib に登録する。
    戻り値: 使えた場合 True（日本語ラベルで描く）／無い場合 False（英語にする）。
    """
    if not os.path.exists(FONT_PATH):
        return False
    # フォントを matplotlib に教え込み、既定フォントに設定する。
    fm.fontManager.addfont(FONT_PATH)
    font_name = fm.FontProperties(fname=FONT_PATH).get_name()
    plt.rcParams["font.family"] = font_name
    # マイナス記号が豆腐(□)に化けるのを防ぐお作法。
    plt.rcParams["axes.unicode_minus"] = False
    return True


# 日本語が使えるか一度だけ判定し、ラベルの言語をそれに合わせて選ぶ。
_JP = _setup_font()

# グラフ内の文字（日本語が使えれば日本語、ダメなら英語）。
# 1か所にまとめておけば、後でラベルを直すのも楽。
if _JP:
    L = {
        "cal_title": "カロリー：実績 vs 目標",
        "actual": "実績", "target": "目標",
        "date": "日付", "kcal": "kcal",
        "p_title": "タンパク質(P) の達成度",
        "p_line": "P達成度", "p_goal": "目標(100%)",
        "achievement": "達成度（％）",
    }
else:
    L = {
        "cal_title": "Calories: Actual vs Target",
        "actual": "Actual", "target": "Target",
        "date": "Date", "kcal": "kcal",
        "p_title": "Protein (P) Achievement",
        "p_line": "P achievement", "p_goal": "Target (100%)",
        "achievement": "Achievement (%)",
    }


# =====================================================================
# グラフ1：カロリー 実績 vs 目標（棒グラフ）
# =====================================================================

def make_calorie_chart(records, out_path=DEFAULT_CALORIE_PNG):
    """
    日付ごとに「実際に食べたカロリー」と「目標カロリー」を
    2本並べた棒グラフにして、PNG画像に保存する。

    引数:
        records  : load_records() が返す記録のリスト
        out_path : 保存先の画像パス（省略すると calories.png）
    """
    # x軸の位置（0,1,2,...）。日付ラベルはあとで貼る。
    positions = list(range(len(records)))
    dates = [r["日付"] for r in records]
    actual = [r["合計kcal"] for r in records]   # 実績
    target = [r["目標kcal"] for r in records]   # 目標

    width = 0.4  # 棒の太さ（2本を左右に少しずらして並べるため）

    fig, ax = plt.subplots(figsize=(8, 4.5))
    # 実績の棒（少し左へ）／目標の棒（少し右へ）
    ax.bar([p - width / 2 for p in positions], actual, width, label=L["actual"])
    ax.bar([p + width / 2 for p in positions], target, width, label=L["target"])

    ax.set_title(L["cal_title"])
    ax.set_xlabel(L["date"])
    ax.set_ylabel(L["kcal"])
    ax.set_xticks(positions)
    ax.set_xticklabels(dates, rotation=45, ha="right")
    ax.legend()
    fig.tight_layout()  # ラベルがはみ出さないよう自動で余白調整

    fig.savefig(out_path)
    plt.close(fig)  # 後片付け（メモリを解放）
    return out_path


# =====================================================================
# グラフ2：タンパク質(P) の達成度（折れ線）
# =====================================================================

def make_protein_chart(records, out_path=DEFAULT_PROTEIN_PNG):
    """
    日付ごとの「実績P ÷ 目標P × 100（％）」を折れ線で描き、PNG画像に保存する。
    100% の位置に目印の横線を引いて、達成・不足が一目で分かるようにする。

    ※達成度の“割り算”はコード側で計算する（数値はブレさせない）。
      目標Pが無い・0 の行は割れないので、その日は飛ばす。
    """
    positions = []   # x軸の位置
    dates = []       # 日付ラベル
    rates = []       # 達成度(%)

    for i, r in enumerate(records):
        target_p = r["目標P(g)"]
        actual_p = r["P(g)"]
        # 目標Pが空(None)や0だと割り算できないので、その行はスキップ。
        if not target_p:
            continue
        positions.append(i)
        dates.append(r["日付"])
        rates.append(actual_p / target_p * 100)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(positions, rates, marker="o", label=L["p_line"])
    # 100%（目標ぴったり）の目安線を引く
    ax.axhline(100, linestyle="--", label=L["p_goal"])

    ax.set_title(L["p_title"])
    ax.set_xlabel(L["date"])
    ax.set_ylabel(L["achievement"])
    ax.set_xticks(positions)
    ax.set_xticklabels(dates, rotation=45, ha="right")
    ax.legend()
    fig.tight_layout()

    fig.savefig(out_path)
    plt.close(fig)
    return out_path


# =====================================================================
# まとめ役：記録を読み込み、2つのグラフを作る
# =====================================================================

def visualize_all(csv_path=DEFAULT_RECORDS_CSV):
    """
    records.csv を読み込み、2種類のグラフを画像に保存する。
    記録がまだ1件も無いときは、グラフを作らず案内だけ出す。

    戻り値:
        作った画像パスのリスト（記録ゼロのときは空リスト）。
    """
    records = load_records(csv_path)

    if not records:
        # 記録が貯まって初めて意味が出る機能なので、ゼロなら優しく案内。
        print("まだ記録がありません。先に食事を記録してから、もう一度お試しください。")
        return []

    calorie_png = make_calorie_chart(records)
    protein_png = make_protein_chart(records)

    print("===== グラフを作りました（画像ファイル）=====")
    print(f" ① カロリー 実績vs目標 : {calorie_png}")
    print(f" ② タンパク質 達成度   : {protein_png}")
    if not _JP:
        # フォントが無くて英語表示になったときだけ、用意の仕方を案内する。
        print("-------------------------------------------")
        print(" ※日本語フォントが無いため、グラフ内の文字は英語で描きました。")
        print("   日本語にしたいときは  python setup_font.py  を実行してください。")
    print("===========================================")
    return [calorie_png, protein_png]


# =====================================================================
# 動作確認用（このファイルを直接実行したときだけ動く）
# =====================================================================
if __name__ == "__main__":
    visualize_all()
