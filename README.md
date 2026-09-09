# PDF Chat 📑

Retrieval-Augmented Generation (RAG) を活用した PDF チャットボットアプリケーション。複数の PDF ドキュメントを一度にアップロードして、その内容について自然言語で質問できます。

## 必要性

現代のビジネスやリサーチの現場では、大量の PDF ドキュメント（契約書、マニュアル、論文、報告書など）から特定の情報を素早く抽出する必要があります。従来の方法では：

- **手作業での検索**: Ctrl+F での検索は単語マッチのみで、意味を理解した検索ができない
- **時間の浪費**: 数百ページのドキュメントから必要な情報を探すのに膨大な時間がかかる
- **文脈の喪失**: 複数ドキュメント間の関連情報を繋げる作業が困難

このアプリは、**最新の大規模言語モデル (LLM) とベクトル検索技術**を組み合わせることで、PDF の内容を意味的に理解し、自然言語での質問に対して正確な回答を即座に提供します。

## 主な特徴

✨ **簡単なセットアップ**
- Docker 対応で環境構築が簡単
- ローカルでの実行が可能（ベクトルDB も含む）

🔍 **意味ベースの検索**
- Voyage AI の最新埋め込みモデルで高精度なベクトル化
- Qdrant による高速な類似度検索

🤖 **複数 LLM モデル対応**
- Claude Haiku（軽量・高速）
- Claude Sonnet（高精度）
- サイドバーで簡単に切り替え可能

⚡ **無料枠対応**
- Voyage AI free tier の 3RPM 制限に自動対応
- 指数バックオフによるリトライロジック搭載

📊 **使いやすい UI**
- Streamlit による直感的なインターフェース
- PDF アップロード、埋め込み処理の進捗表示
- リアルタイムエラー通知

## 技術スタック

| コンポーネント | 技術 |
|---|---|
| **UI フレームワーク** | Streamlit |
| **LLM** | Claude (Anthropic) |
| **埋め込みモデル** | Voyage AI (`voyage-4-lite`) |
| **ベクトルDB** | Qdrant |
| **PDF 処理** | PyPDF |
| **テキスト分割** | LangChain RecursiveCharacterTextSplitter |
| **オーケストレーション** | LangChain RetrievalQA |
| **コンテナ** | Docker + Docker Compose |

## クイックスタート

### 前提条件

