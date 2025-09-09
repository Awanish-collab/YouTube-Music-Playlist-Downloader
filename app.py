import streamlit as st
import subprocess
import json
from datetime import datetime

def get_playlist_info(url):
    command = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        url
    ]

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    videos = []
    for line in process.stdout:
        try:
            info = json.loads(line.strip())
            videos.append(info)
        except json.JSONDecodeError:
            continue

    process.stdout.close()
    process.wait()
    return videos

def download_playlist(url, quality, current_song_placeholder):
    command = [
        "yt-dlp",
        "-f", "bestaudio",
        "-x",
        "--audio-format", "mp3",
        f"--audio-quality", quality,
        "--add-metadata",
        "--embed-thumbnail",
        url
    ]

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    current_song = 0
    for line in process.stdout:
        yield line
        # Increment only when a new download starts
        if line.startswith("[download] Destination:"):
            current_song += 1
            current_song_placeholder.text(f"🎵 Downloaded song {current_song}")

    process.stdout.close()
    process.wait()


def main():
    st.title("🎧 YouTube Music Playlist Downloader")
    st.markdown("Paste your YouTube Music Playlist URL below:")

    url = st.text_input("Playlist URL")
    quality = st.selectbox("Select Audio Quality", options=["128K", "192K", "320K"], index=1)

    if st.button("Analyze Playlist"):
        if not url:
            st.error("⚠️ Please enter a valid playlist URL.")
            return

        with st.spinner("🔍 Fetching playlist info..."):
            videos = get_playlist_info(url)

        total_songs = len(videos)
        st.success(f"✅ Found **{total_songs} songs** in the playlist.")
        st.session_state["videos"] = videos
        st.session_state["total_songs"] = total_songs

    if st.button("Start Download"):
        if "total_songs" not in st.session_state:
            st.error("⚠️ Please analyze playlist first.")
            return

        total_songs = st.session_state["total_songs"]

        st.info(f"📥 Starting download at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        progress_bar = st.progress(0)
        status_text = st.empty()
        song_counter_text = st.empty()

        log_lines = []
        total_lines = total_songs * 10  # approximate

        for i, output in enumerate(download_playlist(url, quality, song_counter_text)):
            log_lines.append(output)
            status_text.text(output.strip())
            progress = min(i / total_lines, 1.0)
            progress_bar.progress(progress)

        st.success("✅ All songs downloaded in current directory!")
        st.info("Files are available in the same directory where this app is running.")

if __name__ == "__main__":
    main()
