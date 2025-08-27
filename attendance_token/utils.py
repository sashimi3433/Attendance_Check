# attendance_token/utils.py
# IPアドレス取得用ユーティリティ関数

import logging
import requests
import json
import urllib3
from django.http import HttpRequest
from django.conf import settings

# SSL警告を無効化（開発環境用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger('attendance_token.utils')


def get_global_ip_from_external_service() -> str:
    """
    外部サービスを利用してグローバルIPアドレスを取得する
    
    複数のサービスを順番に試行し、最初に成功したサービスのIPを返す
    すべてのサービスが失敗した場合は空文字列を返す
    
    Returns:
        str: グローバルIPアドレス、取得失敗時は空文字列
    """
    # 設定から外部サービス情報を取得
    external_config = getattr(settings, 'EXTERNAL_IP_SERVICES', {})
    
    # 外部サービスが無効化されている場合
    if not external_config.get('ENABLED', False):
        logger.debug("外部IPサービスが無効化されています")
        return ''
    
    services = external_config.get('SERVICES', [])
    timeout = external_config.get('TIMEOUT', 5)
    
    for service_url in services:
        try:
            logger.debug(f"外部サービスからIP取得を試行: {service_url}")
            
            # SSL証明書検証を無効化（開発環境用）
            response = requests.get(service_url, timeout=timeout, verify=False)
            response.raise_for_status()
            
            # レスポンスの処理
            ip_address = _extract_ip_from_response(response, service_url)
            
            if ip_address and _is_valid_global_ip(ip_address):
                logger.info(f"外部サービス {service_url} からグローバルIP取得成功: {ip_address}")
                return ip_address
            else:
                logger.warning(f"外部サービス {service_url} から無効なIPを受信: {ip_address}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"外部サービス {service_url} でタイムアウト発生")
        except requests.exceptions.RequestException as e:
            logger.warning(f"外部サービス {service_url} でエラー発生: {e}")
        except Exception as e:
            logger.error(f"外部サービス {service_url} で予期しないエラー: {e}")
    
    logger.warning("すべての外部IPサービスでIP取得に失敗しました")
    return ''


def _extract_ip_from_response(response: requests.Response, service_url: str) -> str:
    """
    外部サービスのレスポンスからIPアドレスを抽出する
    
    Args:
        response: HTTPレスポンスオブジェクト
        service_url: サービスのURL（ログ用）
        
    Returns:
        str: 抽出されたIPアドレス、失敗時は空文字列
    """
    try:
        content = response.text.strip()
        
        # httpbin.orgの場合はJSON形式
        if 'httpbin.org' in service_url:
            data = json.loads(content)
            return data.get('origin', '').split(',')[0].strip()
        
        # その他のサービスは通常プレーンテキスト
        return content
        
    except json.JSONDecodeError:
        logger.warning(f"JSONデコードエラー: {service_url}")
        return ''
    except Exception as e:
        logger.error(f"レスポンス解析エラー {service_url}: {e}")
        return ''


def _is_valid_global_ip(ip: str) -> bool:
    """
    グローバルIPアドレスの妥当性をチェックする
    
    Args:
        ip (str): チェック対象のIPアドレス文字列
        
    Returns:
        bool: 有効なグローバルIPアドレスの場合True
    """
    import ipaddress
    
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        # プライベートIPアドレス、ローカルホスト、マルチキャストを除外
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
            return False
            
        # リンクローカルアドレスも除外
        if hasattr(ip_obj, 'is_link_local') and ip_obj.is_link_local:
            return False
            
        return True
        
    except ValueError:
        return False


def get_client_ip(request: HttpRequest) -> str:
    """
    クライアントのIPアドレスを取得する（グローバルIP優先）
    
    1. 外部サービスを利用してグローバルIPを取得
    2. 失敗した場合はHTTPヘッダーからIPを取得
    3. すべて失敗した場合はフォールバック値を返す
    
    Args:
        request (HttpRequest): DjangoのHTTPリクエストオブジェクト
        
    Returns:
        str: クライアントのIPアドレス
    """
    # 設定から外部サービス情報を取得
    external_config = getattr(settings, 'EXTERNAL_IP_SERVICES', {})
    debug_mode = external_config.get('DEBUG_IP_DETECTION', False)
    force_external_for_local = external_config.get('FORCE_EXTERNAL_FOR_LOCAL', False)
    local_dev_mode = external_config.get('LOCAL_DEVELOPMENT_MODE', False)
    
    if debug_mode:
        logger.debug(f"IP取得開始 - 設定: ENABLED={external_config.get('ENABLED', False)}, "
                    f"FORCE_EXTERNAL_FOR_LOCAL={force_external_for_local}, "
                    f"LOCAL_DEVELOPMENT_MODE={local_dev_mode}")
    
    # ローカル環境の検出
    is_local_request = _is_local_request(request)
    if debug_mode:
        logger.debug(f"ローカルリクエスト判定: {is_local_request}")
    
    # 1. 外部サービスからグローバルIPを取得
    # ローカル環境でも強制的に外部サービスを使用する場合、または通常の外部サービス使用
    if external_config.get('ENABLED', False) and (force_external_for_local or not is_local_request):
        if debug_mode:
            logger.debug("外部サービスからのIP取得を試行")
        
        global_ip = get_global_ip_from_external_service()
        if global_ip:
            logger.info(f"外部サービスからグローバルIP取得成功: {global_ip}")
            return global_ip
        else:
            logger.warning("外部サービスからのIP取得に失敗")
    
    # 2. HTTPヘッダーからIPアドレスを取得（フォールバック）
    if external_config.get('FALLBACK_TO_HEADERS', True):
        if debug_mode:
            logger.debug("HTTPヘッダーからのIP取得を試行")
        
        header_ip = _get_ip_from_headers(request)
        if header_ip:
            # ローカル環境でプライベートIPが取得された場合の警告
            if is_local_request and _is_private_ip(header_ip):
                logger.warning(f"ローカル環境でプライベートIP取得: {header_ip} - "
                             f"本番環境では適切なプロキシ設定が必要です")
            
            logger.info(f"HTTPヘッダーからIP取得: {header_ip}")
            return header_ip
    
    # 3. すべて失敗した場合
    logger.error("すべての方法でIPアドレス取得に失敗しました")
    return '0.0.0.0'


def _get_ip_from_headers(request: HttpRequest) -> str:
    """
    HTTPヘッダーからIPアドレスを取得する（従来の方法）
    
    Args:
        request (HttpRequest): DjangoのHTTPリクエストオブジェクト
        
    Returns:
        str: IPアドレス、取得失敗時は空文字列
    """
    # プロキシ経由の場合のヘッダーを優先順位順にチェック
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
    ]
    
    # プロキシヘッダーをチェック
    for header in headers_to_check:
        ip_list = request.META.get(header)
        if ip_list:
            # カンマ区切りの場合、最初のIPアドレスを取得
            ip = ip_list.split(',')[0].strip()
            if ip and _is_valid_ip(ip):
                logger.debug(f"IPアドレスを{header}から取得: {ip}")
                return ip
    
    # プロキシヘッダーがない場合、直接接続のIPアドレスを取得
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr and _is_valid_ip(remote_addr):
        logger.debug(f"IPアドレスをREMOTE_ADDRから取得: {remote_addr}")
        return remote_addr
    
    # IPアドレスが取得できない場合
    logger.warning("HTTPヘッダーからのIPアドレス取得に失敗しました")
    return ''


