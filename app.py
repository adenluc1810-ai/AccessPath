import streamlit as st
import urllib.parse

# Streamlit Page Setup
st.set_page_config(page_title="AccessPath - Google Maps", layout="wide")

st.title("♿ AccessPath")
st.write("Google Maps பாணியில் உங்கள் நேரடி வழியைக் கண்டறியவும்.")

# Sidebar Controls
st.sidebar.header("📍 Route Search")
start_place = st.sidebar.text_input("Start Location (ஆரம்ப இடம்)", value="Chennai Central, Chennai")
dest_place = st.sidebar.text_input("Destination (செல்ல வேண்டிய இடம்)", value="Ripon Building, Chennai")

# Travel Mode Selection
travel_mode = st.sidebar.selectbox("Travel Mode", ["walking", "bicycling", "driving", "transit"])

# Encode URLs for Embed
start_encoded = urllib.parse.quote(start_place)
dest_encoded = urllib.parse.quote(dest_place)

# Google Maps Directions Embed URL
embed_url = f"https://www.google.com/maps/embed/v1/directions?key=YOUR_GOOGLE_MAPS_API_KEY&origin={start_encoded}&destination={dest_encoded}&mode={travel_mode}"

# Direct Mobile Google Maps Link
gmaps_native_url = f"https://www.google.com/maps/dir/?api=1&origin={start_encoded}&destination={dest_encoded}&travelmode={travel_mode}"

st.sidebar.markdown(f"📲 **[Google Maps செயலியில் வழியைத் திறக்க]({gmaps_native_url})**")

# Display Embedded Interactive Map
st.subheader(f"🗺️ Route: {start_place} ➔ {dest_place}")

# Fallback UI using Google Maps iframe wrapper
iframe_code = f"""
<iframe
  width="100%"
  height="580"
  style="border:0; border-radius:12px;"
  loading="lazy"
  allowfullscreen
  referrerpolicy="no-referrer-when-downgrade"
  src="https://maps.google.com/maps?q={start_encoded}%20to%20{dest_encoded}&output=embed">
</iframe>
"""

st.components.v1.html(iframe_code, height=600)