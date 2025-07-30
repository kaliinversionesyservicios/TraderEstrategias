# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 01:05:59 2025

@author: carlos
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import *
import threading
import time
import pandas as pd
import os


class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}

    def historicalData(self, reqId: int, bar: BarData):
        ticker = self.reqId_to_ticker.get(reqId, f"ID{reqId}")
        if ticker not in self.data:
            self.data[ticker] = []
        self.data[ticker].append((bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume))

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print(f"✔ Datos recibidos para {self.reqId_to_ticker[reqId]}")
        self.pending_requests -= 1
        if self.pending_requests == 0:
            self.disconnect()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"❌ Error: ReqID={reqId}, Code={errorCode}, Msg={errorString}")

    def start_requests(self, tickers):
        self.reqId_to_ticker = {}
        self.pending_requests = len(tickers)

        for i, ticker in enumerate(tickers):
            contract = Contract()
            contract.symbol = ticker
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            self.reqId_to_ticker[i] = ticker

            self.reqHistoricalData(
                reqId=i,
                contract=contract,
                endDateTime="",
                durationStr="1 D",
                barSizeSetting="1 hour",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            time.sleep(1.5)  # importante para evitar bloqueo de IB por exceso de llamadas

def run_loop(app):
    app.run()

# === INICIO ===
#tickers = ["SPY", "META", "AAPL"]
tickers = [
    'SPY',
    'META',
    'AAPL',
    'AMZN',
    'NFLX',
    'MRNA',
    'TSLA',
    'TNA',
    'GLD',
    'SLV',
    'USO',
    'BAC',
    'CVX',
    'XOM',
    'QQQ',
    'MSFT',
    'NVDA',
    'WMT',
    'BA',
    'DIS',
    'CAT',
    'IBM',
    'WFC',
    'PLTR',
    'AMD',
    'AVGO',
    'HOOD',
    'CRWV',
    'MSTR',
    'UNH',
    'GOOG',
    'APP',
    'UBER'
]

app = IBApp()
app.connect("127.0.0.1", 4002, clientId=1)

# Hilo para ejecutar el loop
thread = threading.Thread(target=run_loop, args=(app,))
thread.start()

# Lanza las solicitudes
time.sleep(1)
app.start_requests(tickers)

thread.join()

df= pd.DataFrame()
for ticker in app.data:
    df_ticker = pd.DataFrame(app.data[ticker], columns=["Datetime", "Open", "High", "Low", "Close", "Volume"])
    if df_ticker is not None:
        print("paso ticker:", ticker)
        df_ticker["companyName"] = ticker
        df_ticker['Datetime'] = df_ticker['Datetime'].str.replace(' US/Eastern', '', regex=False)
        print("cantidad:", df_ticker.shape[0])
        if (df_ticker.shape[0]<=0):
            df = df_ticker.copy()
        else:
            df = pd.concat([df, df_ticker], ignore_index=False)
   # print(f"\n{ticker}:\n", df.tail())

df["Datetime"] = pd.to_datetime(df["Datetime"])
fecMin = df["Datetime"].min()


#Obtener datos anteriores
path='data/dataxh.txt'
if os.path.exists(path):
    # Cargar el archivo
    df_old = pd.read_csv(path, sep='\t')
    df_old["Datetime"] = pd.to_datetime(df_old["Datetime"])
    print("Archivo cargado correctamente.")
else:
    # Crear un DataFrame vacío
    df_old = pd.DataFrame()
    print("Archivo no existe. Se creó un DataFrame vacío.")
   
#Crear nuevo dataframe
if (df_old.shape[0]>0):
    df_new = df_old.query("Datetime<@fecMin").copy()
    df_new = pd.concat([df_new, df],ignore_index=False)
    
else:
    df_new = df.copy()


##############
folder = os.path.dirname(path)

# Crear carpeta si no existe
if not os.path.exists(folder):
    os.makedirs(folder)

# Eliminar el archivo si ya existe
if os.path.exists(path):
    os.remove(path)
else:
    print("File does not exist. File needs to be created.")

# Exportar DataFrame a archivo de texto
df_new.to_csv(path, header=True, index=None, sep='\t', mode='w')