def _is_valid_ip(ip: str) -> bool:
    """
    IPアドレスの妥当性をチェックする
    
    Args:
        ip (str): チェック対象のIPアドレス文字列
        
    Returns:
        bool: 有効なIPアドレスの場合True
    """
    import ipaddress
    
    try:
        # IPv4またはIPv6アドレスとして妥当かチェック
        ipaddress.ip_address(ip)
        
        # プライベートIPアドレスやローカルホストは除外しない
        # （開発環境やイントラネット環境でも使用するため）
        
        return True
    except ValueError:
        return False


def _is_local_request(request: HttpRequest) -> bool:
    """
    ローカル環境からのリクエストかどうかを判定する
    
    Args:
        request (HttpRequest): HTTPリクエストオブジェクト
        
    Returns:
        bool: ローカルリクエストの場合True
    """
    # REMOTE_ADDRをチェック
    remote_addr = request.META.get('REMOTE_ADDR', '')
    
    # ローカルホストアドレスのパターン
    local_patterns = ['127.0.0.1', '::1', 'localhost']
    
    # プライベートIPアドレスの範囲もチェック
    if _is_private_ip(remote_addr):
        return True
    
    # ローカルホストパターンのチェック
    for pattern in local_patterns:
        if remote_addr == pattern:
            return True
    
    # HTTPホストヘッダーもチェック
    http_host = request.META.get('HTTP_HOST', '')
    if any(host in http_host for host in ['localhost', '127.0.0.1', '::1']):
        return True
    
    return False


def _is_private_ip(ip: str) -> bool:
    """
    プライベートIPアドレスかどうかを判定する
    
    Args:
        ip (str): チェック対象のIPアドレス文字列
        
    Returns:
        bool: プライベートIPアドレスの場合True
    """
    import ipaddress
    
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


def log_ip_access(request: HttpRequest, action: str, additional_info: str = "") -> None:
    """
    IPアドレスアクセスをログに記録する
    
    Args:
        request (HttpRequest): HTTPリクエストオブジェクト
        action (str): 実行されたアクション（例: "token_generation", "checkin_attempt"）
        additional_info (str): 追加情報（オプション）
    """
    client_ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    # セキュリティログ用のロガーを使用
    security_logger = logging.getLogger('ip_security')
    
    log_message = f"IP: {client_ip} | Action: {action} | User-Agent: {user_agent}"
    if additional_info:
        log_message += f" | Info: {additional_info}"
    
    security_logger.info(log_message)