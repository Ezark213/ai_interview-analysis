# システム構成

## アーキテクチャ概要

本システムは、面談動画とナレッジベースをGemini APIに送信し、行動心理学的な評価レポートを生成するシステムです。

---

## アーキテクチャパターン

### パターンA: Google Apps Script版（簡易版・PoC向け）

#### 構成図
```
┌─────────────────────────────────────────────────────────┐
│                     Google Workspace                     │
│                                                          │
│  ┌──────────────┐        ┌──────────────┐              │
│  │ Google Drive │        │Google Sheets │              │
│  │              │        │              │              │
│  │ ・動画       │        │ ・評価結果   │              │
│  │ ・ナレッジ   │        │ ・候補者情報 │              │
│  └──────┬───────┘        └──────┬───────┘              │
│         │                       │                       │
│         │                       │                       │
│  ┌──────▼───────────────────────▼───────┐              │
│  │   Google Apps Script (GAS)            │              │
│  │                                       │              │
│  │  ┌─────────────────────────────────┐ │              │
│  │  │ main.gs                         │ │              │
│  │  │ - ファイル読み込み              │ │              │
│  │  │ - API呼び出し制御               │ │              │
│  │  │ - レポート生成                  │ │              │
│  │  └─────────────────────────────────┘ │              │
│  │                                       │              │
│  │  ┌─────────────────────────────────┐ │              │
│  │  │ gemini-api.gs                   │ │              │
│  │  │ - Gemini API統合                │ │              │
│  │  │ - プロンプト構築                │ │              │
│  │  └─────────────────────────────────┘ │              │
│  │                                       │              │
│  │  ┌─────────────────────────────────┐ │              │
│  │  │ report-generator.gs             │ │              │
│  │  │ - JSON → Sheets変換             │ │              │
│  │  │ - PDFレポート生成               │ │              │
│  │  └─────────────────────────────────┘ │              │
│  └───────────────┬───────────────────────┘              │
│                  │                                       │
└──────────────────┼───────────────────────────────────────┘
                   │
                   │ HTTPS
                   │
          ┌────────▼────────┐
          │  Gemini API     │
          │  (AI Studio)    │
          │                 │
          │ ・動画解析      │
          │ ・テキスト処理  │
          │ ・評価生成      │
          └─────────────────┘
```

#### データフロー
1. **担当者がGoogleドライブに動画をアップロード**
   - 面談動画（MP4等）を特定フォルダに配置
   - ファイル名規則: `YYYYMMDD_候補者名.mp4`

2. **GASトリガー起動**
   - 時間ベーストリガー（例: 毎日深夜0時）
   - または手動実行

3. **ファイル読み込み**
   - 未処理の動画ファイルを検出
   - ナレッジベースを読み込み

4. **Gemini API呼び出し**
   - 動画とナレッジを送信
   - システムプロンプトで評価指示

5. **結果の保存**
   - Google Sheetsに評価結果を記録
   - PDFレポートを生成してDriveに保存
   - 担当者にメール通知

#### コンポーネント詳細

##### main.gs
```javascript
// 疑似コード
function main() {
  // 1. 未処理の動画を取得
  const videos = getUnprocessedVideos();

  // 2. ナレッジベースを読み込み
  const knowledge = loadKnowledgeBase();

  // 3. 各動画を処理
  videos.forEach(video => {
    try {
      // API呼び出し
      const result = analyzeVideo(video, knowledge);

      // 結果を保存
      saveToSheet(result);
      generatePdfReport(result);

      // 通知
      sendNotification(result);

    } catch (error) {
      logError(error);
      notifyAdmin(error);
    }
  });
}
```

##### gemini-api.gs
```javascript
function analyzeVideo(videoFile, knowledgeText) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  const endpoint = 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent';

  // プロンプト構築
  const prompt = buildPrompt(knowledgeText);

  // API呼び出し
  const response = UrlFetchApp.fetch(endpoint, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify({
      contents: [
        { text: prompt },
        { video: videoFile.getBlob() }
      ]
    })
  });

  return JSON.parse(response.getContentText());
}
```

---

### パターンB: GCP統合版（本格版・スケーラブル）

