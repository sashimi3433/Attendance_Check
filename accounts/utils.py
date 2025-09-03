# -*- coding: utf-8 -*-
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def invalidate_user_sessions(user, exclude_session_key=None):
    """
    指定されたユーザーの既存セッションを無効化する
    
    Args:
        user: 対象のユーザーオブジェクト
        exclude_session_key: 除外するセッションキー（通常は現在のセッション）
    """
    if user.current_session_key and user.current_session_key != exclude_session_key:
        try:
            # 既存のセッションを削除
            session = Session.objects.get(session_key=user.current_session_key)
            session.delete()
        except Session.DoesNotExist:
            # セッションが既に存在しない場合は何もしない
            pass
    
    # ユーザーの現在のセッションキーを更新
    if exclude_session_key:
        user.current_session_key = exclude_session_key
        user.save(update_fields=['current_session_key'])

def cleanup_expired_sessions():
    """
    期限切れのセッションをクリーンアップし、
    対応するユーザーのcurrent_session_keyもクリアする
    """
    # 期限切れのセッションを取得
    expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
    expired_session_keys = list(expired_sessions.values_list('session_key', flat=True))
    
    # 期限切れのセッションを削除
    expired_sessions.delete()
    
    # 対応するユーザーのcurrent_session_keyをクリア
    User.objects.filter(current_session_key__in=expired_session_keys).update(current_session_key=None)

def force_logout_user(user):
    """
    指定されたユーザーを強制的にログアウトさせる
    
    Args:
        user: 対象のユーザーオブジェクト
    """
    invalidate_user_sessions(user)
    user.current_session_key = None
    user.save(update_fields=['current_session_key'])