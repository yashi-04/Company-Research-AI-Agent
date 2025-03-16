# Company-Research-AI-Agent
Overview

The AI-Powered Research Agent is designed to gather and analyze company data using web scraping, API integration, and natural language processing (NLP). It retrieves information on company overviews, financials, employee details, news, social media sentiment, competitor analysis, and growth trends, providing actionable insights for users.

### Features

Company Overview: Retrieves key details such as name, industry, location, and market position.

Financial Data: Fetches revenue, stock performance, and financial metrics (if available via APIs).

Employee Information: Gathers workforce details, leadership profiles, and hiring trends.

News & Sentiment Analysis: Collects news articles and applies NLP-based sentiment analysis.

Social Media Analysis: Monitors sentiment and trends from platforms like Twitter and LinkedIn.

Competitor Analysis: Identifies industry competitors and compares key metrics.

Growth Trends: Analyzes historical data for predictive insights.

Technology Stack

Backend: Python (Flask)

APIs Used: Financial APIs(Alpha Vantage,Financial Modelling Prep etc), Social Media APIs, News APIs

Machine Learning: NLP models for sentiment analysis (TextBlob, vaderSentiment)

Frontend:
HTML
CSS
Javascript

Installation

Clone the repository:

git clone https://github.com/yashi-04/Company-Research-AI-Agent.git
cd ai-research-agent

Install dependencies:

pip install -r requirements.txt

Set up API keys in an .env file

Run the application:

python app.py

#### Usage

* Fetch company data: Access http://localhost:5000/company?name={company_name} to retrieve company's data.

* Analyze sentiment: The agent will process news sentiment.


#### Future Enhancements

* Support for more data sources

* Advanced AI-driven predictions

* Enhanced visualization dashboards

Contributors

Yashi Sharma 

#### License

This project is licensed under the MIT License.
