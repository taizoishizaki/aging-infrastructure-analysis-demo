import ee
import folium
import os
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv('GEE_PROJECT_ID')

# 1. 初期化
try:
    # PROJECT_IDが正しく読み込めているか確認
    if not PROJECT_ID:
        raise ValueError("環境変数 'GEE_PROJECT_ID' が設定されていません。")
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# 2. 千代田区の範囲を取得 (座標で直接指定するのが最も確実です)
# 内神田周辺を中心とした矩形、または行政区画
chiyoda_bounds = ee.Geometry.Rectangle([139.73, 35.66, 139.78, 35.71])

# 3. Sentinel-1 SARデータの期間別平均を作成
def get_sar_mean(start_date, end_date, region):
    return (ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(region)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            .select('VV')
            .mean())

sar_2021 = get_sar_mean('2021-01-01', '2021-12-31', chiyoda_bounds)
sar_2024 = get_sar_mean('2024-01-01', '2024-12-31', chiyoda_bounds)

# 4. 差分計算（2024年 - 2021年）
diff_map = sar_2024.subtract(sar_2021).clip(chiyoda_bounds)

# 5. Foliumで可視化するためのURL生成
# Google Earth Engineの画像をタイル状に変換してブラウザで呼べるようにします
map_id_dict = ee.Image(diff_map).getMapId({
    'min': -5, 
    'max': 5, 
    'palette': ['red', 'white', 'blue']
})

# 6. Foliumマップの作成
# 千代田区を中心に設定
m = folium.Map(location=[35.69, 139.76], zoom_start=14)

# GEEのタイルレイヤーを追加
folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    name='Chiyoda Risk Map (Diff)',
    overlay=True,
    control=True,
    opacity=0.7
).add_to(m)

# 比較用に通常の地図も追加
folium.LayerControl().add_to(m)

# 7. 保存と表示
output_file = 'risk_map_chiyoda.html'
m.save(output_file)
print(f"解析が完了しました。'{output_file}' をブラウザで開いてください。")