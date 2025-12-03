# Color Palette
COLOR_DARK = "#03045e"   # Dark Blue
COLOR_MAIN = "#023e8a"   # Main Blue
COLOR_ACCENT = "#0096c7" # Accent Blue
COLOR_BG = "#f8f9fa"     # Light Gray Background

# Pre-defined list for Auto-complete
COMMON_TICKERS = [
    "VOO", "QQQ", "SCHD", "SPY", "VTI", "IVV", "ARKK", "SMH", "DIA", "IWM",
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOG", "GOOGL", "META", "TSLA", "NFLX",
    "AMD", "INTC", "QCOM", "AVGO", "TXN", "MU",
    "JPM", "BAC", "WFC", "C", "GS", "MS",
    "JNJ", "UNH", "LLY", "PFE", "ABBV", "MRK",
    "KO", "PEP", "PG", "COST", "WMT", "TGT",
    "XOM", "CVX", "COP",
    "BA", "LMT", "RTX",
    "PLTR", "COIN", "MSTR", "HOOD", "SQ"
]

# --- CSS STYLING ---
# The main theme is now set in .streamlit/config.toml
# This CSS is for custom component styling not covered by the theme.
APP_STYLE = f"""
    <style>
    /* 1. Global Headers (Font Family) */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Helvetica Neue', sans-serif;
    }}
    
    /* 2. Button Styling */
    .stButton>button {{ 
        background-color: {COLOR_MAIN} !important; 
        color: white !important; 
        border-radius: 6px; 
        font-weight: bold;
        border: none;
        padding: 10px 24px;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_ACCENT} !important;
    }}
    
    /* 3. Card Styling (Aligned) */
    .metric-card {{
        background-color: white !important; 
        padding: 25px; 
        border-radius: 10px;
        border-left: 6px solid {COLOR_MAIN}; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        color: #333;
        min-height: 180px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    
    .metric-card h2 {{
        margin: 10px 0 !important;
        font-size: 2rem !important;
        color: {COLOR_DARK} !important;
    }}
    .manifesto-card {{
        background-color: white !important; 
        padding: 30px; 
        border-radius: 8px;
        border: 1px solid #e0e0e0; 
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }}
    
    .law-box {{
        padding: 20px;
        border-radius: 6px;
        margin-bottom: 15px;
        border-left: 5px solid {COLOR_ACCENT};
        background-color: #fcfcfc;
        border: 1px solid #eee;
        color: #333;
    }}
    /* Data Table Styling */
    [data-testid="stDataFrame"] {{
        background-color: white !important;
        border: 1px solid #e0e0e0;
    }}
    </style>
    """