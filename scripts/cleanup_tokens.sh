#!/bin/bash
# scripts/cleanup_tokens.sh
# 未使用トークンの自動削除スクリプト

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ログファイルのパス
LOG_FILE="$PROJECT_DIR/logs/token_cleanup.log"

# ログディレクトリが存在しない場合は作成
mkdir -p "$(dirname "$LOG_FILE")"

# 現在時刻をログに記録
echo "[$(date '+%Y-%m-%d %H:%M:%S')] トークンクリーンアップ開始" >> "$LOG_FILE"

# プロジェクトディレクトリに移動
cd "$PROJECT_DIR"

# 仮想環境をアクティベート（必要に応じて調整）
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Django管理コマンドを実行
python manage.py cleanup_tokens --minutes=10 >> "$LOG_FILE" 2>&1

# 実行結果をログに記録
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] トークンクリーンアップ完了" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] トークンクリーンアップでエラーが発生しました" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"