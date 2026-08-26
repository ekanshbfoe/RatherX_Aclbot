# 🕵️ WYR Stealth Scraper

A stealth web scraper for [wouldyourather.app](https://wouldyourather.app/) designed to bypass Cloudflare and anti-bot protections.

## Architecture

| Layer | Technology | Purpose |
|---|---|---|
| **Browser Masking** | `undetected-chromedriver` | Strips automation flags, spoofs browser fingerprint |
| **Network Camouflage** | Residential Proxy | Masks origin IP through residential endpoints |
| **Behavioral Jitter** | `random.uniform()` delays | Mimics human reading speed and interaction timing |
| **DOM Parsing** | `BeautifulSoup` + `lxml` | Robust extraction from JS-rendered HTML |

## Quick Start

```bash
# 1. Install dependencies
cd Scraper
pip install -r requirements.txt

# 2. (Optional) Configure proxy in config.py
#    Open config.py and fill in your residential proxy credentials

# 3. Run the scraper
python scraper.py
```

## Proxy Configuration

Open `config.py` and fill in your residential proxy credentials:

```python
PROXY_HOST = "gate.smartproxy.com"   # Your proxy provider's gateway
PROXY_PORT = "7000"                  # Port number
PROXY_USER = "spxxxx"               # Your username
PROXY_PASS = "your_password"         # Your password
```

**Recommended providers:**
- [Bright Data](https://brightdata.com/) — Largest residential pool
- [Oxylabs](https://oxylabs.io/) — Excellent geo-targeting
- [Smartproxy](https://smartproxy.com/) — Good budget option
- [IPRoyal](https://iproyal.com/) — Affordable residential IPs

> **Note:** The scraper works without a proxy for local testing, but you risk IP bans on repeated runs.

## Headless Mode

In `config.py`, toggle between visible and headless browser:

```python
HEADLESS_MODE = False   # Set True for cloud / server deployment
```

## Output Schema

The scraper outputs `data/questions_sfw.json` with this structure:

```json
[
  {
    "id": "sfw_0001",
    "question": "Would you rather Always be 10 minutes late or Always be 20 minutes early?",
    "option_blue": "Always be 10 minutes late",
    "option_red": "Always be 20 minutes early",
    "global_votes_blue": 38,
    "global_votes_red": 62
  }
]
```

## Tuning Parameters

All timing jitter is configurable in `config.py`:

| Parameter | Default | Purpose |
|---|---|---|
| `MAX_QUESTIONS` | `100` | Stop after this many unique questions |
| `PAGE_LOAD_WAIT` | `(5.0, 9.0)` | Initial page load delay range |
| `ACTION_DELAY` | `(2.5, 5.5)` | Delay before clicking an option |
| `SCROLL_DELAY` | `(1.8, 4.0)` | Delay between scrolling to next question |
| `VOTE_REVEAL_WAIT` | `(2.0, 4.0)` | Wait after voting for percentages to appear |

## File Structure

```
Scraper/
├── config.py           # All configurable parameters
├── scraper.py          # Main scraper script
├── requirements.txt    # Python dependencies
├── data/
│   └── questions_sfw.json   # Output (generated)
└── README.md
```
