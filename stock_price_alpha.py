from alpha_vantage.timeseries import TimeSeries
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from config import ALPHA_VANTAGE_API_KEY, OPENAI_API_KEY
import time
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from GoogleNews import GoogleNews

api_key = ALPHA_VANTAGE_API_KEY

def get_stock_news(symbol, company_name, limit=5):
    """
    LangChainを使用して株価関連のニュースを取得し、要約を生成する
    
    Args:
        symbol (str): 株価コード
        company_name (str): 会社名
        limit (int): 取得するニュースの件数
    
    Returns:
        list: ニュース記事のリスト
    """
    try:
        # Google Newsからニュースを取得
        googlenews = GoogleNews()
        googlenews.set_lang('en')
        googlenews.set_period('7d')  # 過去7日間のニュース
        googlenews.set_encode('utf-8')
        
        # 検索クエリの作成
        query = f"{company_name} OR {symbol} stock"
        googlenews.search(query)
        
        # ニュースの取得
        news_results = googlenews.results()[:limit]
        
        if not news_results:
            return None
        
        # OpenAIの設定
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=OPENAI_API_KEY
        )
        
        # プロンプトテンプレートの作成
        prompt = ChatPromptTemplate.from_template(
            """以下のニュース記事を要約し、投資判断に役立つ情報を抽出してください：
            
            {news_text}
            
            要約と投資判断に役立つ情報を日本語で提供してください。
            """
        )
        
        # チェーンの作成（非推奨メソッドを修正）
        chain = prompt | llm
        
        # ニュースの処理
        processed_news = []
        for news in news_results:
            # ニューステキストの作成
            news_text = f"""
            タイトル: {news['title']}
            日付: {news['date']}
            内容: {news['desc']}
            URL: {news['link']}
            """
            
            try:
                # 要約の生成（非推奨メソッドを修正）
                summary = chain.invoke({"news_text": news_text})
                processed_news.append({
                    'title': news['title'],
                    'date': news['date'],
                    'summary': summary.content,
                    'url': news['link']
                })
            except Exception as e:
                print(f"ニュースの要約生成中にエラーが発生しました: {e}")
                # 要約生成に失敗した場合は、元のニュース情報のみを保存
                processed_news.append({
                    'title': news['title'],
                    'date': news['date'],
                    'summary': "要約を生成できませんでした。",
                    'url': news['link']
                })
        
        return processed_news
        
    except Exception as e:
        print(f"ニュースの取得中にエラーが発生しました: {e}")
        return None

def analyze_stock(stock_data, info):
    """
    株価データを分析し、投資判断の参考となる情報を提供する
    
    Args:
        stock_data (pandas.DataFrame): 株価データ
        info (dict): 会社情報
    
    Returns:
        dict: 分析結果
    """
    analysis = {}
    
    # 基本的な分析
    current_price = info.get('currentPrice')
    previous_close = info.get('previousClose')
    if isinstance(current_price, (int, float)) and isinstance(previous_close, (int, float)):
        price_change = ((current_price - previous_close) / previous_close) * 100
        analysis['price_change'] = f"{price_change:+.2f}%"
        analysis['price_trend'] = "上昇" if price_change > 0 else "下落"
    
    # PER分析
    pe_ratio = info.get('trailingPE')
    if isinstance(pe_ratio, (int, float)):
        analysis['pe_analysis'] = "割高" if pe_ratio > 20 else "割安" if pe_ratio < 15 else "適正"
        analysis['pe_ratio'] = f"{pe_ratio:.2f}"
    
    # 配当利回り分析
    dividend_yield = info.get('dividendYield')
    if isinstance(dividend_yield, (int, float)):
        analysis['dividend_analysis'] = "高配当" if dividend_yield > 3 else "低配当" if dividend_yield < 1 else "適正"
        analysis['dividend_yield'] = f"{dividend_yield*100:.2f}%"
    
    # 時価総額分析
    market_cap = info.get('marketCap')
    if isinstance(market_cap, (int, float)):
        if market_cap >= 1e12:
            analysis['market_cap'] = f"${market_cap/1e12:.2f}兆"
            analysis['size'] = "大型株"
        elif market_cap >= 1e9:
            analysis['market_cap'] = f"${market_cap/1e9:.2f}十億"
            analysis['size'] = "中型株"
        else:
            analysis['market_cap'] = f"${market_cap:,.2f}"
            analysis['size'] = "小型株"
    
    # 52週間の価格範囲分析
    high_52w = info.get('fiftyTwoWeekHigh')
    low_52w = info.get('fiftyTwoWeekLow')
    if all(isinstance(x, (int, float)) for x in [current_price, high_52w, low_52w]):
        price_range = ((current_price - low_52w) / (high_52w - low_52w)) * 100
        analysis['price_position'] = f"{price_range:.1f}%"
        if price_range > 80:
            analysis['price_level'] = "高値圏"
        elif price_range < 20:
            analysis['price_level'] = "安値圏"
        else:
            analysis['price_level'] = "中間圏"
    
    return analysis

