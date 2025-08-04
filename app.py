import streamlit as st
import numpy as np
import joblib
import requests

#Header
st.set_page_config(page_title="Smart Sprinkler System")
st.markdown("<h1 style='text-align:center'>Welcome to Smart Sprinkler System</h1>",unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center'>Predict sprinkler activation based on sensor readings and weather conditions</h5>",unsafe_allow_html=True)
st.write("---")

#Load model
model=joblib.load("Farm_Irrigation_System.pkl")

#Read sensor values 
st.subheader("Enter Sensor Values (scaled 0 - 1)")
cols=st.columns(2)
sensor_values=[]
for i in range(20):
    with cols[i%2]:
        val=st.slider(f"Sensor {i}",0.0,1.0,0.5,0.01)
        sensor_values.append(val)

st.write("---")

#Input weather data
st.markdown("<br><h2>Weather Data</h2>",unsafe_allow_html=True)
with st.expander("Weather-based irrigation thresholds used in this system"):
    st.markdown("""
    - **Temperature:**  
        - < 25°C → normal or reduced irrigation  
        - 25–35°C → normal irrigation  
        - > 35°C → irrigate more
    - **Humidity:**  
        - < 50% → irrigate more  
        - 50–80% → normal irrigation  
        - 75–85% → irrigate less  
        - > 85% (and temperature < 25°C) → turn off irrigation
    - **Rainfall (last 1 hour):**  
        - 0 mm → normal irrigation  
        - 0–2 mm → irrigate less  
        - > 2 mm → turn off irrigation
    """)

API_KEY="ff867b9d8d3eaca8e1c6af3b7334744e"

if "weather_data" not in st.session_state:
    st.session_state.weather_data=None

col=st.columns(2,gap="medium",vertical_alignment="bottom")
with col[0]:
    CITY=st.text_input("Enter your city:")
with col[1]:
    st.write("Enter city name and click Done to fetch live weather.")

if st.button("Done"):
    try:
        url=f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
        response=requests.get(url,timeout=5)
        weather=response.json()
        if weather.get("cod")==200:
            st.session_state.weather_data={
                "temperature":weather['main']['temp'],
                "humidity":weather['main']['humidity'],
                "rain":weather.get('rain',{}).get('1h',0)
            }
            st.success(f"Weather data loaded for {CITY}")
        else:
            raise Exception("API returned error")
    except Exception as e:
        st.error("Weather API failed. Please enter manually.")
        st.session_state.weather_data={
            "temperature":st.slider("Temperature (°C)",-10.0,50.0,25.0),
            "humidity":st.slider("Humidity (%)",0.0,100.0,50.0),
            "rain":st.slider("Rain (mm in last hour)",0.0,50.0,0.0)
        }

#Display weather data
if st.session_state.weather_data is not None:
    st.markdown("### Weather Details")
    st.write(f"**Temperature:** {st.session_state.weather_data['temperature']} °C")
    st.write(f"**Humidity:** {st.session_state.weather_data['humidity']} %")
    st.write(f"**Rain (last 1h):** {st.session_state.weather_data['rain']} mm")
    st.write("---")

    #Prediction of sprinkler values
    if st.button("Predict Sprinklers"):
        temperature=st.session_state.weather_data["temperature"]
        humidity=st.session_state.weather_data["humidity"]
        rain=st.session_state.weather_data["rain"]

        input_array=np.array(sensor_values).reshape(1,-1)
        prediction=model.predict(input_array)[0]

        status_message="Normal irrigation"
        icon="✅"

        #Checking condition of weather and modifying the prediction based on it
        if rain>2:
            prediction[:]=0
            status_message="High rain detected : Sprinklers turned OFF due to high moisture"
            icon="💧"
        elif humidity>85 and temperature<25:
            prediction[:]=0
            status_message="High moisture and low temperature detected : Sprinklers turned OFF"
            icon="💧"
        elif temperature>35 or humidity<50:
            status_message="Hot/dry conditions detected : More irrigation required"
            icon="🔥"
        elif (0<rain<=2) or (75<=humidity<=85):
            status_message="Light rain detected : Irrigate less (some natural moisture present)"
            icon="🌦️"

        #Displaying resuls
        st.markdown(f"### {icon} **{status_message}**")
        col_result=st.columns(4)
        for i,status in enumerate(prediction):
            col_result[i%4].metric(f"Sprinkler {i}","ON" if status else "OFF")