# 🪙 Crypto Price Tracker

A full-featured **CLI + GUI** Python application for tracking real-time cryptocurrency prices using the **CoinGecko API** (no API key required).

---

## 📸 Features

| Feature | CLI | GUI |
|---|---|---|
| Live prices (10+ coins) | ✅ | ✅ |
| 24h change, market cap, volume | ✅ | ✅ |
| Search by name or symbol | ✅ | ✅ |
| Save price history (JSON + CSV) | ✅ | ✅ |
| View history with filters | ✅ | ✅ |
| Price alerts (above/below) | ✅ | ✅ |
| Portfolio tracker with P&L | ✅ | ✅ |
| Auto-refresh every 30s | — | ✅ |
| Color-coded price changes | ✅ | ✅ |

---

##  Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

> **Tkinter** is included with Python. If missing on Linux: `sudo apt install python3-tk`

### 2. Run CLI Application

```bash
python cli.py
```

### 3. Run GUI Dashboard

```bash
python gui.py
```

---

##  Project Structure

```
crypto_tracker/
├── cli.py                  # CLI entry point
├── gui.py                  # Tkinter GUI entry point
├── requirements.txt
├── README.md
├── modules/
│   ├── api.py              # CoinGecko API integration
│   ├── storage.py          # JSON + CSV price history
│   ├── display.py          # CLI colors and formatting
│   ├── alerts.py           # Price alert system
│   └── portfolio.py        # Portfolio tracking + P&L
└── data/
    ├── price_history.json  # Auto-generated price history
    ├── price_history.csv   # Same data in CSV format
    ├── alerts.json         # Saved price alerts
    └── portfolio.json      # Your holdings
```

---

##  API Integration

This app uses the **CoinGecko Public API** — no API key required.

| Endpoint | Purpose |
|---|---|
| `/coins/markets` | Fetch live prices, market cap, volume, 24h change |
| `/search` | Search coins by name/symbol |

**Rate limit:** ~30 calls/minute on the free tier.

### Supported Coins (default)

Bitcoin, Ethereum, BNB, Solana, XRP, Cardano, Dogecoin, Polkadot, Litecoin, Chainlink

Any CoinGecko coin can be searched by name or symbol.

---

##  CLI Menu

```
1.  View Live Prices       → Fetches and displays all tracked coins
2.  Search Coin            → Search any coin, view detail, add to tracker
3.  Save Current Prices    → Saves to data/price_history.json + .csv
4.  View Price History     → Browse stored snapshots, filter by coin
5.  Set Price Alert        → Alert when coin goes above/below a price
6.  View Portfolio         → Track holdings and P&L
7.  Exit
```

---

##  Data Storage

Price history is stored in two formats automatically:

**JSON** (`data/price_history.json`):
```json
[
  {
    "timestamp": "2025-05-03 14:30:00",
    "id": "bitcoin",
    "name": "Bitcoin",
    "symbol": "BTC",
    "price_usd": 96423.50,
    "market_cap": 1905000000000,
    "change_24h": 2.34,
    "volume_24h": 42300000000
  }
]
```

**CSV** (`data/price_history.csv`):
```
timestamp,id,name,symbol,price_usd,market_cap,change_24h,volume_24h
2025-05-03 14:30:00,bitcoin,Bitcoin,BTC,96423.50,1905000000000,2.34,42300000000
```

---

##  Configuration

In `modules/api.py`, you can:
- Add coins to `DEFAULT_COINS` list
- Add coin aliases to the `COIN_IDS` dictionary

---

##  Error Handling

| Scenario | Behavior |
|---|---|
| No internet | Friendly error message, no crash |
| API timeout | Timeout error with retry prompt |
| API rate limit | HTTP 429 error with message |
| Invalid coin name | Falls back to search API |
| Malformed data | Graceful `None` fallbacks |

---

##  Requirements

- Python 3.10+
- `requests` library
- `tkinter` (bundled with Python, for GUI only)
- Internet connection

---

##  License

MIT License. Free for personal and educational use.

---

##  Acknowledgements

- [CoinGecko API](https://www.coingecko.com/en/api) — Free crypto market data
# Crypto-Price-Tracker-By-Muhammad Junaid
# Crypto-Price-Tracker-
