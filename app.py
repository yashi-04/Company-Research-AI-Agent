from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import time
import requests
from collections import Counter
from bs4 import BeautifulSoup
import json
from textblob import TextBlob
import praw
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
CORS(app)

FMP_API_KEY = "your_key"
NEWSAPI_API_KEY = "your_key"
RAPIDAPI_KEY = "your_key"
ALPHA_VANTAGE_API_KEY = "your_key"
reddit = praw.Reddit(
    client_id="client_id",
    client_secret="client_secret",
    user_agent="ua"
)

analyzer = SentimentIntensityAnalyzer()

def get_stock_price(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "datatype": "json",
        "apikey": ALPHA_VANTAGE_API_KEY,
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        if "Global Quote" in data:
            stock_info = data["Global Quote"]
            return {
                "symbol": symbol,
                "open": float(stock_info["02. open"]),
                "high": float(stock_info["03. high"]),
                "low": float(stock_info["04. low"]),
                "price": float(stock_info["05. price"]),
                "volume": int(stock_info["06. volume"]),
                "latest_trading_day": stock_info["07. latest trading day"],
                "previous_close": float(stock_info["08. previous close"]),
                "change": float(stock_info["09. change"]),
                "change_percent": stock_info["10. change percent"]
            }
        elif "Note" in data:
            # Rate limit exceeded
            print("API limit reached. Waiting for 60 seconds before retrying...")
            time.sleep(60)
            return get_stock_price(symbol)
        else:
            return {"error": "Invalid response from API"}
    
    elif response.status_code == 429:
        print("Rate limit exceeded. Retrying after 60 seconds...")
        time.sleep(60)
        return get_stock_price(symbol)
    
    else:
        return {"error": "Failed to fetch stock price"}

@app.route("/stock/<symbol>", methods=["GET"])
def stock_price(symbol):
    return jsonify(get_stock_price(symbol))


# Fetch Stock History (Financial Modeling Prep API)
# Fetch Stock Price History
def get_stock_history(symbol, period="1mo", interval="1d"):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?timeseries=30&apikey={FMP_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if "historical" in data and data["historical"]:
            dates = [entry["date"] for entry in data["historical"]]
            prices = [entry["close"] for entry in data["historical"]]
            return {"dates": dates, "prices": prices}
    return {"dates": [], "prices": []}


@app.route("/stock/history/<symbol>", methods=["GET"])
def stock_history(symbol):
    history = get_stock_history(symbol)
    return jsonify(history)




# Get Company Ticker
def get_ticker_from_name(company_name):
    url = f"https://financialmodelingprep.com/api/v3/search?query={company_name}&limit=1&apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data:
        return data[0]["symbol"]
    return None


# Get Company Details + Stock Market Data
def get_company_info(company_name):
    """Fetch company details, stock price, and financial data."""
    
    ticker = get_ticker_from_name(company_name)
    if not ticker:
        return {"error": "Company not found"}

    # API URLs
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
    stock_price_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"
    fin_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"

    # Fetch data
    profile_data = requests.get(profile_url).json()
    stock_data = requests.get(stock_price_url).json()
    fin_data = requests.get(fin_url).json()
    stock_history = get_stock_history(ticker)  

    # Validate API responses
    if not profile_data or "Error Message" in fin_data:
        return {"error": "Company or stock details not found"}

    # Extract data safely
    profile = profile_data[0] if isinstance(profile_data, list) and profile_data else {}
    market_cap = fin_data.get("MarketCapitalization", "N/A")
    ebitda = fin_data.get("EBITDA", "N/A")

    return {
        "Name": profile.get("companyName", "N/A"),
        "Industry": profile.get("industry", "N/A"),
        "Sector": profile.get("sector", "N/A"),
        "CEO": profile.get("ceo", "N/A"),
        "Cap": market_cap,
        "Website": profile.get("website", "N/A"),
        "Description": profile.get("description", "N/A"),
        "Headquarters": profile.get("address", "N/A"),
        "City": profile.get("city", "N/A"),
        "State": profile.get("state", "N/A"),
        "Country": profile.get("country", "N/A"),
        "Zip": profile.get("zip", "N/A"),
        "Employees": profile.get("fullTimeEmployees", "N/A"),
        "Phone": profile.get("phone", "N/A"),
        "Symbol": ticker,
        "Stock Price History": stock_history if stock_history else "N/A",
        "Ebitda": ebitda
    }

    return {"error": "Company or stock details not found"}


# Sentiment Analysis
def get_sentiment(text):
    """Perform sentiment analysis using TextBlob."""
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return "Positive"
    elif analysis.sentiment.polarity < 0:
        return "Negative"
    else:
        return "Neutral"


# Fetch Recent News
def get_recent_news(company_name, max_articles=5):
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={NEWSAPI_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get("articles", [])
        
        recent_news = []
        for article in articles[:max_articles]:
            recent_news.append({
                "headline": article.get("title", "N/A"),
                "source": article.get("source", {}).get("name", "N/A"),
                "date": article.get("publishedAt", "N/A"),
                "sentiment": get_sentiment(article.get("title"))
            })
        return recent_news
    else:
        return []

def get_reddit_posts(subreddits, query, limit=50):
    """Fetch posts from specified subreddits."""
    posts = []
    for subreddit in subreddits:
        for post in reddit.subreddit(subreddit).search(query, sort="new", limit=limit):
            posts.append(post.title + " " + post.selftext)
    return posts




def analyze_sentiment(texts):
    """Perform sentiment analysis using VADER and return sentiment counts."""
    results = []
    sentiment_labels = []

    for text in texts:
        sentiment_score = analyzer.polarity_scores(text)["compound"]
        sentiment_label = "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral"
        
        results.append({
            "text": text,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label
        })
        
        sentiment_labels.append(sentiment_label)

    # Determine sentiment distribution
    sentiment_counts = Counter(sentiment_labels)
    
    return pd.DataFrame(results), sentiment_counts

@app.route("/analyze_sentiment", methods=["POST"])
def analyze_sentiment_api():  # Renamed function to avoid conflict
    data = request.json.get("texts", [])
    df, sentiment_counts = analyze_sentiment(data)

    return jsonify({
        "sentiment_analysis": df.to_dict(orient="records"),
        "sentiment_counts": dict(sentiment_counts)
    })



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        company_name = request.form.get("company_name")

        if company_name:
            # Fetch company overview and stock market details
            overview = get_company_info(company_name)
            
            # Fetch recent news articles related to the company
            recent_news = get_recent_news(company_name)

            # Extract ticker symbol from company name
            ticker = get_ticker_from_name(company_name)

            # Fetch real-time stock price using the ticker
            stock_data = get_stock_price(ticker) if ticker else {"error": "Ticker not found"}

            return render_template(
                "index.html", 
                overview=overview, 
                recent_news=recent_news, 
                stock_data=stock_data, 
                company_name=company_name
            )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
