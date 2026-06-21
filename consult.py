# -*- coding: utf-8 -*-
"""
デジトレ 食事コンサル（機能④）

このファイルは「目標と実績を引き算して、残りを出す担当」です。
  残り許容量 ＝ 目標(②targets) − 実績(③intake)
「あと何kcal食べられるか」「タンパク質があと何g足りないか」を数値で示す。

設計の線引き（SPEC §6 / §0）：
  ・コードの役目：引き算して“残り”の数値を出すところまで（数値はブレさせない）。
  ・AIの役目：その数値をもとに「では夕食はこれ」と提案文を作る（将来）。
  ・計算結果は丸めない（丸めるのは表示する側）。

注意：目標(targets)と実績(intake)で辞書のキー名が違うので、ここで対応づける。
  目標 targets:  "Target Kcal" / "P(g)" / "F(g)" / "C(g)"
  実績 intake :  "kcal"        / "P"    / "F"    / "C"
"""

import sys

# Windowsの画面で日本語が文字化けしないように出力をUTF-8にする。
# （targets.py / intake.py 先頭と同じおまじない。このファイルやテストを
#   単体で動かす時のために入れておく）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def calculate_remaining(targets, intake):
    """
    目標から実績を引いて「残り許容量」を計算して返す。

    引数:
        targets : calculate_daily_targets が返す目標の辞書
        intake  : calculate_intake が返す実績（合計）の辞書
    戻り値:
        残りを入れた辞書。プラス＝まだ食べてよい量／不足分、
        マイナス＝すでに超過（食べ過ぎ）を表す。
        例: {"kcal": ..., "P": ..., "F": ..., "C": ...}
    """
    return {
        "kcal": targets["Target Kcal"] - intake["kcal"],
        "P": targets["P(g)"] - intake["P"],
        "F": targets["F(g)"] - intake["F"],
        "C": targets["C(g)"] - intake["C"],
    }


def show_remaining(remaining):
    """
    残り許容量を見やすく表示する（表示の瞬間に丸める）。
    プラスなら「あと食べてよい」、マイナスなら「超過」をことばで添える。
    """
    print("\n===== 残り許容量（目標 − 実績）=====")

    # カロリー：プラス＝あと食べられる、マイナス＝オーバー
    kcal = remaining["kcal"]
    if kcal >= 0:
        print(f" カロリー : あと {kcal:.0f} kcal 食べられます")
    else:
        # abs() でマイナス符号を外し、「超過」と伝える
        print(f" カロリー : {abs(kcal):.0f} kcal オーバーしています")

    # タンパク質は「不足分」を特に大事に見る栄養素なので個別に強調
    p = remaining["P"]
    if p > 0:
        print(f" タンパク質: あと {p:.1f} g 足りません（意識して補いましょう）")
    else:
        print(f" タンパク質: 目標達成（{abs(p):.1f} g 超過）")

    # 脂質・炭水化物は参考として残りを表示
    print(f" 脂質     : 残り {remaining['F']:.1f} g")
    print(f" 炭水化物 : 残り {remaining['C']:.1f} g")
    print("===================================")


# =====================================================================
# 動作確認用（このファイルを直接実行したときだけ動く）
# =====================================================================
if __name__ == "__main__":
    # 他の担当から借りてきて、実際の流れで試す
    from targets import calculate_daily_targets   # ② 目標
    from intake import calculate_intake           # ③ 実績

    # 例の人物の1日目標（男性30歳 170cm 70kg 活動1.5 −500 ダイエット特化）
    targets = calculate_daily_targets(
        gender="male", age=30, height=170, weight=70,
        activity_level=1.5, goal_offset=-500, strategy="③ダイエット特化",
    )

    # これまでに食べたもの（朝・昼の例）
    eaten = calculate_intake([
        ("ごはん（精白米）", 200),
        ("鶏むね肉（皮なし・生）", 150),
        ("卵（全卵・生）", 50),
    ])

    remaining = calculate_remaining(targets, eaten)

    # 参考に目標と実績も表示してから、残りを出す
    print("【目標】     "
          f"{targets['Target Kcal']:.0f}kcal / P{targets['P(g)']:.1f} F{targets['F(g)']:.1f} C{targets['C(g)']:.1f}")
    print("【食べた実績】"
          f"{eaten['kcal']:.0f}kcal / P{eaten['P']:.1f} F{eaten['F']:.1f} C{eaten['C']:.1f}")
    show_remaining(remaining)
