import requests
import time
import json
import numpy as np
from datetime import datetime

# Token dan Chat ID Telegram
TOKEN = ""
CHAT_ID = ""

# Simpan harga 1 jam lalu
price_history = {}

# Ambil semua data koin dari Indodax
def get_all_coins():
    url = "https://indodax.com/api/tickers"
    response = requests.get(url).json()
    return response.get("tickers", {})

# Hitung RSI (Relative Strength Index)
def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None  # Data kurang dari periode RSI

    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0).sum() / period
    loss = -np.where(deltas < 0, deltas, 0).sum() / period

    if loss == 0:
        return 100  # RSI max (overbought)
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Hitung Simple Moving Average (SMA)
def calculate_sma(prices, period=14):
    if len(prices) < period:
        return None  # Data kurang dari periode SMA
    return sum(prices[-period:]) / period

# Analisis koin potensial naik
def find_potential_pumps():
    global price_history
    coins = get_all_coins()
    potential_pumps = {}

    for coin, data in coins.items():
        try:
            last_price = float(data["last"]) if data["last"] else None #harga terakhir
            high = float(data.get("high", 0))  # Harga tertinggi 24 jam
            low = float(data.get("low", 0))  # Harga terendah 24 jam
            volume = float(data.get("vol_idr", 0))  # Volume IDR

            if low == 0:
                continue  # Hindari pembagian dengan nol

            # Simpan harga 1 jam lalu (sebagai list)
            if coin not in price_history:
                price_history[coin] = [last_price]  # Jika belum ada, buat list baru
            else:
                price_history[coin].append(last_price)  # Tambahkan harga baru
                if len(price_history[coin]) > 14:  # Hapus data lama jika lebih dari 14
                    price_history[coin].pop(0)

            previous_price = price_history[coin][0]  # Harga pertama dalam list


            # Hitung kenaikan 1 jam
            change_1h = ((last_price - previous_price) / previous_price) * 100

            # Hitung kenaikan dalam 24 jam
            change_24h = ((last_price - low) / low) * 100

            # Hitung RSI (gunakan data dari 14 jam terakhir jika ada)
            if coin not in price_history:
                price_history[coin] = [last_price] * 14  # Isi awal data
            else:
                price_history[coin].append(last_price)
                if len(price_history[coin]) > 14:
                    price_history[coin].pop(0)

            rsi = calculate_rsi(price_history[coin])
            sma = calculate_sma(price_history[coin])

            # Kriteria pump:
            if (
                change_1h >= 3 and  # Naik ≥3% dalam 1 jam
                change_24h >= 5 and  # Naik ≥5% dalam 24 jam
                volume > 1_000_000_000 and  # Volume tinggi
                (rsi is None or rsi < 70) and  # RSI di bawah overbought
                (sma is None or last_price > sma)  # Harga di atas SMA
            ):
                potential_pumps[coin] = {
                    "price": last_price,
                    "change_1h": change_1h,
                    "change_24h": change_24h,
                    "volume": volume,
                    "rsi": rsi,
                    "sma": sma
                }

        except ValueError:
            print(f"Error parsing data untuk {coin}: {data['last']}")
            last_price = None


    return potential_pumps

# Kirim notifikasi per koin
def send_signal():
    potential_pumps = find_potential_pumps()

    if not potential_pumps:
        print("Tidak ada koin potensial naik saat ini.")
        return
    rsi_value = data.get('rsi')  # Ambil nilai RSI, default None jika tidak ada
    rsi_text = f"📊 RSI: {rsi_value:.2f} {'(Overbought)' if rsi_value and rsi_value >= 70 else ''}\n" if rsi_value is not None else "📊 RSI: Data tidak tersedia\n"

    for coin, data in potential_pumps.items():
        message = (
            f"🚀 **SINYAL PUMP TERDETEKSI** 🚀\n\n"
            f"💰 **{coin.upper()}**\n"
            f"🔹 Harga Sekarang: Rp {data['price']:,.0f}\n"
            f"📊 Volume: Rp {data['volume']:,.0f}\n"
            f"📈 Naik 1 Jam: {data['change_1h']:.2f}%\n"
            f"📈 Naik 24 Jam: {data['change_24h']:.2f}%\n"
            f"📈 {rsi_text}%\n"
            f"📊 SMA (14): {data['sma']:,.0f}\n"
            f"🕒 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"------------------\n"
        )

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

        time.sleep(2)  # Delay antar notifikasi agar tidak spam

# Jalankan bot setiap 1 detik di VPS
while True:
    send_signal()
    time.sleep(1)  # 1 detik
