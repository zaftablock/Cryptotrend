import streamlit as st
from binance.client import Client
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Ganti dengan API key dan secret Anda
api_key = 'your_api_key'
api_secret = 'your_api_secret'

# Inisialisasi client Binance
client = Client(api_key, api_secret)

# Judul aplikasi
st.title("Crypto Price Analysis and Signal")
st.sidebar.header("Settings")

# Sidebar untuk memilih simbol
symbol = st.sidebar.text_input("Symbol (e.g., BTCUSDT):", value="BTCUSDT")
interval = Client.KLINE_INTERVAL_1MINUTE
lookback = '1 day ago GMT+7'

# Tombol untuk memperbarui data
if st.sidebar.button("Update Data"):
    with st.spinner("Fetching and analyzing data..."):
        try:
            # Mengambil data candlestick
            candles = client.get_historical_klines(symbol, interval, lookback)
            df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close', 'volume', 
                                                'close_time', 'quote_asset_volume', 'number_of_trades', 
                                                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

            # Memproses data
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df['close'] = df['close'].astype(float)
            df.set_index('time', inplace=True)
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Jakarta')
            df['SMA_6'] = df['close'].rolling(window=6).mean()
            df['SMA_21'] = df['close'].rolling(window=21).mean()
            df['signal'] = 0
            df.loc[df['SMA_6'] > df['SMA_21'], 'signal'] = 1
            df.loc[df['SMA_6'] < df['SMA_21'], 'signal'] = -1

            # Hitung Take Profit, Stop Loss, dan prediksi harga
            current_price = df['close'].iloc[-1]
            TP = current_price * 1.02
            SL = current_price * 0.99
            entry_price = current_price if df['signal'].iloc[-1] != 0 else np.nan
            X = np.array(range(len(df))).reshape(-1, 1)
            y = df['close'].values
            model = LinearRegression()
            model.fit(X, y)
            future_time = len(df) + 5
            predicted_price = model.predict(np.array([[future_time]]))[0]

            # Menampilkan data dan hasil analisis
            st.write("### Current Data and Analysis")
            st.write(df.tail(10))  # Menampilkan 10 data terakhir
            recommendation = pd.DataFrame({
                'Waktu (GMT+7)': [df.index[-1].strftime('%Y-%m-%d %H:%M:%S')],
                'Price': [current_price],
                'Signal': ['Long' if df['signal'].iloc[-1] == 1 else 'Short' if df['signal'].iloc[-1] == -1 else 'No Signal'],
                'Entry': [entry_price],
                'TP': [TP],
                'SL': [SL],
                'NEXT 5M': [predicted_price]
            })
            st.write("### Recommendation")
            st.table(recommendation)
        except Exception as e:
            st.error(f"An error occurred: {e}")
