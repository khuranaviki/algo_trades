# Streamlit Market Analysis Application

A comprehensive Streamlit-based stock analysis system that combines technical analysis, fundamental analysis, and management insights to provide detailed investment recommendations.

## 🚀 Features

- **Real-time Stock Analysis** - Comprehensive multi-agent analysis system
- **Enhanced Data Extraction** - Advanced Screener.in data extraction with >98% accuracy
- **Management Insights** - ArthaLens management transcript and guidance extraction
- **Cost Tracking** - OpenAI API usage and cost tracking
- **PDF Export** - Complete analysis reports in PDF format
- **Interactive UI** - Streamlit-based web interface with real-time updates

## 📦 Core Components

### Main Analysis Engine
- **`streamlit_app_enhanced.py`** - Enhanced Streamlit web application
- **`EnhancedMultiAgent.py`** - The core multi-agent analysis system

### Data Collection Modules
- **`fundamental_scraper.py`** - Enhanced fundamental data collection from Screener.in
- **`enhanced_screener_extraction_v3.py`** - Latest enhanced Screener.in data extraction
- **`arthalens_extractor.py`** - ArthaLens management transcript and guidance extraction

### Integration & Utilities
- **`notion_integration.py`** - Notion database integration for storing analysis results
- **`openai_cost_tracker.py`** - OpenAI API usage and cost tracking

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd streamlit-market-analysis
```

### 2. Install Dependencies
```bash
pip install -r requirements_streamlit.txt
pip install -r requirements_multi_agent.txt
```

### 3. Set Up Environment Variables
Create a `.env` file with the following variables:
```bash
OPENAI_API_KEY=your_openai_api_key_here
NOTION_TOKEN=your_notion_token_here  # Optional
NOTION_DATABASE_ID=your_database_id_here  # Optional
```

## 🚀 Usage

### Running the Streamlit Application
```bash
streamlit run streamlit_app_enhanced.py
```

The application will be available at `http://localhost:8501`

### Direct Analysis (Python)
```python
from EnhancedMultiAgent import EnhancedMultiAgentStockAnalysis
import os

analyzer = EnhancedMultiAgentStockAnalysis(openai_api_key=os.getenv('OPENAI_API_KEY'))
results = analyzer.analyze_stock("AAPL", "Apple Inc", "Technology")
```

## 📊 Features Overview

### Multi-Agent Analysis
- **Technical Analysis Agent** - Chart patterns, indicators, and price action
- **Fundamental Analysis Agent** - Financial metrics, ratios, and valuation
- **Management Insights Agent** - Earnings call transcripts and guidance
- **Coordinator Agent** - Synthesizes all analysis into actionable recommendations

### Data Sources
- **Yahoo Finance** - Real-time stock data and historical prices
- **Screener.in** - Comprehensive fundamental data for Indian stocks
- **ArthaLens** - Management insights and earnings call transcripts

### Export Capabilities
- **PDF Reports** - Complete analysis in professional PDF format
- **JSON Data** - Structured data for further processing
- **Notion Integration** - Direct export to Notion databases

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for AI analysis
- `NOTION_TOKEN` - Optional for Notion integration
- `NOTION_DATABASE_ID` - Optional for Notion integration
- `OPENAI_MODEL` - Default model (defaults to 'gpt-4')

### Chrome WebDriver
The application requires Chrome WebDriver for web scraping. It will be automatically downloaded if not present.

## 📈 Analysis Output

Each analysis includes:
- **Executive Summary** with investment recommendation
- **Technical Analysis** with key levels and patterns
- **Fundamental Analysis** with financial metrics
- **Management Commentary** analysis
- **Risk Assessment** and position sizing recommendations
- **Historical Performance** comparison
- **Cost Tracking** for API usage

## 🛡️ Security

- Store API keys in `.env` file (never commit to version control)
- Use environment variables for all sensitive credentials
- Follow secure coding practices for API interactions

## 📝 Notes

- Analysis results are cached in `analysis_runs/` directory
- Screenshots are saved in `screener_screenshots/` directory
- API usage is logged in `openai_usage_log.json`
- Supports both Indian (.NS) and US stock symbols

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 