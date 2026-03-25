"""フィードバック送信モジュール

GitHub Issue作成 + メール通知でフィードバックを収集する。
"""
import json
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from datetime import datetime


GITHUB_REPO = "Ezark213/ai_interview-analysis"
FEEDBACK_EMAIL = "yiwao@arma-as.co.jp"

# カテゴリ → GitHub Issueラベル
CATEGORY_LABELS = {
    "バグ報告": "bug",
    "機能リクエスト": "enhancement",
    "UI改善": "ui",
    "評価精度": "accuracy",
    "その他": "feedback",
}


def create_github_issue(
    title: str,
    body: str,
    category: str,
    github_token: str,
) -> dict:
    """GitHub Issueを作成する

    Args:
        title: Issue のタイトル
        body: Issue の本文（Markdown）
        category: フィードバックカテゴリ
        github_token: GitHub Personal Access Token

    Returns:
        dict: 作成されたIssueの情報（html_url等）

    Raises:
        Exception: API呼び出し失敗時
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    label = CATEGORY_LABELS.get(category, "feedback")

    data = {
        "title": f"[{category}] {title}",
        "body": body,
        "labels": [label, "user-feedback"],
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Authorization": f"token {github_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Interview-Analysis-App",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_email_notification(
    title: str,
    body: str,
    category: str,
    sender_name: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    to_email: str = FEEDBACK_EMAIL,
) -> None:
    """メールでフィードバック通知を送信する

    Args:
        title: 件名
        body: 本文
        category: カテゴリ
        sender_name: 送信者名
        smtp_host: SMTPホスト
        smtp_port: SMTPポート
        smtp_user: SMTP認証ユーザー
        smtp_pass: SMTP認証パスワード
        to_email: 送信先メールアドレス
    """
    subject = f"[AI面談解析FB] [{category}] {title}"

    email_body = f"""AI面談動画解析システム - フィードバック通知

送信者: {sender_name}
カテゴリ: {category}
日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}

--- 内容 ---
{title}

{body}
---
このメールはAI面談動画解析システムから自動送信されています。
"""

    msg = MIMEText(email_body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())


def submit_feedback(
    title: str,
    body: str,
    category: str,
    sender_name: str = "匿名",
    github_token: str = "",
    smtp_config: dict = None,
) -> dict:
    """フィードバックを送信する（GitHub Issue + メール）

    Args:
        title: フィードバックのタイトル
        body: 詳細内容
        category: カテゴリ
        sender_name: 送信者名
        github_token: GitHub Token（未設定時はIssue作成スキップ）
        smtp_config: SMTP設定dict（未設定時はメール送信スキップ）

    Returns:
        dict: 送信結果 {"github": ..., "email": ...}
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    issue_body = f"""## フィードバック

**カテゴリ**: {category}
**送信者**: {sender_name}
**日時**: {timestamp}

### 内容
{body}

---
*このIssueはアプリのフィードバックフォームから自動作成されました。*
"""

    result = {"github": None, "email": None}

    # GitHub Issue作成
    if github_token:
        try:
            issue = create_github_issue(title, issue_body, category, github_token)
            result["github"] = {
                "success": True,
                "url": issue.get("html_url", ""),
                "number": issue.get("number", 0),
            }
        except Exception as e:
            result["github"] = {"success": False, "error": str(e)}

    # メール通知
    if smtp_config and smtp_config.get("host"):
        try:
            send_email_notification(
                title=title,
                body=body,
                category=category,
                sender_name=sender_name,
                smtp_host=smtp_config["host"],
                smtp_port=int(smtp_config.get("port", 587)),
                smtp_user=smtp_config["user"],
                smtp_pass=smtp_config["password"],
                to_email=smtp_config.get("to_email", FEEDBACK_EMAIL),
            )
            result["email"] = {"success": True}
        except Exception as e:
            result["email"] = {"success": False, "error": str(e)}

    return result
