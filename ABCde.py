import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---- Streamlit Page Setup ----
st.set_page_config(page_title="Algo vs Human - Illiquid Option Simulation", layout="wide")
st.title("💹 Illiquid Option Market Simulation (Algo vs Human)")
st.markdown("""
This app simulates an **illiquid option market** where an **algorithm** acts as both buyer and seller.
When a human enters a buy order, the algo pushes the price above fair value and sells at a profit.
> ⚠️ *Educational purpose only — real-world market manipulation is illegal.*
""")

# ---- User Inputs ----
col1, col2, col3 = st.columns(3)
with col1:
    fair_price = st.number_input("Fair Value of Option", value=40.0, min_value=1.0, step=1.0)
    initial_bid = st.number_input("Initial Bid (Algo Buyer)", value=20.0, min_value=0.0, step=1.0)
with col2:
    initial_ask = st.number_input("Initial Ask (Algo Seller)", value=100.0, min_value=1.0, step=1.0)
    human_limit_price = st.number_input("Human Buy Order Price", value=21.0, min_value=1.0, step=1.0)
with col3:
    push_step = st.number_input("Algo Push Step", value=2.0, min_value=0.5, step=0.5)
    target_multiplier = st.slider("Target Sell (× Fair Value)", 1.0, 2.0, 1.2)

# ---- Simulation ----
time = 0
orderbook_history = []
trade_history = []

best_bid = initial_bid
best_ask = initial_ask
human_order = {"type": "limit_buy", "price": human_limit_price, "size": 1, "filled": 0}

target_price = fair_price * target_multiplier
max_steps = 15
filled = False

def record_state(t, bid, ask, human):
    orderbook_history.append({
        "time": t,
        "best_bid": bid,
        "best_ask": ask,
        "mid_price": (bid + ask) / 2,
        "human_bid": human["price"] if human["filled"] < human["size"] else None
    })

record_state(time, best_bid, best_ask, human_order)

for step in range(1, max_steps + 1):
    time += 1
    mid = (best_bid + best_ask) / 2

    if human_order["price"] > best_bid and not filled:
        best_bid = human_order["price"] + push_step
        best_ask += push_step
        record_state(time, best_bid, best_ask, human_order)

        mid = (best_bid + best_ask) / 2
        if mid >= target_price:
            sell_price = target_price
            trade_history.append({
                "time": time,
                "buyer": "human",
                "seller": "algo",
                "price": sell_price,
                "size": 1
            })
            human_order["filled"] = 1
            filled = True
            best_bid = initial_bid
            best_ask = initial_ask
            record_state(time + 0.1, best_bid, best_ask, human_order)
            break
    else:
        record_state(time, best_bid, best_ask, human_order)

# ---- DataFrames ----
orderbook_df = pd.DataFrame(orderbook_history)
trades_df = pd.DataFrame(trade_history)

# ---- Human P&L ----
if not trades_df.empty:
    fill_price = trades_df.iloc[-1]["price"]
    revert_price = (initial_bid + initial_ask) / 2
    pnl = (revert_price - fill_price)
else:
    fill_price = None
    pnl = None

# ---- Display Results ----
st.subheader("📊 Order Book History")
st.dataframe(orderbook_df, use_container_width=True)

st.subheader("💱 Trade History")
if not trades_df.empty:
    st.dataframe(trades_df, use_container_width=True)
else:
    st.info("No trade occurred within simulation steps.")

# ---- Chart ----
st.subheader("📈 Price Movement Visualization")
fig, ax = plt.subplots()
ax.plot(orderbook_df["time"], orderbook_df["best_bid"], label="Best Bid", linestyle="--")
ax.plot(orderbook_df["time"], orderbook_df["best_ask"], label="Best Ask", linestyle="--")
ax.plot(orderbook_df["time"], orderbook_df["mid_price"], label="Mid Price", color="black", linewidth=2)
if fill_price:
    ax.axhline(fill_price, color="red", linestyle=":", label=f"Trade @ {fill_price:.2f}")
ax.axhline(fair_price, color="green", linestyle="-.", label="Fair Value")
ax.legend()
st.pyplot(fig)

# ---- Summary ----
st.subheader("📋 Summary")
st.write({
    "Fair Value": fair_price,
    "Target Sell Price": target_price,
    "Human Limit Buy Price": human_limit_price,
    "Trade Executed": bool(filled),
    "Fill Price": fill_price,
    "Human P&L After Revert": pnl
})
