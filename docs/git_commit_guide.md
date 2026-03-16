# Gitコミットガイド（リリース準備）

**作成日**: 2026-03-16
**バージョン**: 1.0
**対象**: Phase 2完了時点のコミット・リリース準備

---

## 1. 未コミットファイルの一覧

### 1.1 現在の状態

```bash
# git statusの結果（2026-03-16時点）

Changes not staged for commit:
	modified:   README.md

Untracked files:
	.env.example
	demo.py
	docs/candidate_consent_form.md
	docs/evaluation_guidelines.md
	docs/operation_manual.md
	docs/poc_execution_guide.md
	docs/poc_limited_checklist.md
	docs/poc_plan.md
	docs/revised-plan-v2.md
	docs/今後の課題と対策.md
	knowledge-base/
	poc_report_sample.json
	poc_report_sample.md
	requirements.txt
	src/
	tests/
```

### 1.2 ファイルの分類

#### カテゴリ1: コア実装
- `src/__init__.py`
- `src/analyzer.py`
- `src/knowledge_loader.py`
- `src/prompt_builder.py`
- `src/response_parser.py`（Iteration-04: ハルシネーション対策）
- `src/video_chunker.py`
- `src/chunked_analyzer.py`
- `src/poc_analysis.py`（Iteration-05: PoC分析ロジック）
- `src/streamlit_app.py`
- `src/prompts/system.txt`（Iteration-04: 出典明記追加）

#### カテゴリ2: テスト
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_analyzer.py`
- `tests/test_knowledge_loader.py`
- `tests/test_prompt_builder.py`
- `tests/test_response_parser.py`（Iteration-04: ハルシネーション検証テスト追加）
- `tests/test_video_chunker.py`
- `tests/test_chunked_analyzer.py`
- `tests/test_poc_analysis.py`（Iteration-05: PoC分析テスト）
- `tests/test_documentation.py`（Iteration-06: ドキュメント品質テスト）
- `tests/fixtures/`（各種フィクスチャ）

#### カテゴリ3: ドキュメント
- `README.md`（更新）
- `docs/revised-plan-v2.md`
- `docs/今後の課題と対策.md`
- `docs/evaluation_guidelines.md`（Iteration-04）
- `docs/poc_plan.md`（Iteration-05）
- `docs/poc_execution_guide.md`（Iteration-05）
- `docs/candidate_consent_form.md`（Iteration-06）
- `docs/operation_manual.md`（Iteration-06）
- `docs/poc_limited_checklist.md`（Iteration-06）
- `docs/git_commit_guide.md`（本ファイル）

#### カテゴリ4: ナレッジベース
- `knowledge-base/core-criteria.md`

#### カテゴリ5: 設定・その他
- `requirements.txt`（依存関係）
- `.env.example`（環境変数テンプレート）
- `demo.py`（デモスクリプト）
- `poc_report_sample.md`（サンプル出力）
- `poc_report_sample.json`（サンプル出力）

---

## 2. コミットメッセージ案

### 2.1 コミット戦略

**方針**: 機能ごとに分割してコミット（原子性の原則）

**メリット**:
- レビューしやすい
- 必要に応じて特定のコミットを revert 可能
- 履歴が明確

### 2.2 推奨コミット順序

#### Commit 1: 基本機能（Iteration-01〜03）

```bash
git add src/__init__.py src/analyzer.py src/knowledge_loader.py src/prompt_builder.py src/response_parser.py src/streamlit_app.py src/video_chunker.py src/chunked_analyzer.py src/prompts/
git add tests/__init__.py tests/conftest.py tests/test_analyzer.py tests/test_knowledge_loader.py tests/test_prompt_builder.py tests/test_response_parser.py tests/test_video_chunker.py tests/test_chunked_analyzer.py
git add tests/fixtures/mock_gemini_response.json tests/fixtures/test_knowledge.md
git add knowledge-base/
git add requirements.txt .env.example demo.py
git add README.md

git commit -m "Add core AI interview analysis system (Iteration-01~03)