#### 構成図
```
┌─────────────────────────────────────────────────────────────┐
│                      フロントエンド                          │
│                                                              │
│  ┌──────────────────┐       ┌──────────────────┐           │
│  │  採用管理システム │       │  管理画面        │           │
│  │  (既存システム)   │       │  (新規開発)      │           │
│  └────────┬─────────┘       └────────┬─────────┘           │
│           │                          │                      │
└───────────┼──────────────────────────┼──────────────────────┘
            │                          │
            │ REST API                 │
            │                          │
┌───────────▼──────────────────────────▼──────────────────────┐
│                    Google Cloud Platform                     │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Cloud Storage                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│  │
│  │  │ 動画バケット  │  │ナレッジ      │  │レポート      ││  │
│  │  │              │  │バケット      │  │バケット      ││  │
│  │  └──────┬───────┘  └──────────────┘  └──────────────┘│  │
│  └─────────┼────────────────────────────────────────────┘  │
│            │                                                 │
│            │ トリガー                                         │
│            │                                                 │
│  ┌─────────▼───────────────────────────────────────────┐    │
│  │  Cloud Functions (Node.js / Python)                 │    │
│  │                                                      │    │
│  │  ┌────────────────────────────────────────────────┐ │    │
│  │  │ video-upload-handler                           │ │    │
│  │  │ - 動画アップロード時のトリガー                  │ │    │
│  │  │ - バリデーション                                │ │    │
│  │  └────────────────────────────────────────────────┘ │    │
│  │                                                      │    │
│  │  ┌────────────────────────────────────────────────┐ │    │
│  │  │ video-analysis-function                        │ │    │
│  │  │ - Gemini API呼び出し                           │ │    │
│  │  │ - 動画とナレッジの送信                          │ │    │
│  │  │ - 結果のパース                                 │ │    │
│  │  └────────────────────────────────────────────────┘ │    │
│  │                                                      │    │
│  │  ┌────────────────────────────────────────────────┐ │    │
│  │  │ report-generator-function                      │ │    │
│  │  │ - PDFレポート生成                              │ │    │
│  │  │ - BigQueryへのデータ保存                       │ │    │
│  │  │ - 通知送信                                     │ │    │
│  │  └────────────────────────────────────────────────┘ │    │
│  └──────────────────┬───────────────────────────────────┘    │
│                     │                                        │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐    │
│  │  BigQuery                                            │    │
│  │                                                      │    │
│  │  ┌────────────────┐  ┌────────────────┐            │    │
│  │  │ candidates     │  │ evaluations    │            │    │
│  │  │ (候補者マスタ)  │  │ (評価結果)     │            │    │
│  │  └────────────────┘  └────────────────┘            │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Cloud Logging / Cloud Monitoring                    │    │
│  │  - 処理ログ                                          │    │
│  │  - エラーログ                                        │    │
│  │  - パフォーマンスモニタリング                         │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ HTTPS
                           │
                  ┌────────▼────────┐
                  │  Gemini API     │
                  │  (Vertex AI)    │
                  │                 │
                  │ ・動画解析      │
                  │ ・テキスト処理  │
                  │ ・評価生成      │
                  └─────────────────┘
```

#### データフロー

##### 1. 動画アップロード
```
[採用システム]
    → REST API
    → [Cloud Storage]
    → [Pub/Sub通知]
    → [video-upload-handler]
```

##### 2. 解析処理
```
[video-upload-handler]
    → バリデーション
    → [video-analysis-function]
    → [Gemini API]
    → 結果取得
```

##### 3. 結果保存・通知
```
[video-analysis-function]
    → [report-generator-function]
    → [BigQuery保存]
    → [PDFレポート生成]
    → [Cloud Storage保存]
    → [メール/Slack通知]
```

#### コンポーネント詳細

##### video-analysis-function (Python)
```python
import functions_framework
from google.cloud import storage
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel

@functions_framework.cloud_event
def analyze_video(cloud_event):
    # 動画ファイル情報取得
    bucket_name = cloud_event.data["bucket"]
    file_name = cloud_event.data["name"]

    # Cloud Storageから動画を取得
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # ナレッジベースを読み込み
    knowledge_blob = bucket.blob("knowledge/psychology_base.txt")
    knowledge_text = knowledge_blob.download_as_text()

    # Vertex AI初期化
    vertexai.init(project="your-project-id", location="us-central1")
    model = GenerativeModel("gemini-1.5-pro")

    # プロンプト構築
    prompt = build_prompt(knowledge_text)

    # Gemini APIで解析
    response = model.generate_content([
        prompt,
        vertexai.Part.from_uri(f"gs://{bucket_name}/{file_name}", mime_type="video/mp4")
    ])

    # 結果をBigQueryに保存
    save_to_bigquery(response.text)

    # レポート生成関数を呼び出し
    trigger_report_generation(file_name, response.text)

    return {"status": "success"}
```

---

## セキュリティアーキテクチャ

### 認証・認可
```
[ユーザー]
    → [Cloud Identity/Workspace認証]
    → [IAMロール確認]
    → [リソースアクセス]
```

### データ保護
- **転送中**: TLS 1.3
- **保存時**: Cloud KMS自動暗号化
- **アクセス制御**: IAMポリシーによる最小権限

### 監査ログ
- すべてのAPI呼び出しをCloud Loggingに記録
- BigQueryで長期保存・分析

---

## 拡張性とスケーラビリティ

### 水平スケーリング
- Cloud Functions: 自動スケール（最大1000インスタンス）
- Cloud Storage: 無制限のストレージ
- BigQuery: ペタバイト級のデータ処理可能

### 地理的冗長性
- マルチリージョン構成のオプション
- ディザスタリカバリ対応

---

## モニタリングとアラート

### メトリクス
- API呼び出し成功率
- 処理時間
- エラー率
- コスト推移

### アラート設定
- エラー率が5%を超えた場合
- 処理時間が10分を超えた場合
- API利用料が予算を超えた場合

---

## バックアップとリカバリ

### データバックアップ
- Cloud Storage: バージョニング有効化
- BigQuery: スナップショット（日次）

### リカバリ手順
1. エラーログの確認
2. 該当データの特定
3. バックアップからの復元
4. 再処理の実行

---

## コスト最適化

### コスト削減策
- **動画の自動削除**: 処理完了後、一定期間で削除
- **ストレージクラス**: 長期保存はColdline/Archiveを使用
- **Cloud Functionsの最適化**: メモリ割り当ての調整

---

## デプロイメント

### CI/CDパイプライン
```
[GitHub]
    → [Cloud Build]
    → [テスト実行]
    → [本番デプロイ]
```

### 環境分離
- 開発環境（dev）
- ステージング環境（staging）
- 本番環境（production）

---

## 次のステップ

### Phase 1: PoC（Google Apps Script版）
- [ ] プロトタイプの実装と動作確認

### Phase 2: 本格実装（GCP版）
- [ ] インフラのセットアップ
- [ ] Cloud Functionsの実装
- [ ] セキュリティ設定

### Phase 3: 運用開始
- [ ] モニタリング体制の確立
- [ ] 運用マニュアルの整備