- Python 3.11+
- Docker & Docker Compose（オプション）
- API キー：
  - [Anthropic API キー](https://console.anthropic.com/)
  - [Voyage AI API キー](https://www.voyageai.com/)

### インストール

#### オプション 1: ローカル実行

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/pdf-chat.git
cd pdf-chat

# 依存ライブラリをインストール
pip install -r requirements.txt

# .env ファイルを作成
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_key_here
VOYAGE_API_KEY=your_voyage_key_here
EOF

# アプリケーションを起動
streamlit run src/main.py
```

#### オプション 2: Docker 実行（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/pdf-chat.git
cd pdf-chat

# .env ファイルを作成
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_key_here
VOYAGE_API_KEY=your_voyage_key_here
EOF

# Docker Compose で起動
docker-compose up --build
```

ブラウザで `http://localhost:8501` にアクセスしてください。

## 使い方

### 1. PDF のアップロード

1. サイドバーから **"PDF Upload"** を選択
2. **"Upload your PDF file"** をクリック
3. PDF ファイルをアップロード
4. 自動的にテキスト抽出・埋め込み処理が開始
5. 処理完了後、"完了しました!" と表示されます

### 2. PDF への質問

1. サイドバーから **"Ask My PDF(s)"** を選択
2. モデルを選択（Haiku or Sonnet）
3. 質問を入力
4. AI が PDF の内容に基づいて回答を生成

## アーキテクチャ

```
┌─────────────────┐
│  PDF ファイル    │
└────────┬────────┘
         ↓
┌─────────────────────────────┐
│  テキスト抽出 (PyPDF)        │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  テキスト分割 (LangChain)    │
│  - チャンクサイズ: 1000 chars│
│  - オーバーラップ: 100 chars │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  ベクトル化 (Voyage AI)      │
│  - モデル: voyage-4-lite    │
│  - 次元: 1024              │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  ベクトルDB (Qdrant)         │
│  - 永続化: ./local_qdrant   │
└─────────────────────────────┘

┌─────────────────┐
│  ユーザーの質問   │
└────────┬────────┘
         ↓
┌─────────────────────────────┐
│  質問をベクトル化            │
│  (Voyage AI)                │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  類似チャンク検索 (Qdrant)   │
│  - k: 10                   │
│  - 距離メトリック: Cosine   │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  プロンプト構築             │
│  (検索結果 + 質問)         │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  Claude LLM で回答生成      │
│  (Haiku or Sonnet)         │
└────────┬────────────────────┘
         ↓
┌─────────────────┐
│  ユーザーに表示  │
└─────────────────┘
```

## レート制限への対応

Voyage AI の無料枠は **3 RPM (3 Requests Per Minute)** に制限されています。本アプリケーションは以下の方法で対応しています：

- 埋め込みを**チャンク単位で逐次処理**（並列化なし）
- 各リクエスト間に **21 秒の待機時間** を設定
- **レート制限エラーの際は指数バックオフでリトライ**
  - 1 回目: 20 秒待機
  - 2 回目: 40 秒待機
  - 3 回目: 60 秒待機
  - 以降も同様
- 5 回のリトライに失敗したチャンクはスキップされ、ログに記録

## プロジェクト構成

```
pdf-chat/
├── src/
│   └── main.py              # メインアプリケーション
├── local_qdrant/            # ベクトルDB永続化ディレクトリ（実行時作成）
├── requirements.txt         # Python 依存ライブラリ
├── dockerfile               # Docker イメージ定義
├── docker-compose.yml       # Docker Compose 設定
├── .env.example             # 環境変数テンプレート
├── README.md                # このファイル
└── CLAUDE.md                # Claude Code 用ガイド
```

## 主な機能

### PDF テキスト抽出
- PyPDF を使用した高精度なテキスト抽出
- ページごとのテキスト結合
- 大規模テキストの自動チャンク化

### インテリジェントなテキスト分割
- 単語や文の区切りを保持する再帰的分割
- チャンク間のオーバーラップで文脈を保全

### ベクトル埋め込み
- Voyage AI `voyage-4-lite` モデル使用
- トークンカウント機能（監視用）

### RAG チェーン
- LangChain による自動プロンプト構築
- Qdrant との統合検索
- Claude による最終回答生成

### UI/UX
- 直感的な 2 ページレイアウト
- 進捗バー + ステータス表示
- エラーハンドリングと通知
- モデル選択ドロップダウン

## 環境変数

`.env` ファイルで以下の環境変数を設定します：

```
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic API キー
VOYAGE_API_KEY=pa-...               # Voyage AI API キー
```

## トラブルシューティング

### レート制限エラーが出続ける

これは Voyage AI 無料枠の正常な動作です。以下の対応を試してください：

1. **少量の PDF から始める** — 最初は小さい PDF でテストして徐々に規模を増やす
2. **チャンクサイズを調整** — `src/main.py` の `chunk_size` を大きくしてチャンク数を減らす
3. **有料プランへアップグレード** — Voyage AI または Anthropic のプランをアップグレード

### ベクトル DB が見つからない

Qdrant のコレクションが自動作成されます。手動で削除した場合は、再度アップロードすることで自動的に再作成されます。

### API キーエラー

`.env` ファイルが正しく配置されていることを確認してください：

```bash
# Docker を使用している場合
docker-compose exec app cat /app/.env

# ローカル実行の場合
cat .env
```

## パフォーマンス

### 典型的な処理時間（目安）

- PDF アップロード〜テキスト抽出: 数秒
- テキスト分割: 数秒
- ベクトル化（100 チャンク）: 約 35 分（3RPM レート制限対応）
- 質問への回答生成: 5-15 秒

### 推奨設定

| 用途 | LLM モデル | 推奨チャンク数 |
|---|---|---|
| 試験運用 | Haiku | < 50 |
| 本運用（速度重視） | Haiku | < 200 |
| 本運用（精度重視） | Sonnet | < 500 |

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まず Issue を開いて変更内容を議論してください。

## サポート

問題が発生した場合は、[GitHub Issues](https://github.com/yourusername/pdf-chat/issues) で報告してください。

## 関連リソース

- [Anthropic Claude API ドキュメント](https://docs.anthropic.com/)
- [Voyage AI ドキュメント](https://docs.voyageai.com/)
- [Qdrant ドキュメント](https://qdrant.tech/documentation/)
- [LangChain ドキュメント](https://python.langchain.com/)
- [Streamlit ドキュメント](https://docs.streamlit.io/)

---

**作成日**: 2026-09-09  
**バージョン**: 1.0.0
