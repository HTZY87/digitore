# -*- coding: utf-8 -*-
"""
デジトレ 対話・入力・表示（機能①）

このファイルは「人と話す担当」です。
ユーザーに質問して情報を集め（オンボーディング）、計算結果を画面に見せる。
計算そのものは行わない（計算は targets.py の役目）。役割を分けることで、
計算の中身を触らずに見た目や聞き方だけを変えられる。

（もとは app.py の前半部分でした）
くわしい仕様は SPEC.md（第3章）を参照してください。
"""


# =====================================================================
# 入力を受け取る小さな部品（まちがった入力にやさしく対応する）
# =====================================================================

def ask_number(prompt, min_value, max_value, integer=False):
    """
    数字を1つ受け取る。数字でない・範囲外なら、聞き直す。
        prompt    : 画面に出す質問文
        min_value : 受け付ける最小値
        max_value : 受け付ける最大値
        integer   : True なら整数として受け取る（年齢など）
    """
    # while True は「正しい入力が来るまでずっと繰り返す」という意味
    while True:
        raw = input(prompt).strip()  # 入力を受け取り、前後の空白を取り除く
        try:
            # 整数か小数か、指定に応じて数値に変換する
            value = int(raw) if integer else float(raw)
        except ValueError:
            # 数字に変換できなかった（文字を入れた等）→ エラーで止めず聞き直す
            print("  → 数字で入力してください。")
            continue
        # 範囲のチェック
        if value < min_value or value > max_value:
            print(f"  → {min_value}〜{max_value} の範囲で入力してください。")
            continue
        return value  # ここまで来たら正しい値なので返す


def ask_choice(prompt, options):
    """
    番号で1つ選んでもらう（メニュー方式。打ち間違いを防げる）。
        prompt  : 見出しの質問文
        options : (画面に出すラベル, 実際に使う値) のリスト
    戻り値: 選ばれた「実際に使う値」
    """
    print(prompt)
    # 選択肢に 1) 2) 3)... と番号を振って表示する
    # enumerate(..., start=1) は「1から番号を振りながら順に取り出す」書き方
    for i, (label, _value) in enumerate(options, start=1):
        print(f"  {i}) {label}")

    while True:
        raw = input("  番号を入力: ").strip()
        try:
            idx = int(raw)
        except ValueError:
            print("  → 番号（数字）で入力してください。")
            continue
        if idx < 1 or idx > len(options):
            print(f"  → 1〜{len(options)} の番号で入力してください。")
            continue
        # options[idx-1] は選ばれた行。その [1] が「実際に使う値」
        return options[idx - 1][1]


# =====================================================================
# オンボーディング（機能①）：情報を一つずつ聞き取る
# =====================================================================

def run_onboarding():
    """質問して、計算に必要な7項目を集めて辞書で返す。"""
    print("===== デジトレ 初期設定 =====\n")

    gender = ask_choice("■ 性別を選んでください：", [
        ("男性", "male"),
        ("女性", "female"),
    ])
    age = ask_number("■ 年齢（歳）: ", 10, 100, integer=True)
    height = ask_number("■ 身長（cm）: ", 100, 250)
    weight = ask_number("■ 現在の体重（kg）: ", 20, 300)
    activity_level = ask_number("■ 活動強度（1.2=低い 〜 1.9=高い）: ", 1.2, 1.9)

    goal_offset = ask_choice("■ 目的を選んでください：", [
        ("減量・ゆっくり（-250kcal）", -250),
        ("減量・標準（-500kcal）", -500),
        ("減量・ハイペース（-750kcal）", -750),
        ("維持（±0kcal）", 0),
        ("増量・標準（+250kcal）", 250),
        ("増量・しっかり（+500kcal）", 500),
    ])
    strategy = ask_choice("■ PFC戦略を選んでください：", [
        ("①ウェルネス（バランス重視）", "①ウェルネス"),
        ("②ヘルスケア（たんぱく質しっかり）", "②ヘルスケア"),
        ("③ダイエット特化（高P・低F）", "③ダイエット特化"),
        ("④筋肥大・競技者（P最大）", "④筋肥大・競技者"),
    ])

    # 集めた情報を辞書にまとめて返す（calculate_daily_targets にそのまま渡せる形）
    return dict(
        gender=gender,
        age=age,
        height=height,
        weight=weight,
        activity_level=activity_level,
        goal_offset=goal_offset,
        strategy=strategy,
    )


# =====================================================================
# 結果の表示
# =====================================================================

def show_result(result):
    # エンジンは丸めず正確な数値を返すので、表示するこの場所で丸める。
    #   :.1f = 小数第1位まで表示 ／ :.0f = 整数で表示
    print("\n===== あなたの1日の目標 =====")
    print(f" BMR（基礎代謝量）  : {result['BMR']:.1f} kcal")
    print(f" TDEE（総消費）     : {result['TDEE']:.1f} kcal")
    print(f" 目標カロリー       : {result['Target Kcal']:.0f} kcal")
    print("-------------------------------------------")
    print(f" P タンパク質       : {result['P(g)']:.1f} g")
    print(f" F 脂質             : {result['F(g)']:.1f} g")
    print(f" C 炭水化物         : {result['C(g)']:.1f} g")
    print("===========================================")