Features:
- Video analysis with Gemini 2.5 Flash API
- Knowledge base integration (behavioral psychology)
- Prompt builder with bias prevention
- Response parser with structured validation
- Video chunking for long videos (30+ minutes)
- Streamlit Web UI for easy operation
- Comprehensive test coverage (22 tests)

Tech stack:
- Python 3.12+
- google-genai SDK
- Streamlit for UI
- pytest for testing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Commit 2: ハルシネーション対策（Iteration-04）

```bash
git add src/response_parser.py src/prompts/system.txt
git add tests/test_response_parser.py
git add tests/fixtures/response_*.json
git add docs/evaluation_guidelines.md

git commit -m "Add hallucination prevention features (Iteration-04)

Features:
- Reference citation enforcement in observations
- Low confidence threshold check (3+ categories)
- Contradiction detection (high score + negative keywords)
- Validation function: validate_response()

Quality improvements:
- Prompt updated to require citations
- System prompt includes confidence criteria
- Response parser validates references, confidence, contradictions

Test coverage:
- 14 tests for response parser (all passing)
- 4 test fixtures for edge cases

Documentation:
- Evaluation guidelines with confidence definitions

Score: 93/100 (A grade)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Commit 3: PoC分析ロジック（Iteration-05）

```bash
git add src/poc_analysis.py
git add requirements.txt  # scipy, scikit-learn, pandas added
git add tests/test_poc_analysis.py
git add tests/fixtures/poc_sample_data/
git add docs/poc_plan.md docs/poc_execution_guide.md
git add poc_report_sample.md poc_report_sample.json

git commit -m "Add PoC analysis features for precision validation (Iteration-05)

Features:
- Correlation calculation (Pearson, Spearman)
- Confusion matrix generation
- False positive/negative rate calculation
- Hallucination verification integration
- PoC report generation (Markdown + JSON)
- CLI tool with --sample option

Dependencies added:
- scipy >= 1.11.0
- scikit-learn >= 1.3.0
- pandas >= 2.1.0

Test coverage:
- 9 new tests for PoC analysis (all passing)
- Sample data with 5 candidates (2 excellent, 2 problematic, 1 borderline)
- Dry run successful (correlation: 0.994)

Documentation:
- PoC implementation plan
- PoC execution guide (step-by-step)

Score: 96/100 (A grade)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Commit 4: 運用ドキュメント（Iteration-06）

```bash
git add docs/candidate_consent_form.md docs/operation_manual.md docs/poc_limited_checklist.md docs/git_commit_guide.md
git add tests/test_documentation.py

git commit -m "Add operation documents for production deployment (Iteration-06)

Documentation:
- Candidate consent form (privacy law compliance)
- Operation manual (workflow, UI guide, troubleshooting)
- Limited PoC checklist (functional validation, not statistical)
- Git commit guide (release preparation)

Quality assurance:
- Document quality tests (10 tests)
- Required sections validation
- Markdown link validation

Key documents:
1. Candidate consent form
   - Purpose and scope of use
   - Personal data collection (video, evaluation results)
   - AI analysis explanation
   - Consent withdrawal rights
   - GDPR/privacy law compliance

2. Operation manual
   - System overview
   - Operation workflow (9 steps)
   - Streamlit UI guide
   - Troubleshooting (common errors)
   - Escalation criteria
   - Post-deployment improvement plan

3. Limited PoC checklist
   - Functional validation only (1 video, no human comparison)
   - System operation check
   - Hallucination verification
   - Pass/fail criteria

4. Git commit guide
   - Uncommitted files list
   - Commit message templates
   - Release tag recommendations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Commit 5: 計画ドキュメント

```bash
git add docs/revised-plan-v2.md docs/今後の課題と対策.md

git commit -m "Add project planning documents

Documentation:
- Revised project plan v2 (milestones, iterations)
- Future challenges and countermeasures

Planning changes:
- Statistical PoC (5-10 videos) → Limited PoC (1 video, functional check)
- Phase 3 precision validation postponed to post-deployment

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 3. リリースタグ案

### 3.1 セマンティックバージョニング

推奨バージョン: **`v0.9.0`** または **`v1.0.0-beta`**

### 3.2 タグの選択基準

#### オプション1: `v0.9.0`（推奨）

