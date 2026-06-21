# -*- coding: utf-8 -*-
"""
デジトレ 安全警告（機能⑥）

「その設定、極端すぎませんか？」を見張る担当。
1日のカロリー増減から「1か月の体重変化（予測）」を計算し、
それが現体重の5%を超えるなら警告を出す。

（もとは app.py の中にあった機能を、役割ごとに分けて独立させたものです）
くわしい仕様は SPEC.md（第8章）を参照してください。
"""

# 体重1kgの増減に相当する、おおよそのカロリー（体脂肪ベースの一般値）。
# 安全警告の計算に使う固定値。
KCAL_PER_KG_BODY = 7200


def check_safety(weight, goal_offset):
    """
    1日のカロリー増減から「月の体重変化（予測）」を出し、
    それが現体重の5%を超えるなら警告する。

    引数:
        weight      : 現在の体重(kg)
        goal_offset : 1日のカロリー増減（減量 -500 など）
    """
    # 月の予測変化(kg) = 1日の増減 × 30日 ÷ (1kgあたりのカロリー)
    monthly_change_kg = goal_offset * 30 / KCAL_PER_KG_BODY
    # 現体重に対する割合(%)。abs() は絶対値（マイナスの符号を外して大きさだけ見る）
    percent = abs(monthly_change_kg) / weight * 100

    if percent > 5:
        print("\n⚠ 注意：この設定だと月の体重変化が約 "
              f"{percent:.1f}%（{monthly_change_kg:+.1f}kg）と大きめです。")
        print("  体に負担がかかる可能性があります。もう少しゆるやかな目標も検討しましょう。")
    else:
        print(f"\n✓ 体重変化は月 約{percent:.1f}%（{monthly_change_kg:+.1f}kg）。"
              "無理のない範囲です。")
