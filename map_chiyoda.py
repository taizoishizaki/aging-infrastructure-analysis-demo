import ee
import geemap.foliumap as geemap  # ここを書き換える（重要！）
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv('GEE_PROJECT_ID')

# 初期化
try:
    # PROJECT_IDが正しく読み込めているか確認
    if not PROJECT_ID:
        raise ValueError("環境変数 'GEE_PROJECT_ID' が設定されていません。")
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# 千代田区周辺の座標
chiyoda = ee.Geometry.Point([139.75, 35.68])

# 衛星データ取得
image = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
         .filterBounds(chiyoda)
         .filterDate('2023-01-01', '2023-12-31')
         .sort('CLOUDY_PIXEL_PERCENTAGE')
         .first())

# 地図作成 (geemap.foliumap を使っているので、出力が安定します)
Map = geemap.Map()
Map.centerObject(chiyoda, 14)
Map.addLayer(image, {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}, 'Chiyoda Image')

# 保存と表示
output_file = "map_chiyoda.html"
Map.save(output_file) # foliumベースなので save() でOK

print(f"Success! Opening {output_file}...")
webbrowser.open('file://' + os.path.realpath(output_file))