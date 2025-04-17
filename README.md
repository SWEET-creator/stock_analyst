# 株価分析ツール

このツールは、株価データの取得、分析、および投資判断の支援を行うPythonプログラムです。

## 機能

- 株価データの取得（Alpha Vantage API使用）
- 技術的分析
- ニュース取得と分析（Google News API使用）
- AIによる総合的な投資判断（OpenAI API使用）

## 必要条件

- Python 3.8以上
- 必要なPythonパッケージ（requirements.txtに記載）
- Alpha Vantage APIキー
- OpenAI APIキー

## インストール

1. リポジトリをクローン：
```bash
git clone [repository-url]
cd [repository-name]
```

2. 必要なパッケージをインストール：
```bash
pip install -r requirements.txt
```

3. `config.py`の設定：
```python
# Alpha Vantage APIキーを設定
ALPHA_VANTAGE_API_KEY = "your-alpha-vantage-api-key"

# OpenAI APIキーを設定
OPENAI_API_KEY = "your-openai-api-key"
```

APIキーの取得方法：
- Alpha Vantage APIキー: https://www.alphavantage.co/support/#api-key
- OpenAI APIキー: https://platform.openai.com/api-keys

## 使用方法

1. プログラムを実行：
```bash
python stock_price_alpha.py
```

2. デフォルトではテスラ（TSLA）の株価データを取得します。
   他の銘柄を分析する場合は、`stock_price_alpha.py`の以下の部分を変更：
```python
symbol = "TSLA"  # 分析したい銘柄のティッカーシンボル
company_name = "Tesla"  # 会社名
market = "US"    # 市場（US: 米国、JP: 日本）
```

## 出力内容

- 株価データ（過去100日分）
- 技術的分析結果
  - 前日比
  - PER
  - 配当利回り
  - 時価総額
  - 52週間価格帯
- 最新ニュースと分析
- AIによる総合的な投資判断
- 株価チャート

## 注意事項

- APIの利用制限に注意してください
- 投資判断は参考情報としてご利用ください
- 実際の投資判断は自己責任で行ってください

## トラブルシューティング

1. APIキーが設定されていない場合：
   - `config.py`に正しいAPIキーが設定されているか確認
   - APIキーが有効か確認

2. データが取得できない場合：
   - インターネット接続を確認
   - APIの利用制限に達していないか確認
   - ティッカーシンボルが正しいか確認

3. エラーメッセージが表示される場合：
   - エラーメッセージを確認
   - 必要なパッケージが正しくインストールされているか確認

## ライセンス

MIT License