**理由**:
- Phase 2完了、Phase 3未実施
- 統計的精度検証が未完了
- 運用開始可能だが、精度は未保証

**メリット**:
- 「未完成」であることが明確
- v1.0.0は精度検証完了後にリリース

**推奨度**: ⭐⭐⭐⭐⭐

#### オプション2: `v1.0.0-beta`

**理由**:
- β版として運用開始
- 正式版（v1.0.0）は精度検証完了後

**メリット**:
- 「β版」であることが明確
- v1.0.0への移行が自然

**推奨度**: ⭐⭐⭐⭐

#### オプション3: `v1.0.0`（非推奨）

**理由**:
- 基本機能は実装済み

**デメリット**:
- 精度検証が未完了なのに「正式版」と誤解される
- 後で問題が発覚した場合、信頼性低下のリスク

**推奨度**: ⭐⭐

### 3.3 推奨タグ

```bash
# タグ作成
git tag -a v0.9.0 -m "Release v0.9.0 - Phase 2 Complete (Pre-production)"

# または
git tag -a v1.0.0-beta -m "Release v1.0.0-beta - Beta version for production deployment"

# タグをリモートにプッシュ
git push origin v0.9.0
# または
git push origin v1.0.0-beta
```

---

## 4. リリースノート案

### 4.1 リリースノートテンプレート

```markdown
# AI Interview Analysis System - Release v0.9.0

**Release Date**: 2026-03-16
**Status**: Phase 2 Complete (Pre-production)
**Next Step**: Phase 3 (Statistical precision validation post-deployment)

---

## Overview

AI-powered interview video analysis system for behavioral psychology-based risk screening in SES business. This release completes Phase 2 (Practical version) and is ready for production deployment with **functional validation only** (statistical precision validation planned for Phase 3).

---

## What's New

### Core Features

1. **Video Analysis with Gemini 2.5 Flash API**
   - Multimodal AI analysis (video + audio)
   - 4 evaluation categories: Communication, Stress Tolerance, Reliability, Teamwork
   - Structured JSON output with confidence levels

2. **Hallucination Prevention (Iteration-04)**
   - Reference citation enforcement
   - Low confidence threshold check
   - Contradiction detection
   - Validation score: 93/100

3. **PoC Analysis Features (Iteration-05)**
   - Correlation calculation (Pearson, Spearman)
   - False positive/negative rate calculation
   - Report generation (Markdown + JSON)
   - Sample data dry run: correlation 0.994

4. **Streamlit Web UI**
   - Easy video upload
   - Real-time analysis
   - Interactive results display
   - JSON export

5. **Operation Documents (Iteration-06)**
   - Candidate consent form
   - Operation manual
   - Limited PoC checklist
   - Troubleshooting guide

---

## Technical Stack

- **Language**: Python 3.12+
- **AI Model**: Google Gemini 2.5 Flash
- **SDK**: google-genai, streamlit, scipy, scikit-learn, pandas
- **Testing**: pytest (41 tests, all passing)
- **Documentation**: Comprehensive user guides and operation manuals

---

## Installation

```bash
# Clone repository
git clone https://github.com/your-org/ai_interview-analysis.git
cd ai_interview-analysis

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run Streamlit UI
streamlit run src/streamlit_app.py
```

---

## Usage

1. **Start Streamlit UI**: `streamlit run src/streamlit_app.py`
2. **Upload video**: Click "Upload interview video"
3. **Start analysis**: Click "Start analysis"
4. **Review results**: Check evaluation report
5. **Make decision**: Human final judgment (AI is reference only)

See [Operation Manual](./operation_manual.md) for details.

---

## Important Notes

### ⚠️ Precision Not Yet Validated

- **Status**: Functional validation complete (Limited PoC)
- **Statistical validation**: Planned for Phase 3 (post-deployment)
- **Recommendation**: Treat AI evaluation as **reference information only**
- **Final judgment**: Always made by humans

### Phase 3 Plan

- **Timeline**: 3 months post-deployment
- **Scope**: 5-10 video samples
- **Metrics**: Correlation > 0.7, FPR < 20%, FNR < 10%
- **Goal**: Statistical precision validation

---

## Documentation

- [README](../README.md): Project overview and setup
- [Operation Manual](./operation_manual.md): User guide
- [Candidate Consent Form](./candidate_consent_form.md): Privacy compliance
- [Evaluation Guidelines](./evaluation_guidelines.md): Confidence definitions
- [PoC Plan](./poc_plan.md): Precision validation plan
- [Limited PoC Checklist](./poc_limited_checklist.md): Functional validation

---

## Test Coverage

- **Total tests**: 41 (all passing)
- **Coverage**: Core features, hallucination prevention, PoC analysis, documentation quality
- **Test frameworks**: pytest, pytest-mock

---

## Known Limitations

1. **Precision unvalidated**: Statistical validation pending (Phase 3)
2. **Sample size**: Limited PoC with 1 video only
3. **False negative rate**: May be higher than target (33% in sample data)
4. **Language**: Japanese only (system prompts and documentation)

---

## Future Roadmap

### Phase 3 (Post-deployment)
- Statistical precision validation (5-10 videos)
- Correlation, false positive/negative rate measurement
- Prompt and knowledge base improvement

### Phase 4 (Long-term)
- Multilingual support (English)
- Batch processing (multiple videos)
- Advanced analytics (trend analysis)
- Integration with HR systems

---

## Contributors

- **Project Owner**: Iwao-san
- **Development**: Co-authored by Claude Sonnet 4.5

---

## License

TBD

---

## Contact

For questions or issues, please contact:
- Email: recruit@example.com (placeholder)
- GitHub Issues: https://github.com/your-org/ai_interview-analysis/issues
```

