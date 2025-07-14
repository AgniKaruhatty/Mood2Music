import streamlit as st
st.set_page_config(layout="wide", page_title="Mood-Based Song Recommender")

from emotion_models import (
    load_cnn_model,
    predict_emotion_from_image,
    load_text_model,
    predict_emotion_from_text
)
from song_recommender import load_spotify_data, get_songs_for_emotion

# Load models and data
cnn_model = load_cnn_model()
text_model, label_map = load_text_model()
spotify_df = load_spotify_data()

# Title and intro
st.subheader("MOOD2MUSIC: PLAYLIST RETRIEVAL BASED ON EMOTION 🎶")

# Mood input selection
st.markdown("#### How are you feeling right now? 👋 ")
st.markdown("###### Select from one of the option below. ")

input_mode = st.radio(
    "Select an input method:",
    ["📝 Text Input", "🎭 Preset Emotion", "📸 Image Input"],
    horizontal=True
)

input_mode_clean = input_mode.split(" ", 1)[1].strip()
selected_mood = None
detected_msg = ""

# user sends a text about their feelings for detection 
if input_mode_clean == "Text Input":
    st.subheader("📝 Describe how you're feeling:")
    user_text = st.text_area("Enter your mood in words:")
    if user_text:
        selected_mood, confidence = predict_emotion_from_text(text_model, label_map, user_text)
        detected_msg = f"Detected Mood: **{selected_mood.capitalize()}** ({confidence*100:.1f}% confidence)"

# choose emotion from preset
elif input_mode_clean == "Preset Emotion":
    st.subheader("🎭 Choose a mood that matches your vibe:")
    mood_choice = st.selectbox("Select a mood:", ["", "Happy", "Sad", "Angry", "Fear", "Surprise", "Neutral"])
    if mood_choice:
        selected_mood = mood_choice.lower()
        detected_msg = f"Selected Mood: **{selected_mood.capitalize()}**"

# upload or enter an image for detection 
elif input_mode_clean == "Image Input":
    st.subheader("📸 Show us your expression:")
    
    method = st.selectbox("Choose how to upload your image:", ["Take a photo with webcam", "Upload an image"])
    image_bytes = None

    if method == "Take a photo with webcam":
        cam_photo = st.camera_input("Capture your face")
        if cam_photo:
            image_bytes = cam_photo.getvalue()
    elif method == "Upload an image":
        uploaded_file = st.file_uploader("Upload a face image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            image_bytes = uploaded_file.read()

    if image_bytes:
        selected_mood = predict_emotion_from_image(cnn_model, image_bytes)
        detected_msg = f"Detected Mood: **{selected_mood.capitalize()}**"

# Recommends 10 songs -> playlist + Refresh = new
if selected_mood:
    st.success(detected_msg)

    if "refresh_count" not in st.session_state:
        st.session_state.refresh_count = 0
    # refresh for a new set of songs
    if st.button("Give me a new playlist"):
        st.session_state.refresh_count += 1

    songs = get_songs_for_emotion(selected_mood, spotify_df, seed=st.session_state.refresh_count)

    if not songs.empty:
        st.subheader("Your Song Recommendations 🎧")

        for i, row in songs.iterrows():
            with st.container():
                st.markdown(f"### {i+1}. {row['track_name']} by *{row['artists']}*")
                st.markdown(f"**Album:** `{row['album_name']}`")

                # Genre 
                genre_tag = f"<span style='background-color:#1db954; color:white; padding:3px 8px; border-radius:12px; font-size:0.85em;'>{row['track_genre']}</span>"
                st.markdown(f"**Genre:** {genre_tag}", unsafe_allow_html=True)

                # Duration 
                colA, colB = st.columns([2, 3])
                colA.markdown(f"**⏱ Duration:** `{row['duration_min']}`")

                # Popularity bar
                popularity_bar = f"""
                <div style='background-color:#333;border-radius:10px;height:20px;width:100%;'>
                    <div style='background-color:#1db954;width:{row['popularity']}%;height:100%;border-radius:10px;text-align:center;color:white;font-size:12px;line-height:20px;'>
                        {int(row['popularity'])}/100
                    </div>
                </div>
                """
                colB.markdown("**Popularity**")
                colB.markdown(popularity_bar, unsafe_allow_html=True)

                # Play button
                st.markdown(
                    f"""
                    <a href="{row['spotify_search']}" target="_blank" style="text-decoration:none;">
                        <button style="background-color:#1db954;border:none;color:white;padding:8px 20px;border-radius:25px;cursor:pointer;font-weight:bold;font-size:14px;">
                            ▶️ Play on Spotify
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown("---")
    else:
        st.warning("No matching songs found for this mood.")