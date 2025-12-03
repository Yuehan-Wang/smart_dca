# Smart DCA Portfolio Manager

**[Live Demo](https://yuehan-wang-smart-dca-app-cujodf.streamlit.app/)**

A Streamlit web application designed to implement and backtest a dynamic Dollar-Cost Averaging (DCA) strategy. Instead of investing a fixed amount on a fixed schedule, this tool adjusts your investment based on market conditions, aiming to buy more during downturns and less during periods of euphoria.

## Key Features

- **Dynamic Investment Logic:** Automatically calculates investment multipliers based on technical indicators like RSI, Moving Averages, Bollinger Bands, and the VIX.
- **Strategy Backtesting:** Compare the performance of the "Smart DCA" strategy against a standard DCA approach over historical data.
- **Action Dashboard:** Get a real-time recommendation on how much to invest based on current market data.
- **Email Subscriptions:** Subscribe to receive automated weekly investment recommendations directly to your inbox.
- **Historical Inspector:** Look up what the strategy would have recommended on any specific day in the past.
- **Customizable Portfolio:** Select from a list of common tickers or add your own, and set custom percentage allocations.
- **Flexible Investment Options:** Support for initial investments, rebalancing, and weekly or monthly contributions.

## Email Subscription Setup

Users can subscribe to receive automated investment recommendations via email. See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed setup instructions.
