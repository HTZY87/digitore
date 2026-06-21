# -*- coding: utf-8 -*-
"""
デジトレ 入口（main）

このファイルは「司令塔」です。自分では計算も質問もせず、
各担当ファイルから関数を借りてきて、正しい順番で呼ぶだけ。
全体の流れがここを読むだけで分かるようにしてある。

  これを動かすには：  python main.py

役割分担（どのファイルが何をするか）：
  ・dialogue.py … 質問して情報を集める／結果を表示する（人と話す担当）
  ・targets.py  … 目標カロリー・PFCを計算する（計算エンジン）
  ・safety.py   … 設定が極端すぎないか警告する（安全担当）
"""

# 各担当から必要な関数を借りてくる。
# ※ targets を読み込んだ時点で「画面出力はUTF-8で」という設定も動くので、
#   日本語が文字化けしない（targets.py の先頭で設定している）。
from targets import calculate_daily_targets    # ② 計算エンジン
from dialogue import run_onboarding, show_result  # ① 対話・表示
from safety import check_safety                 # ⑥ 安全警告


# このファイルを直接実行したときだけ、下の流れが動く
if __name__ == "__main__":
    profile = run_onboarding()                       # ① 聞き取り
    result = calculate_daily_targets(**profile)      # ② 計算（エンジンに依頼）
    show_result(result)                              # 結果を表示
    check_safety(profile["weight"], profile["goal_offset"])  # ⑥ 安全チェック
