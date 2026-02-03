import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

# --- ページ設定 ---
st.set_page_config(page_title="九州気温 3D Map (Light)", layout="wide")
st.title("九州主要都市の現在の気温 3Dカラムマップ (明るい配色版)")

# 九州7県のデータ
kyushu_capitals = {
    'Fukuoka':    {'lat': 33.5904, 'lon': 130.4017},
    'Saga':       {'lat': 33.2494, 'lon': 130.2974},
    'Nagasaki':   {'lat': 32.7450, 'lon': 129.8739},
    'Kumamoto':   {'lat': 32.7900, 'lon': 130.7420},
    'Oita':       {'lat': 33.2381, 'lon': 131.6119},
    'Miyazaki':   {'lat': 31.9110, 'lon': 131.4240},
    'Kagoshima':  {'lat': 31.5600, 'lon': 130.5580}
}

# --- データ取得関数 ---
@st.cache_data(ttl=600)
def fetch_weather_data():
    weather_info = []
    BASE_URL = 'https://api.open-meteo.com/v1/forecast'
    
    for city, coords in kyushu_capitals.items():
        params = {
            'latitude':  coords['lat'],
            'longitude': coords['lon'],
            'current': 'temperature_2m',
            'timezone': 'Asia/Tokyo'  # 【追加】日本時間を指定して取得
        }
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 【追加】時刻データの取得と整形 (ISO形式の "T" をスペースに置換)
            time_str = data['current']['time'].replace('T', ' ')
            
            weather_info.append({
                'City': city,
                'lat': coords['lat'],
                'lon': coords['lon'],
                'Temperature': data['current']['temperature_2m'],
                'Time': time_str  # 【追加】計測時刻
            })
        except Exception as e:
            st.error(f"Error fetching {city}: {e}")
            
    return pd.DataFrame(weather_info)

# データの取得
with st.spinner('最新の気温データを取得中...'):
    df = fetch_weather_data()

# 気温を高さ（メートル）に変換
df['elevation'] = df['Temperature'] * 3000

# --- メインレイアウト ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("取得したデータ")
    # 【変更】Time列も含めて表示
    # 最新のStreamlit向けに use_container_width ではなく width="stretch" を使用推奨
    st.dataframe(df[['City', 'Temperature', 'Time']], width="stretch")
    
    if st.button('データを更新'):
        st.cache_data.clear()
        st.rerun()

    # 全体の最終更新時刻を目立たせる
    if not df.empty:
        latest_time = df['Time'].iloc[0]
        st.info(f"🕒 データ計測時刻: {latest_time}")

with col2:
    st.subheader("3D カラムマップ")

    # Pydeck の設定
    view_state = pdk.ViewState(
        latitude=32.7,
        longitude=131.0,
        zoom=6.2,
        pitch=45,
        bearing=0
    )

    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position='[lon, lat]',
        get_elevation='elevation',
        radius=12000,
        # 【変更】明るい背景に映えるよう、鮮やかなオレンジに変更
        get_fill_color='[255, 140, 0, 200]', 
        pickable=True,
        auto_highlight=True,
    )

    # 描画
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        # 【変更】地図スタイルを「Light（明るい）」に設定
        map_style='mapbox://styles/mapbox/light-v9',
        tooltip={
            # 【変更】ツールチップにも時刻を表示し、文字色を黒（見やすく）に変更
            "html": "<div style='color:black;'><b>{City}</b><br>気温: {Temperature}°C<br>時刻: {Time}</div>",
            "style": {"backgroundColor": "white", "color": "black"}
        }
    ))
