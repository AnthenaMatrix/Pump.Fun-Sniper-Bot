# Pump.Fun Sniper Bot

**Pump.Fun Sniper Bot** is an advanced Python script designed to help crypto enthusiasts snipe low-cap gems and capitalize on opportunities in the fast-paced crypto market. This bot is tailor-made for the **Pump.fun** platform, allowing users to automate the process of discovering, buying, and selling tokens based on their preferences. It simplifies complex transactions, adds efficiency, and ensures you never miss a beat.

## 🚀 Features

### 1. **Automatic Token Sniping**
- Identify low-cap gems on the Pump.fun platform.
- Automatically execute buy and sell orders for tokens meeting your criteria.

### 2. **Customizable Parameters**
- Set minimum SOL allocation with `--min`.
- Use `--max-coins` to limit the number of tokens you want to buy.
- Adjust `--slippage` to account for market volatility.
- Control transaction speed with `--priority-fee`.
- Specify `--sell-percentage` for partial sells at target thresholds.

### 3. **Wallet Flexibility**
- Supports both **Private Key** and **Seed Phrase** for wallet access.
- Securely sign and send transactions via Solana's mainnet.

### 4. **Real-Time Monitoring**
- Monitor token performance and adjust strategies on the fly.
- Automatically trigger sell orders when price thresholds are met.

## 📦 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/AnthenaMatrix/Pump.Fun-Sniper-Bot.git
cd Pump.Fun-Sniper-Bot
```
### Step 2: Install Dependencies
Make sure you have Python 3.8+ installed. Then install the required dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Your Wallet
1. **Private Key:** Copy your wallet's private key.

## 🛠️ Usage

### Private Key Example
```bash
python3 PumpFunBot.py --min 0.1 --private-key "your_private_key" --max-coins 5 --slippage 5 --priority-fee 0.002 --sell-percentage 60
```

### Explanation of Parameters:
- `--min`: Minimum SOL to allocate for each token purchase.
- `--private-key`: Use your private key to access your wallet.
- `--max-coins`: Limit the number of tokens to buy (default is 3).
- `--slippage`: Percentage slippage tolerance for transactions.
- `--priority-fee`: Additional fee (in SOL) to prioritize transactions.
- `--sell-percentage`: Percentage of coins to sell when the target price threshold is reached.

## 🔐 Security Disclaimer
Ensure you:
- Only run the bot on a secure system.
- Do not expose your private key or seed phrase publicly.
- Use at your own risk. The crypto market is volatile, and profits are not guaranteed.

## 🛡️ License
This project is open-source and available under the MIT License. See the LICENSE file for more details.

## 🤝 Contributing
Pull requests are welcome. For significant changes, please open an issue first to discuss what you would like to change.

## 🌟 Support
If you find this tool useful, give the repository a ⭐ on GitHub. Happy sniping!

