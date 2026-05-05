#!/usr/bin/env python3
"""
Crypto Price Tracker - CLI Application
Real-time cryptocurrency price tracking using CoinGecko API
"""

import sys
import time
import threading

# Ensure modules are importable
import os
sys.path.insert(0, os.path.dirname(__file__))

from modules import api, storage, display, alerts, portfolio

# Tracked coins
tracked_coins = list(api.DEFAULT_COINS)
_last_data = []
_auto_refresh = False
_refresh_thread = None


def do_refresh():
    global _last_data
    try:
        display.print_info("Fetching live prices...")
        data = api.fetch_prices(tracked_coins)
        _last_data = data or []
        return data
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        display.print_error(str(e))
        return None


def menu_view_prices():
    data = do_refresh()
    if data:
        display.print_prices_table(data)
        triggered = alerts.check_alerts(data)
        for msg in triggered:
            print(display.yellow(f"\n  {msg}"))
        if triggered:
            print()
    input(display.dim("  Press Enter to continue..."))


def menu_search():
    query = display.prompt("Enter coin name or symbol (e.g. bitcoin, eth, sol)")
    if not query:
        return
    display.print_info(f"Searching for '{query}'...")
    try:
        coin_id = api.resolve_coin_id(query)
        if not coin_id:
            # Try search API
            results = api.search_coin(query)
            if not results:
                display.print_error(f"No coin found for '{query}'")
                return
            print(f"\n  {display.bold('Search Results:')}\n")
            for i, r in enumerate(results[:5], 1):
                print(f"  {display.yellow(str(i))}. {r['name']} ({r.get('symbol','?').upper()}) — ID: {display.dim(r['id'])}")
            choice = display.prompt("Enter number to view details (or Enter to skip)")
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(results[:5]):
                    coin_id = results[idx]["id"]
                else:
                    return
            else:
                return

        coin = api.fetch_single_coin(coin_id)
        if coin:
            display.print_coin_detail(coin)
            add = display.prompt("Add to tracked coins? (y/n)")
            if add.lower() == "y" and coin_id not in tracked_coins:
                tracked_coins.append(coin_id)
                display.print_success(f"{coin['name']} added to tracked coins!")
        else:
            display.print_error("Could not fetch coin data.")
    except Exception as e:
        display.print_error(str(e))
    input(display.dim("  Press Enter to continue..."))


def menu_save_data():
    if not _last_data:
        display.print_info("Fetching data first...")
        data = do_refresh()
    else:
        data = _last_data

    if not data:
        display.print_error("No data to save.")
        input(display.dim("  Press Enter to continue..."))
        return

    count, ts = storage.save_prices(data)
    display.print_success(f"Saved {count} coin records at {ts}")
    display.print_info(f"Files:\n    JSON: data/price_history.json\n    CSV:  data/price_history.csv")
    input(display.dim("  Press Enter to continue..."))


def menu_history():
    summary = storage.get_history_summary()
    if summary["total_records"] == 0:
        display.print_info("No history saved yet. Use 'Save Data' first.")
        input(display.dim("  Press Enter to continue..."))
        return

    print(f"\n  {display.bold('History Summary:')}")
    print(f"  Total records : {display.yellow(str(summary['total_records']))}")
    print(f"  Coins tracked : {', '.join(summary['coins'][:8])}")
    print(f"  From          : {display.dim(str(summary['earliest']))}")
    print(f"  To            : {display.dim(str(summary['latest']))}")

    coin_filter = display.prompt("\n  Filter by coin ID (Enter for all, e.g. 'bitcoin')")
    coin_filter = coin_filter.strip() or None
    records = storage.load_history(coin_id=coin_filter)
    display.print_history_table(records, coin_filter)
    input(display.dim("  Press Enter to continue..."))


def menu_alerts():
    existing = alerts.list_alerts()
    print(f"\n  {display.bold('Active Alerts:')} {display.dim(f'({len(existing)} total)')}")
    if existing:
        for i, a in enumerate(existing, 1):
            status = display.green("✓ Active") if not a["triggered"] else display.dim("✓ Triggered")
            cond = display.yellow("ABOVE") if a["condition"] == "above" else display.red("BELOW")
            print(f"  {i}. {a['coin_name']} {cond} ${a['threshold']:,.2f} — {status}")
    else:
        print(display.dim("  No alerts set."))

    print()
    action = display.prompt("Add new alert? (y/n)")
    if action.lower() != "y":
        input(display.dim("\n  Press Enter to continue..."))
        return

    coin_q = display.prompt("Enter coin (e.g. bitcoin, eth)")
    coin_id = api.resolve_coin_id(coin_q)
    if not coin_id:
        display.print_error(f"Coin '{coin_q}' not found.")
        input(display.dim("  Press Enter to continue..."))
        return

    coin_data = api.fetch_single_coin(coin_id)
    if not coin_data:
        display.print_error("Could not fetch coin.")
        input(display.dim("  Press Enter to continue..."))
        return

    display.print_coin_detail(coin_data)
    cond = display.prompt("Alert when price is 'above' or 'below'").lower()
    if cond not in ("above", "below"):
        display.print_error("Invalid condition. Use 'above' or 'below'.")
        input(display.dim("  Press Enter to continue..."))
        return

    try:
        threshold = float(display.prompt(f"Enter threshold price in USD"))
    except ValueError:
        display.print_error("Invalid price.")
        input(display.dim("  Press Enter to continue..."))
        return

    alerts.add_alert(coin_id, coin_data["name"], cond, threshold)
    display.print_success(f"Alert set: {coin_data['name']} {cond} ${threshold:,.2f}")
    input(display.dim("  Press Enter to continue..."))


