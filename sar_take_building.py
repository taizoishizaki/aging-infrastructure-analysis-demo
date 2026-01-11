import ee
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

# 1. 初期化と認証（初回実行時や認証が切れている場合に必要）
load_dotenv()
PROJECT_ID = os.getenv('GEE_PROJECT_ID')
try:
    # PROJECT_IDが正しく読み込めているか確認
    if not PROJECT_ID:
        raise ValueError("環境変数 'GEE_PROJECT_ID' が設定されていません。")
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# 2. 竹ビルの座標を設定
target_poi = ee.Geometry.Point([139.7686, 35.6915]) 

# 3. Sentinel-1 SARデータの取得（過去3年分）
sar_collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(target_poi)
    .filterDate('2021-01-01', '2024-12-31')
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .select('VV'))

# 4. 特定地点の時系列データを抽出する関数
def extract_time_series(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(), 
        geometry=target_poi, 
        scale=10
    )
    # 辞書形式でプロパティを返す
    return ee.Feature(None, {
        'date': image.date().format('YYYY-MM-DD'), 
        'vv': stats.get('VV')
    })

# Googleのサーバー側でマップ処理を実行して結果を取得
time_series_info = sar_collection.map(extract_time_series).getInfo()

# --- 5. Pandas DataFrameへの変換（クレンジングを強化） ---
data = []
for f in time_series_info['features']:
    props = f['properties']
    if props.get('vv') is not None and props.get('date') is not None:
        data.append({'date': props['date'], 'value': props['vv']})

if not data:
    print("データが空です。座標や期間を確認してください。")
else:
    df = pd.DataFrame(data)

    # 【修正ポイント】不正な日付（2021-02-40等）を強制的にNaTに変換し、除去する
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # NaT（変換失敗データ）がある行を削除
    initial_count = len(df)
    df = df.dropna(subset=['date'])
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        print(f"警告: 不正な日付形式のデータを {dropped_count} 件除外しました。")

    # 同じ日のデータは平均化して時系列順にソート
    df = df.groupby('date').mean().reset_index().sort_values('date')

    # --- 6. グラフの作成（変更なし） ---
    if df.empty:
        print("表示できる有効なデータがありません。")
    else:
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['value'], marker='o', linestyle='-', color='#1f77b4', markersize=3, linewidth=1)
        plt.title('SAR Backscatter Analysis: Take Building (Uchikanda 2-11-6)', fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Backscatter Intensity (VV dB)', fontsize=12)
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()