def get_stock_price_alpha(symbol, api_key, outputsize='compact', market='US', max_retries=3, retry_delay=10):
    """
    Alpha Vantage APIを使用して株価データを取得する
    
    Args:
        symbol (str): 株価コード
        api_key (str): Alpha Vantage APIキー
        outputsize (str): 'compact'（直近100件）または'full'（全期間）
        market (str): 'US'（米国株）または'JP'（日本株）
        max_retries (int): 最大リトライ回数
        retry_delay (int): リトライ間の遅延（秒）
    
    Returns:
        pandas.DataFrame: 株価データ
    """
    for attempt in range(max_retries):
        try:
            # TimeSeriesオブジェクトの作成
            ts = TimeSeries(key=api_key, output_format='pandas')
            
            # 日次データの取得
            data, meta_data = ts.get_daily(symbol=symbol, outputsize=outputsize)
            
            # 列名を変更
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            return data
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error occurred: {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Maximum retries reached. Error: {e}")
                return None
    
    return None

def plot_stock_price(data, title, market='US'):
    """
    株価データをグラフで表示する
    """
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['Close'], label='Close')
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel(f'Stock Price ({"JPY" if market == "JP" else "USD"}）')
    plt.grid(True)
    plt.legend()
    # plt.show()

def analyze_stock_with_news(stock_data, info, news):
    """
    株価データとニュースを分析し、総合的な投資判断を提供する
    
    Args:
        stock_data (pandas.DataFrame): 株価データ
        info (dict): 会社情報
        news (list): ニュース記事のリスト
    
    Returns:
        str: 総合的な投資判断
    """
    try:
        # OpenAIの設定
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=OPENAI_API_KEY
        )
        
        # 株価分析結果の取得
        analysis = analyze_stock(stock_data, info)
        
        # 分析結果のテキスト化
        analysis_text = f"""
        株価分析結果:
        - 前日比: {analysis.get('price_change', 'N/A')} ({analysis.get('price_trend', 'N/A')})
        - PER: {analysis.get('pe_ratio', 'N/A')} ({analysis.get('pe_analysis', 'N/A')})
        - 配当利回り: {analysis.get('dividend_yield', 'N/A')} ({analysis.get('dividend_analysis', 'N/A')})
        - 時価総額: {analysis.get('market_cap', 'N/A')} ({analysis.get('size', 'N/A')})
        - 52週間価格帯: {analysis.get('price_position', 'N/A')} ({analysis.get('price_level', 'N/A')})
        """
        
        # ニュースの要約
        news_summary = ""
        if news:
            for article in news:
                news_summary += f"""
                タイトル: {article['title']}
                日付: {article['date']}
                要約: {article['summary']}
                """
        
        # プロンプトテンプレートの作成
        prompt = ChatPromptTemplate.from_template(
            """以下の株価分析結果とニュース情報を基に、総合的な投資判断を日本語で提供してください：
            
            株価分析結果:
            {analysis_text}
            
            最新ニュース:
            {news_summary}
            
            以下の点を含めて判断してください：
            1. 現在の株価水準の評価
            2. ニュースによる影響評価
            3. 短期的な投資判断
            4. 中長期的な投資判断
            5. リスク要因
            6. 具体的な投資戦略の提案
            
            回答は箇条書きで、簡潔にまとめてください。
            """
        )
        
        # チェーンの作成
        chain = prompt | llm
        
        # 総合判断の生成
        result = chain.invoke({
            "analysis_text": analysis_text,
            "news_summary": news_summary
        })
        
        return result.content
        
    except Exception as e:
        print(f"総合判断の生成中にエラーが発生しました: {e}")
        return "総合判断を生成できませんでした。"

if __name__ == "__main__":
    if not api_key:
        print("Error: ALPHA_VANTAGE_API_KEY is not set.")
        print("1. Get an API key from Alpha Vantage website")
        print("2. Set the API key in config.py")
        exit(1)
    
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set.")
        print("1. Get an API key from OpenAI website")
        print("2. Set the API key in config.py")
        exit(1)
    
    # テスラの株価を取得
    symbol = "TSLA"  # テスラのティッカーシンボル
    company_name = "Tesla"  # 会社名
    market = "US"    # 米国株を指定
    print(f"Fetching {symbol} stock data...")
    
    # 株価データの取得
    data = get_stock_price_alpha(symbol, api_key, outputsize='compact', market=market)
    
    if data is not None:
        # Yahoo Financeから追加情報を取得
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 分析結果を取得
        analysis = analyze_stock(data, info)
        
        print(f"\n{symbol} Stock Data (Last 100 Days):")
        print(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail())
        
        # 分析結果を表示
        print("\n=== 投資分析 ===")
        if 'price_change' in analysis:
            print(f"前日比: {analysis['price_change']} ({analysis['price_trend']})")
        
        if 'pe_ratio' in analysis:
            print(f"PER: {analysis['pe_ratio']} ({analysis['pe_analysis']})")
        
        if 'dividend_yield' in analysis:
            print(f"配当利回り: {analysis['dividend_yield']} ({analysis['dividend_analysis']})")
        
        if 'market_cap' in analysis:
            print(f"時価総額: {analysis['market_cap']} ({analysis['size']})")
        
        if 'price_position' in analysis:
            print(f"52週間価格帯: {analysis['price_position']} ({analysis['price_level']})")
        
        # ニュースの取得と表示
        print("\n=== 最新ニュースと分析 ===")
        news = get_stock_news(symbol, company_name, limit=3)
        
        if news:
            for idx, article in enumerate(news, 1):
                print(f"\n{idx}. {article['title']}")
                print(f"   日付: {article['date']}")
                print(f"   要約と分析:")
                print(f"   {article['summary']}")
                print(f"   URL: {article['url']}")
        else:
            print("ニュースは利用できません。")
        
        # 総合判断の表示
        print("\n=== 総合投資判断 ===")
        overall_analysis = analyze_stock_with_news(data, info, news)
        print(overall_analysis)
        
        # グラフを表示
        plot_stock_price(data, f"{symbol} Stock Price Trend", market=market)
        
    else:
        print("Failed to fetch data.")
        print("Please check the following:")
        print("1. Internet connection")
        print("2. API key validity")
        print("3. Ticker symbol accuracy") 