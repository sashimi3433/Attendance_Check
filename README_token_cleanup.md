# 未使用トークン自動削除機能

## 概要

未使用で期限切れの出席確認トークンを自動的に削除する機能です。
データベースの容量を節約し、システムのパフォーマンスを維持するために実装されています。

## 機能

### 1. Django管理コマンド

#### 基本的な使用方法

```bash
# 10分前の未使用期限切れトークンを削除
python manage.py cleanup_tokens

# 削除せずに対象トークン数のみ確認（ドライラン）
python manage.py cleanup_tokens --dry-run

# 30分前のトークンを削除
python manage.py cleanup_tokens --minutes=30
```

#### オプション

- `--minutes`: 何分前のトークンを削除するか（デフォルト: 10分）
- `--dry-run`: 実際に削除せず、削除対象のトークン数のみ表示

### 2. 自動実行設定

#### cronジョブでの設定

1. crontabを編集:
   ```bash
   crontab -e
   ```

2. 以下の行を追加（10分ごとに実行）:
   ```
   */10 * * * * /path/to/project/scripts/cleanup_tokens.sh
   ```

3. 設定を確認:
   ```bash
   crontab -l
   ```

#### 実行スクリプト

`scripts/cleanup_tokens.sh`スクリプトが提供されており、以下の機能があります：

- 仮想環境の自動アクティベート
- ログファイルへの実行結果記録
- エラーハンドリング

### 3. モデルメソッド

#### AttendanceToken.cleanup_expired_tokens(minutes=10)

```python
from attendance_token.models import AttendanceToken

# 10分前の未使用期限切れトークンを削除
deleted_count, details = AttendanceToken.cleanup_expired_tokens()
print(f"削除されたトークン数: {deleted_count}")

# 30分前のトークンを削除
deleted_count, details = AttendanceToken.cleanup_expired_tokens(minutes=30)
```

#### AttendanceToken.get_cleanup_statistics()

```python
from attendance_token.models import AttendanceToken

# 統計情報を取得
stats = AttendanceToken.get_cleanup_statistics()
print(f"総トークン数: {stats['total']}")
print(f"使用済み: {stats['used']}")
print(f"未使用: {stats['unused']}")
print(f"期限切れ未使用: {stats['expired_unused']}")
```

## ファイル構成

```
project/
├── attendance_token/
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── cleanup_tokens.py      # Django管理コマンド
│   └── models.py                      # クリーンアップメソッド追加
├── scripts/
│   └── cleanup_tokens.sh              # 自動実行スクリプト
├── logs/
│   └── token_cleanup.log              # 実行ログ（自動作成）
└── cron_setup.txt                     # cron設定例
```

## ログ

実行ログは `logs/token_cleanup.log` に記録されます。

### ログの例

```
[2024-01-15 10:00:01] トークンクリーンアップ開始
未使用の期限切れトークンを 5件 削除しました

=== トークン統計 ===
総トークン数: 15件
使用済み: 8件
未使用: 7件
期限切れ未使用: 2件
[2024-01-15 10:00:02] トークンクリーンアップ完了
```

## 注意事項

1. **削除条件**: 以下の条件をすべて満たすトークンが削除されます
   - 未使用（is_used=False）
   - 期限切れ（expires < 現在時刻 - 指定分数）

2. **データの整合性**: 削除されるのは未使用のトークンのみで、出席記録に関連付けられたトークンは削除されません

3. **パフォーマンス**: 大量のトークンがある場合は、削除処理に時間がかかる可能性があります

4. **権限**: cronジョブを設定する際は、適切なファイル権限とユーザー権限を確認してください

## トラブルシューティング

### よくある問題

1. **コマンドが見つからない**
   - 仮想環境がアクティベートされているか確認
   - プロジェクトディレクトリにいるか確認

2. **権限エラー**
   - スクリプトファイルに実行権限があるか確認: `chmod +x scripts/cleanup_tokens.sh`
   - ログディレクトリの書き込み権限を確認

3. **cronジョブが動作しない**
   - 絶対パスを使用しているか確認
   - cronサービスが動作しているか確認
   - ログファイルでエラーを確認

### デバッグ

```bash
# ドライランで動作確認
python manage.py cleanup_tokens --dry-run

# 詳細な統計情報を確認
python manage.py shell
>>> from attendance_token.models import AttendanceToken
>>> stats = AttendanceToken.get_cleanup_statistics()
>>> print(stats)
```