def menu_portfolio():
    data = do_refresh() if not _last_data else _last_data
    if not data:
        display.print_error("Could not fetch prices.")
        input(display.dim("  Press Enter to continue..."))
        return

    holdings = portfolio.get_portfolio_value(data)

    print(f"\n  {display.bold('PORTFOLIO')}\n")
    if not holdings:
        print(display.dim("  No holdings yet."))
    else:
        header = f"  {'COIN':<20} {'AMOUNT':>12} {'BUY PRICE':>14} {'NOW':>14} {'VALUE':>14} {'P&L':>14}"
        print(display.bold(header))
        print(display.dim("  " + "─" * 90))
        total_value = 0
        total_pnl = 0
        for h in holdings:
            pnl_str = display.green(f"+${h['pnl']:,.2f}") if h["pnl"] >= 0 else display.red(f"-${abs(h['pnl']):,.2f}")
            pct = display.green(f"+{h['pnl_pct']:.1f}%") if h["pnl_pct"] >= 0 else display.red(f"{h['pnl_pct']:.1f}%")
            print(f"  {h['name']:<20} {h['amount']:>12.4f} {display.fmt_price(h['buy_price']) if hasattr(display, 'fmt_price') else f'${h[\"buy_price\"]:,.2f}':>14} "
                  f"{f'${h[\"current_price\"]:,.2f}':>14} {f'${h[\"current_value\"]:,.2f}':>14} {pnl_str:>22} ({pct})")
            total_value += h["current_value"]
            total_pnl += h["pnl"]
        print(display.dim("  " + "─" * 90))
        total_pnl_str = display.green(f"+${total_pnl:,.2f}") if total_pnl >= 0 else display.red(f"-${abs(total_pnl):,.2f}")
        print(f"  {display.bold('TOTAL'):>20}{'':>28} {display.bold(f'${total_value:,.2f}'):>28} {total_pnl_str:>22}")

    print()
    add = display.prompt("Add holding? (y/n)")
    if add.lower() == "y":
        coin_q = display.prompt("Coin (e.g. bitcoin, eth)")
        coin_id = api.resolve_coin_id(coin_q)
        if not coin_id:
            display.print_error("Coin not found.")
        else:
            coin_info = api.fetch_single_coin(coin_id)
            if coin_info:
                try:
                    amount = float(display.prompt(f"Amount of {coin_info['name']} you hold"))
                    buy_price = float(display.prompt("Your average buy price (USD)"))
                    portfolio.add_holding(coin_id, coin_info["name"], coin_info["symbol"], amount, buy_price)
                    display.print_success(f"Added {amount} {coin_info['symbol'].upper()} to portfolio!")
                except ValueError:
                    display.print_error("Invalid number.")

    input(display.dim("\n  Press Enter to continue..."))


def main():
    global _last_data
    display.clear()
    display.print_banner()
    print(display.cyan("  Welcome to Crypto Price Tracker!"))
    print(display.dim(f"  Tracking {len(tracked_coins)} coins by default. Data from CoinGecko.\n"))

    while True:
        display.print_menu()
        choice = display.prompt("Enter your choice (1-7)")

        if choice == "1":
            display.clear()
            menu_view_prices()
        elif choice == "2":
            display.clear()
            menu_search()
        elif choice == "3":
            display.clear()
            menu_save_data()
        elif choice == "4":
            display.clear()
            menu_history()
        elif choice == "5":
            display.clear()
            menu_alerts()
        elif choice == "6":
            display.clear()
            menu_portfolio()
        elif choice == "7":
            print(display.cyan("\n  Thanks for using Crypto Price Tracker. Goodbye! 👋\n"))
            sys.exit(0)
        else:
            display.print_error("Invalid choice. Please enter 1-7.")


if __name__ == "__main__":
    main()
