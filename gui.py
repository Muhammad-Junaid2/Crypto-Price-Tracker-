#!/usr/bin/env python3
"""
Crypto Price Tracker - Tkinter GUI
A modern dashboard for tracking cryptocurrency prices
"""

import sys
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from modules import api, storage, alerts, portfolio

# ─── Palette ──────────────────────────────────────────────────────────────────
BG       = "#0d1117"
BG2      = "#161b22"
BG3      = "#21262d"
BORDER   = "#30363d"
ACCENT   = "#58a6ff"
GREEN    = "#3fb950"
RED      = "#f85149"
YELLOW   = "#e3b341"
TEXT     = "#e6edf3"
MUTED    = "#8b949e"
CARD_BG  = "#1c2128"


class CryptoTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Price Tracker")
        self.root.configure(bg=BG)
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)

        self._data = []
        self._auto_refresh = tk.BooleanVar(value=False)
        self._refresh_interval = 30
        self._refresh_thread = None
        self._stop_refresh = threading.Event()

        self._build_ui()
        self._fetch_data()

    # ── UI Building ───────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_main()
        self._build_status_bar()

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG, pady=10)
        header.pack(fill="x", padx=20)

        left = tk.Frame(header, bg=BG)
        left.pack(side="left")

        tk.Label(left, text="₿ CRYPTO TRACKER", font=("Courier", 20, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(left, text="  Real-time prices", font=("Courier", 11),
                 bg=BG, fg=MUTED).pack(side="left", padx=10)

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")

        self._time_label = tk.Label(right, text="", font=("Courier", 11),
                                     bg=BG, fg=MUTED)
        self._time_label.pack(side="right", padx=10)
        self._update_clock()

        btn_style = {"font": ("Courier", 10, "bold"), "relief": "flat",
                     "padx": 14, "pady": 6, "cursor": "hand2"}

        tk.Button(right, text="⟳ REFRESH", bg=ACCENT, fg=BG,
                  command=self._fetch_data, **btn_style).pack(side="right", padx=4)

        tk.Button(right, text="💾 SAVE", bg=BG3, fg=TEXT,
                  command=self._save_data, **btn_style).pack(side="right", padx=4)

        # Auto-refresh toggle
        auto_frame = tk.Frame(right, bg=BG3, bd=0, relief="flat",
                               padx=10, pady=4)
        auto_frame.pack(side="right", padx=4)
        tk.Label(auto_frame, text="Auto (30s)", font=("Courier", 10),
                 bg=BG3, fg=MUTED).pack(side="left")
        tk.Checkbutton(auto_frame, variable=self._auto_refresh, bg=BG3,
                       fg=ACCENT, activebackground=BG3, selectcolor=BG3,
                       command=self._toggle_auto_refresh).pack(side="left")

    def _build_main(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Left sidebar: search + alerts + portfolio
        sidebar = tk.Frame(main, bg=BG2, width=280, bd=1, relief="flat")
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # Right: price table
        right_frame = tk.Frame(main, bg=BG)
        right_frame.pack(side="left", fill="both", expand=True)
        self._build_price_table(right_frame)

    def _build_sidebar(self, parent):
        # Search
        sec = self._sidebar_section(parent, "🔍 SEARCH COIN")
        self._search_var = tk.StringVar()
        entry = tk.Entry(sec, textvariable=self._search_var, font=("Courier", 11),
                         bg=BG3, fg=TEXT, insertbackground=ACCENT,
                         relief="flat", bd=0)
        entry.pack(fill="x", padx=10, pady=4, ipady=6)
        entry.bind("<Return>", lambda e: self._do_search())
        tk.Button(sec, text="Search", font=("Courier", 10, "bold"),
                  bg=ACCENT, fg=BG, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._do_search).pack(pady=(0, 10))

        # Alerts
        sec2 = self._sidebar_section(parent, "🚨 PRICE ALERTS")
        self._alerts_list = tk.Text(sec2, font=("Courier", 9), bg=BG3, fg=TEXT,
                                     relief="flat", bd=0, height=6,
                                     state="disabled", wrap="word")
        self._alerts_list.pack(fill="x", padx=10, pady=4)
        tk.Button(sec2, text="Add Alert", font=("Courier", 10, "bold"),
                  bg=BG3, fg=ACCENT, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._add_alert_dialog).pack(pady=(0, 10))
        self._refresh_alerts_display()

        # Portfolio summary
        sec3 = self._sidebar_section(parent, "💼 PORTFOLIO")
        self._portfolio_text = tk.Text(sec3, font=("Courier", 9), bg=BG3, fg=TEXT,
                                        relief="flat", bd=0, height=8,
                                        state="disabled", wrap="word")
        self._portfolio_text.pack(fill="x", padx=10, pady=4)
        tk.Button(sec3, text="Add Holding", font=("Courier", 10, "bold"),
                  bg=BG3, fg=GREEN, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._add_holding_dialog).pack(pady=(0, 10))

    def _sidebar_section(self, parent, title):
        frame = tk.Frame(parent, bg=BG2)
        frame.pack(fill="x", padx=0, pady=1)
        tk.Label(frame, text=title, font=("Courier", 10, "bold"),
                 bg=BG3, fg=MUTED, anchor="w", padx=12, pady=6).pack(fill="x")
        return frame

    def _build_price_table(self, parent):
        # Title
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="LIVE PRICES", font=("Courier", 13, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        self._last_update_lbl = tk.Label(top, text="", font=("Courier", 10),
                                          bg=BG, fg=MUTED)
        self._last_update_lbl.pack(side="right")

        # Table
        cols = ("rank", "name", "symbol", "price", "change_24h", "market_cap", "volume")
        col_labels = {"rank": "#", "name": "Coin", "symbol": "Symbol",
                      "price": "Price (USD)", "change_24h": "24h Change",
                      "market_cap": "Market Cap", "volume": "Volume 24h"}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Crypto.Treeview",
                         background=CARD_BG, foreground=TEXT,
                         fieldbackground=CARD_BG, rowheight=34,
                         font=("Courier", 11), borderwidth=0)
        style.configure("Crypto.Treeview.Heading",
                         background=BG3, foreground=MUTED,
                         font=("Courier", 10, "bold"), relief="flat",
                         borderwidth=0)
        style.map("Crypto.Treeview", background=[("selected", BG3)],
                  foreground=[("selected", ACCENT)])

        frame = tk.Frame(parent, bg=BG, bd=1, relief="flat",
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(frame, columns=cols, show="headings",
                                   style="Crypto.Treeview", selectmode="browse")

        widths = {"rank": 45, "name": 160, "symbol": 80,
                  "price": 130, "change_24h": 110, "market_cap": 140, "volume": 130}
        for col in cols:
            self._tree.heading(col, text=col_labels[col])
            self._tree.column(col, width=widths[col], anchor="e" if col not in ("name",) else "w")

        # Tags for coloring
        self._tree.tag_configure("positive", foreground=GREEN)
        self._tree.tag_configure("negative", foreground=RED)
        self._tree.tag_configure("neutral",  foreground=MUTED)
        self._tree.tag_configure("even",     background=CARD_BG)
        self._tree.tag_configure("odd",      background=BG2)

        sb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BG3, pady=4)
        bar.pack(fill="x", side="bottom")
        self._status = tk.Label(bar, text="Ready", font=("Courier", 10),
                                 bg=BG3, fg=MUTED, anchor="w", padx=12)
        self._status.pack(side="left")
        tk.Label(bar, text="Powered by CoinGecko API  |  No API key required",
                 font=("Courier", 10), bg=BG3, fg=MUTED, padx=12).pack(side="right")

    # ── Data Fetching ─────────────────────────────────────────────────────────

    def _fetch_data(self):
        self._set_status("Fetching live prices...", ACCENT)
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        try:
            data = api.fetch_prices(api.DEFAULT_COINS)
            self._data = data or []
            self.root.after(0, lambda: self._populate_table(self._data))
            self.root.after(0, lambda: self._update_portfolio_display())
            triggered = alerts.check_alerts(self._data)
            for msg in triggered:
                self.root.after(0, lambda m=msg: messagebox.showwarning("Price Alert!", m))
        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Error: {e}", RED))

    def _populate_table(self, data):
        for row in self._tree.get_children():
            self._tree.delete(row)
        for i, coin in enumerate(data):
            ch = coin.get("price_change_percentage_24h") or 0
            ch_str = f"▲ +{ch:.2f}%" if ch >= 0 else f"▼ {ch:.2f}%"
            tag = "positive" if ch >= 0 else "negative"
            row_tag = "even" if i % 2 == 0 else "odd"
            price = coin.get("current_price", 0)
            price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
            mc = coin.get("market_cap", 0)
            mc_str = f"${mc/1e9:.2f}B" if mc >= 1e9 else (f"${mc/1e6:.2f}M" if mc >= 1e6 else f"${mc:,.0f}")
            vol = coin.get("total_volume", 0)
            vol_str = f"${vol/1e9:.2f}B" if vol >= 1e9 else (f"${vol/1e6:.2f}M" if vol >= 1e6 else f"${vol:,.0f}")
            self._tree.insert("", "end", values=(
                coin.get("market_cap_rank", i+1),
                coin.get("name", ""),
                coin.get("symbol", "").upper(),
                price_str,
                ch_str,
                mc_str,
                vol_str,
            ), tags=(tag, row_tag))
        ts = datetime.now().strftime("%H:%M:%S")
        self._last_update_lbl.config(text=f"Updated: {ts}")
        self._set_status(f"Loaded {len(data)} coins  |  Last update: {ts}", GREEN)

    def _save_data(self):
        if not self._data:
            messagebox.showinfo("No Data", "No data fetched yet. Please refresh first.")
            return
        count, ts = storage.save_prices(self._data)
        messagebox.showinfo("Saved!", f"Saved {count} records at {ts}\n\nFiles:\n  data/price_history.json\n  data/price_history.csv")
        self._set_status(f"Saved {count} records", GREEN)

    # ── Search ────────────────────────────────────────────────────────────────

    def _do_search(self):
        q = self._search_var.get().strip()
        if not q:
            return
        self._set_status(f"Searching for '{q}'...", ACCENT)
        threading.Thread(target=self._search_worker, args=(q,), daemon=True).start()

    def _search_worker(self, q):
        try:
            coin_id = api.resolve_coin_id(q)
            if coin_id:
                coin = api.fetch_single_coin(coin_id)
                if coin:
                    self.root.after(0, lambda: self._show_coin_detail(coin))
                    return
            results = api.search_coin(q)
            if results:
                self.root.after(0, lambda: self._show_search_results(results))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Not Found", f"No coin found for '{q}'"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _show_coin_detail(self, coin):
        ch = coin.get("price_change_percentage_24h") or 0
        price = coin.get("current_price", 0)
        msg = (
            f"Name:       {coin.get('name','')} ({coin.get('symbol','').upper()})\n"
            f"Price:      ${price:,.4f}\n"
            f"24h Change: {'▲ +' if ch>=0 else '▼ '}{ch:.2f}%\n"
            f"Market Cap: ${coin.get('market_cap',0):,.0f}\n"
            f"24h Volume: ${coin.get('total_volume',0):,.0f}\n"
            f"24h High:   ${coin.get('high_24h',0):,.4f}\n"
            f"24h Low:    ${coin.get('low_24h',0):,.4f}\n"
            f"Rank:       #{coin.get('market_cap_rank','?')}"
        )
        messagebox.showinfo(f"{coin.get('name','')} Details", msg)
        self._set_status(f"Showing {coin.get('name','')} details", TEXT)

    def _show_search_results(self, results):
        names = [f"{r['name']} ({r.get('symbol','?').upper()})" for r in results[:5]]
        choice = simpledialog.askinteger("Search Results",
            "Multiple coins found:\n" + "\n".join(f"{i+1}. {n}" for i,n in enumerate(names)) +
            "\n\nEnter number to view details:", minvalue=1, maxvalue=len(names))
        if choice:
            coin_id = results[choice-1]["id"]
            threading.Thread(target=lambda: self.root.after(0,
                lambda: self._show_coin_detail(api.fetch_single_coin(coin_id) or {})),
                daemon=True).start()

    # ── Alerts ────────────────────────────────────────────────────────────────

    def _add_alert_dialog(self):
        coin = simpledialog.askstring("Add Alert", "Enter coin name or symbol:")
        if not coin:
            return
        cond = simpledialog.askstring("Condition", "Alert when price is 'above' or 'below':")
        if not cond or cond.lower() not in ("above", "below"):
            messagebox.showerror("Invalid", "Please enter 'above' or 'below'")
            return
        price = simpledialog.askfloat("Threshold", "Enter price threshold (USD):")
        if price is None:
            return
        coin_id = api.resolve_coin_id(coin)
        if not coin_id:
            messagebox.showerror("Not Found", f"Could not find coin: {coin}")
            return
        coin_data = api.fetch_single_coin(coin_id)
        if not coin_data:
            messagebox.showerror("Error", "Could not fetch coin data.")
            return
        alerts.add_alert(coin_id, coin_data["name"], cond.lower(), price)
        messagebox.showinfo("Alert Set", f"Alert: {coin_data['name']} {cond} ${price:,.2f}")
        self._refresh_alerts_display()

    def _refresh_alerts_display(self):
        al = alerts.list_alerts()
        self._alerts_list.config(state="normal")
        self._alerts_list.delete("1.0", "end")
        if not al:
            self._alerts_list.insert("end", "No alerts set.\n")
        for a in al:
            status = "✓" if not a["triggered"] else "✗"
            cond = ">" if a["condition"] == "above" else "<"
            self._alerts_list.insert("end",
                f"{status} {a['coin_name'][:10]:<10} {cond} ${a['threshold']:,.0f}\n")
        self._alerts_list.config(state="disabled")

    # ── Portfolio ─────────────────────────────────────────────────────────────

    def _add_holding_dialog(self):
        coin = simpledialog.askstring("Add Holding", "Coin name or symbol:")
        if not coin:
            return
        amount = simpledialog.askfloat("Amount", "How many coins do you hold?")
        if amount is None:
            return
        buy_price = simpledialog.askfloat("Buy Price", "Your average buy price (USD):")
        if buy_price is None:
            return
        coin_id = api.resolve_coin_id(coin)
        if not coin_id:
            messagebox.showerror("Not Found", f"Could not find: {coin}")
            return
        coin_data = api.fetch_single_coin(coin_id)
        if not coin_data:
            messagebox.showerror("Error", "Could not fetch coin.")
            return
        portfolio.add_holding(coin_id, coin_data["name"], coin_data.get("symbol","?"), amount, buy_price)
        messagebox.showinfo("Added!", f"Added {amount} {coin_data['symbol'].upper()} @ ${buy_price:,.2f}")
        self._update_portfolio_display()

    def _update_portfolio_display(self):
        holdings = portfolio.get_portfolio_value(self._data)
        self._portfolio_text.config(state="normal")
        self._portfolio_text.delete("1.0", "end")
        if not holdings:
            self._portfolio_text.insert("end", "No holdings yet.\n\nAdd coins to\ntrack your portfolio.")
        else:
            total = sum(h["current_value"] for h in holdings)
            total_pnl = sum(h["pnl"] for h in holdings)
            pnl_sign = "+" if total_pnl >= 0 else ""
            self._portfolio_text.insert("end", f"Total: ${total:,.2f}\n")
            self._portfolio_text.insert("end", f"P&L:   {pnl_sign}${total_pnl:,.2f}\n\n")
            for h in holdings:
                pnl_s = f"+{h['pnl_pct']:.1f}%" if h["pnl_pct"] >= 0 else f"{h['pnl_pct']:.1f}%"
                self._portfolio_text.insert("end",
                    f"{h['symbol']:<8} ${h['current_value']:,.0f} ({pnl_s})\n")
        self._portfolio_text.config(state="disabled")

    # ── Auto Refresh ──────────────────────────────────────────────────────────

    def _toggle_auto_refresh(self):
        if self._auto_refresh.get():
            self._stop_refresh.clear()
            self._refresh_thread = threading.Thread(target=self._auto_refresh_worker, daemon=True)
            self._refresh_thread.start()
            self._set_status(f"Auto-refresh every {self._refresh_interval}s", GREEN)
        else:
            self._stop_refresh.set()
            self._set_status("Auto-refresh stopped", MUTED)

    def _auto_refresh_worker(self):
        while not self._stop_refresh.is_set():
            self._stop_refresh.wait(self._refresh_interval)
            if not self._stop_refresh.is_set():
                self.root.after(0, self._fetch_data)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _set_status(self, msg, color=None):
        self._status.config(text=f"  {msg}", fg=color or MUTED)

    def _update_clock(self):
        now = datetime.now().strftime("%a %b %d  %H:%M:%S")
        self._time_label.config(text=now)
        self.root.after(1000, self._update_clock)


def main():
    root = tk.Tk()
    app = CryptoTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
