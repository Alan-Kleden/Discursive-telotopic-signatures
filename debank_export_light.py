"""
PORTFOLIO TRACKER FINAL - Solution complète
===========================================
Morpho est ajouté manuellement car non détecté par Moralis API
À vérifier mensuellement sur DeBank
"""

import requests
import csv
from datetime import datetime
import time

# ============================================================================
# CONFIGURATION
# ============================================================================
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjdlM2RiZTJjLTBmNzEtNDgyOC04NGM4LTgwZDAwMzVhNzlkYyIsIm9yZ0lkIjoiNDc0NzM2IiwidXNlcklkIjoiNDg4MzgxIiwidHlwZUlkIjoiMzQ5Y2NiYzctMjZmMi00OWUwLWE5NTMtNDA3ZjEzZmJiNzAyIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTk5MDU2NTEsImV4cCI6NDkxNTY2NTY1MX0.xbj4spwVxdqA31X8lii7b6aIvi4FJxqfO5o73VX42Bk"
WALLET_ADDRESS = "0x2bce4bb535f45b05c5cd1004345c23a892ee6733"

MORALIS_BASE = "https://deep-index.moralis.io/api/v2.2"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
REALT_API = "https://api.realtoken.community/v1/token"

moralis_headers = {
    "X-API-Key": MORALIS_API_KEY,
    "accept": "application/json"
}

price_cache = {}
realt_cache = None

# ============================================================================
# POSITIONS DEFI MANUELLES (MAJ mensuelle depuis DeBank)
# Dernière MAJ: 2025-10-08
# ============================================================================

# Positions DeFi Gnosis détectables automatiquement
GNOSIS_DEFI_RATES = {
    "AGNOUSDC": (1.0, "Aave V3"),
    "SPUSDC": (1.0, "Spark"),
}

# Positions DeFi NON détectables (à vérifier mensuellement sur DeBank)
MANUAL_DEFI_POSITIONS = [
    {
        "chain": "gnosis",
        "protocol": "Morpho",
        "position_type": "Lending",
        "symbol": "USDC",
        "balance": 14495.63,  # À mettre à jour depuis DeBank
        "note": "Morpho Clearstar USDC Reactor - Vérifié sur DeBank"
    },
]

# ============================================================================
# MORALIS API
# ============================================================================

def fetch_tokens_moralis(chain):
    """Tokens ERC20"""
    url = f"{MORALIS_BASE}/{WALLET_ADDRESS}/erc20"
    params = {"chain": chain}
    
    try:
        response = requests.get(url, headers=moralis_headers, params=params, timeout=10)
        response.raise_for_status()
        tokens = response.json()
        filtered = [t for t in tokens if float(t.get("balance", "0")) > 0 and not is_spam(t)]
        print(f"  ✓ {chain.upper()}: {len(filtered)} tokens")
        return filtered
    except Exception as e:
        print(f"  ✗ {chain.upper()}: {e}")
        return []

def fetch_native_balance(chain):
    """Balance native"""
    url = f"{MORALIS_BASE}/{WALLET_ADDRESS}/balance"
    params = {"chain": chain}
    
    try:
        response = requests.get(url, headers=moralis_headers, params=params, timeout=10)
        response.raise_for_status()
        return float(response.json().get("balance", 0)) / (10 ** 18)
    except:
        return 0.0