---

## 5. リリース手順

### 5.1 事前確認

- [ ] 全テストがPASSすることを確認
- [ ] ドキュメントが最新であることを確認
- [ ] `.env.example` が正しく設定されていることを確認

```bash
# テスト実行
pytest tests/ -v

# ドキュメントテスト
pytest tests/test_documentation.py -v
```

### 5.2 コミット実行

上記「2. コミットメッセージ案」の順序でコミットを実行：

```bash
# Commit 1: 基本機能
git add [ファイルリスト]
git commit -m "[メッセージ]"

# Commit 2: ハルシネーション対策
git add [ファイルリスト]
git commit -m "[メッセージ]"

# Commit 3: PoC分析ロジック
git add [ファイルリスト]
git commit -m "[メッセージ]"

# Commit 4: 運用ドキュメント
git add [ファイルリスト]
git commit -m "[メッセージ]"

# Commit 5: 計画ドキュメント
git add [ファイルリスト]
git commit -m "[メッセージ]"
```

### 5.3 タグ作成

```bash
# タグ作成（v0.9.0推奨）
git tag -a v0.9.0 -m "Release v0.9.0 - Phase 2 Complete (Pre-production)"

# タグの確認
git tag -l
git show v0.9.0
```

### 5.4 リモートへプッシュ

```bash
# コミットをプッシュ
git push origin main

# タグをプッシュ
git push origin v0.9.0
```

### 5.5 GitHubリリース作成

GitHubのWeb UIで以下を実施：

1. **Releases** → **Create a new release** をクリック
2. **Choose a tag**: `v0.9.0` を選択
3. **Release title**: `v0.9.0 - Phase 2 Complete (Pre-production)`
4. **Describe this release**: 上記「4.1 リリースノートテンプレート」を貼り付け
5. **This is a pre-release** にチェック（v0.9.0の場合）
6. **Publish release** をクリック

---

## 6. リリース後の確認

### 6.1 動作確認

- [ ] リモートリポジトリからクローン
- [ ] セットアップ手順に従ってインストール
- [ ] Streamlit UIが起動することを確認
- [ ] サンプルデータで解析が成功することを確認

### 6.2 ドキュメント確認

- [ ] READMEが正しく表示されることを確認
- [ ] 各ドキュメントのリンクが正しく動作することを確認

---

## 7. 更新履歴

| 日付 | バージョン | 内容 |
|---|---|---|
| 2026-03-16 | 1.0 | 初版作成（Iteration-06） |

---

**Gitコミットガイド v1.0**
**作成日**: 2026-03-16
