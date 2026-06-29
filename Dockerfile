# ベースイメージ：Node.js 22 入りの軽量Linux（Claude Codeの動作に必要）
FROM node:22-slim

# パッケージ情報を更新し、Python3とgitをインストール
# Python3：デジトレの実行に必要
# git：Claudeがコードの変更履歴を操作するために必要
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Claude Code CLI をグローバルインストール
RUN npm install -g @anthropic-ai/claude-code

# デジトレが使うPythonライブラリ（Flask=Web画面 / matplotlib=グラフ）を入れる。
# requirements.txt を先にコピーしておくと、依存だけ変えたときにここから作り直せる。
# --break-system-packages：このOSのpip保護(PEP668)を承知のうえで入れる指定。
#   （箱は使い捨て前提＝箱の中に直接入れてよい、という判断）
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# ログイン情報の保存先を用意し、非rootの node ユーザー所有にする
# （理由1：--dangerously-skip-permissions は root 実行を拒否する仕様なので node で動かす）
# （理由2：ここを名前付きボリュームに繋ぐことで、一度ログインすれば次回から不要になる）
RUN mkdir -p /home/node/.claude && chown -R node:node /home/node/.claude

# 箱の中の作業場所を /project に設定
WORKDIR /project