def fetch_defi_positions_eth():
    """Positions DeFi ETH (Moralis)"""
    url = f"{MORALIS_BASE}/wallets/{WALLET_ADDRESS}/defi/positions"
    params = {"chain": "eth"}
    
    try:
        response = requests.get(url, headers=moralis_headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            positions = data if isinstance(data, list) else data.get("result", [])
            if positions:
                print(f"  ✓ ETH DeFi: {len(positions)} positions")
            return positions
        return []
    except:
        return []

# ============================================================================
# PRIX
# ============================================================================

def fetch_realt_tokens():
    """RealT API"""
    global realt_cache
    if realt_cache:
        return realt_cache
    
    try:
        response = requests.get(REALT_API, timeout=15)
        if response.status_code == 200:
            realt_cache = response.json()
            print(f"  ✓ RealT API: {len(realt_cache)} tokens")
            return realt_cache
    except requests.exceptions.SSLError:
        try:
            response = requests.get(REALT_API, timeout=15, verify=False)
            if response.status_code == 200:
                realt_cache = response.json()
                print(f"  ✓ RealT API: {len(realt_cache)} tokens")
                return realt_cache
        except:
            pass
    except:
        pass
    
    print(f"  → RealT API indisponible")
    return []

def get_realtoken_price(symbol, name=""):
    """Prix RealToken"""
    tokens = fetch_realt_tokens()
    
    for token in tokens:
        token_short = token.get("shortName", "").upper()
        token_full = token.get("fullName", "").upper()
        
        if token_short in symbol.upper() or symbol.upper() in token_short:
            price = float(token.get("tokenPrice", 0))
            if price > 0:
                return price, "RealT API"
        
        if name and (token_full in name.upper() or name.upper() in token_full):
            price = float(token.get("tokenPrice", 0))
            if price > 0:
                return price, "RealT API"
    
    return 50.0, "RealT avg"

def get_coingecko_price(symbol):
    """Prix CoinGecko"""
    if symbol in price_cache:
        return price_cache[symbol]
    
    symbol_map = {
        "ETH": "ethereum",
        "USDC": "usd-coin",
        "DAI": "dai",
        "WXDAI": "xdai",
    }
    
    coin_id = symbol_map.get(symbol.upper())
    if not coin_id:
        return None
    
    try:
        url = f"{COINGECKO_BASE}/simple/price"
        response = requests.get(url, params={"ids": coin_id, "vs_currencies": "usd"}, timeout=10)
        if response.status_code == 200:
            price = response.json().get(coin_id, {}).get("usd", 0)
            price_cache[symbol] = price
            return price
    except:
        pass
    
    return None

def get_token_price(symbol, name=""):
    """Stratégie de prix"""
    symbol_upper = symbol.upper()
    
    if symbol_upper in ["USDC", "DAI", "USDT"]:
        return 1.0, "Stablecoin"
    
    if "REALTOKEN" in symbol_upper or "REALTOKEN" in name.upper():
        return get_realtoken_price(symbol, name)
    
    if symbol_upper in GNOSIS_DEFI_RATES:
        return 0.0, "DeFi Gnosis"
    
    cg_price = get_coingecko_price(symbol)
    if cg_price and cg_price > 0:
        return cg_price, "CoinGecko"
    
    if any(x in symbol_upper for x in ["LP", "WRAPPED", "REUSD"]):
        return 0.0, "Wrapped"
    
    return 0.0, "Unknown"

# ============================================================================
# GNOSIS DEFI RESOLVER
# ============================================================================

def resolve_gnosis_defi_positions(tokens):
    """Convertit tokens wrapped en positions DeFi"""
    positions = []
    
    for token in tokens:
        symbol = token.get("symbol", "").upper()
        
        if symbol in GNOSIS_DEFI_RATES:
            rate, protocol = GNOSIS_DEFI_RATES[symbol]
            
            decimals = token.get("decimals", 18)
            balance_raw = float(token.get("balance", 0))
            balance_normalized = balance_raw / (10 ** decimals) if decimals else balance_raw
            
            underlying_balance = balance_normalized / rate
            value_usd = underlying_balance
            
            positions.append({
                "protocol": protocol,
                "position_type": "Lending",
                "symbol": "USDC",
                "balance": underlying_balance,
                "value_usd": value_usd,
                "rate": rate,
                "source": "Auto-detected"
            })
    
    return positions

# ============================================================================
# UTILS
# ============================================================================

def is_spam(token):
    """Détecte spam"""
    symbol = token.get("symbol", "").upper()
    name = token.get("name", "").upper()
    text = f"{symbol} {name}"
    
    spam_keywords = ["AIRDROP", "CLAIM", "VISIT", "WWW.", "HTTP", "T.LY", "FYDE", "USD0"]
    if any(kw in text for kw in spam_keywords) or symbol == "UNDEFINED":
        return True
    
    balance_raw = float(token.get("balance", 0))
    decimals = token.get("decimals", 18)
    balance = balance_raw / (10 ** decimals) if decimals else balance_raw
    
    return balance > 1_000_000

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("  PORTFOLIO TRACKER FINAL - SOLUTION COMPLÈTE")
    print("  Wallet: " + WALLET_ADDRESS)
    print("=" * 80)
    
    chains = ["eth", "gnosis"]
    all_assets = []
    
    print("\n[1/6] Balances natives...")
    for chain in chains:
        balance = fetch_native_balance(chain)
        if balance > 0:
            symbol = "ETH" if chain == "eth" else "WXDAI"
            price, source = get_token_price(symbol)
            value = balance * price
            
            all_assets.append({
                "chain": chain,
                "type": "native",
                "protocol": "Wallet",
                "position_type": "Native",
                "symbol": symbol,
                "name": "Native Token",
                "balance": balance,
                "price_usd": price,
                "value_usd": value,
                "source": source
            })
        time.sleep(0.3)
    
    print("\n[2/6] Tokens wallet...")
    all_tokens = {}
    for chain in chains:
        tokens = fetch_tokens_moralis(chain)
        all_tokens[chain] = tokens
        time.sleep(0.3)
    
    print("\n[3/6] DeFi Ethereum (Moralis API)...")
    eth_defi = fetch_defi_positions_eth()
    
    for pos in eth_defi:
        protocol = pos.get("protocol_name", "Unknown")
        value = float(pos.get("balance_usd", 0))
        
        if value > 0:
            all_assets.append({
                "chain": "eth",
                "type": "defi",
                "protocol": protocol,
                "position_type": pos.get("position_type", ""),
                "symbol": pos.get("token_symbol", "UNKNOWN"),
                "name": f"{protocol} - {pos.get('position_type', '')}",
                "balance": float(pos.get("balance", 0)),
                "price_usd": 0,
                "value_usd": value,
                "source": "Moralis DeFi"
            })
    
    print("\n[4/6] DeFi Gnosis (Auto-détection)...")
    gnosis_defi = resolve_gnosis_defi_positions(all_tokens.get("gnosis", []))
    
    for pos in gnosis_defi:
        print(f"  ✓ {pos['protocol']}: ${pos['value_usd']:,.2f}")
        
        all_assets.append({
            "chain": "gnosis",
            "type": "defi",
            "protocol": pos["protocol"],
            "position_type": pos["position_type"],
            "symbol": pos["symbol"],
            "name": f"{pos['protocol']} - {pos['position_type']}",
            "balance": pos["balance"],
            "price_usd": 1.0,
            "value_usd": pos["value_usd"],
            "source": pos["source"]
        })
    
    print("\n[5/6] DeFi Positions manuelles...")
    for pos in MANUAL_DEFI_POSITIONS:
        value = pos["balance"]
        print(f"  ✓ {pos['protocol']}: ${value:,.2f} (manuel)")
        
        all_assets.append({
            "chain": pos["chain"],
            "type": "defi",
            "protocol": pos["protocol"],
            "position_type": pos["position_type"],
            "symbol": pos["symbol"],
            "name": f"{pos['protocol']} - {pos['position_type']}",
            "balance": pos["balance"],
            "price_usd": 1.0,
            "value_usd": value,
            "source": "Manual (DeBank)"
        })
    
    print("\n[6/6] Prix REALTOKENs...")
    fetch_realt_tokens()
    
    for chain, tokens in all_tokens.items():
        for token in tokens:
            symbol = token.get("symbol", "UNKNOWN")
            
            if symbol.upper() in GNOSIS_DEFI_RATES:
                continue
            
            name = token.get("name", "")
            decimals = token.get("decimals", 18)
            balance_raw = float(token.get("balance", 0))
            balance = balance_raw / (10 ** decimals) if decimals else balance_raw
            
            price, source = get_token_price(symbol, name)
            value = balance * price
            
            all_assets.append({
                "chain": chain,
                "type": "token",
                "protocol": "Wallet",
                "position_type": "Token",
                "symbol": symbol,
                "name": name[:50],
                "balance": balance,
                "price_usd": price,
                "value_usd": value,
                "source": source
            })
    
    # Export
    print("\n[Export] Génération...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"portfolio_{timestamp}.csv"
    
    # CSV compatible Excel français (virgule comme décimale, point-virgule comme séparateur)
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:  # BOM pour Excel
        writer = csv.DictWriter(f, fieldnames=[
            "chain", "type", "protocol", "position_type", "symbol",
            "name", "balance", "price_usd", "value_usd", "source"
        ], delimiter=';')  # Point-virgule pour Excel français
        writer.writeheader()
        
        total_per_chain = {"eth": 0.0, "gnosis": 0.0}
        total_per_type = {"wallet": 0.0, "defi": 0.0}
        
        print("\n  Assets > $50:")
        print("  " + "-" * 76)
        
        for asset in sorted(all_assets, key=lambda x: x["value_usd"], reverse=True):
            total_per_chain[asset["chain"]] += asset["value_usd"]
            
            if asset["type"] == "defi":
                total_per_type["defi"] += asset["value_usd"]
            else:
                total_per_type["wallet"] += asset["value_usd"]
            
            if asset["value_usd"] > 50:
                print(f"  {asset['name']:45s} ${asset['value_usd']:>10,.2f}")
            
            # Conversion des nombres avec virgule pour Excel français
            row = {}
            for k, v in asset.items():
                if k in ['balance', 'price_usd', 'value_usd']:
                    # Convertir le point décimal en virgule pour Excel FR
                    row[k] = str(v).replace('.', ',')
                else:
                    row[k] = str(v)
            
            writer.writerow(row)
    
    # Résumé
    print("\n" + "=" * 80)
    print("  RÉSUMÉ FINAL")
    print("=" * 80)
    
    total = sum(total_per_chain.values())
    
    print("\n  Par chaîne:")
    for chain, value in total_per_chain.items():
        pct = (value / total * 100) if total > 0 else 0
        print(f"    {chain.upper():10s} ${value:>14,.2f}  ({pct:>5.1f}%)")
    
    print("\n  Par catégorie:")
    print(f"    {'Wallet':10s} ${total_per_type['wallet']:>14,.2f}")
    print(f"    {'DeFi':10s} ${total_per_type['defi']:>14,.2f}")
    
    print("\n  " + "-" * 76)
    print(f"  {'TOTAL':10s} ${total:>14,.2f}")
    
    # Comparaison
    debank_ref = 123191
    diff = total - debank_ref
    diff_abs = abs(diff)
    diff_pct = (diff_abs / debank_ref * 100)
    
    print("\n  vs DeBank ($123,191):")
    print(f"    Calculé:       ${total:>14,.2f}")
    print(f"    Écart:         ${diff:>+14,.2f} ({diff_pct:.2f}%)")
    
    if diff_pct < 1:
        verdict = "✅ EXCELLENT"
    elif diff_pct < 2:
        verdict = "✓ TRÈS BON"
    elif diff_pct < 5:
        verdict = "⚠ Acceptable"
    else:
        verdict = "❌ Vérifier MANUAL_DEFI_POSITIONS"
    
    print(f"    {verdict}")
    
    print(f"\n  📝 Maintenance mensuelle:")
    print(f"     1. Vérifier MANUAL_DEFI_POSITIONS sur DeBank")
    print(f"     2. Mettre à jour les balances si changement")
    
    print(f"\n  ✓ Export: {filename}")
    print(f"  ✓ Format: Excel français (virgule décimale, point-virgule séparateur)")
    print(f"  ✓ Encodage: UTF-8 avec BOM (compatible Excel)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()