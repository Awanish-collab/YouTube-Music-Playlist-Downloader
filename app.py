import streamlit as st
import subprocess
import json
import os
from datetime import datetime

def get_playlist_info(url):
    command = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        url
    ]

    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        videos = []
        error_output = []
        
        # Read stdout
        for line in process.stdout:
            try:
                info = json.loads(line.strip())
                videos.append(info)
            except json.JSONDecodeError:
                continue

        # Read stderr for errors
        for line in process.stderr:
            error_output.append(line.strip())

        process.stdout.close()
        process.stderr.close()
        return_code = process.wait()
        
        # If there are errors, show them
        if return_code != 0 or not videos:
            error_msg = "\n".join(error_output) if error_output else "Unknown error occurred"
            st.error(f"yt-dlp error: {error_msg}")
            
        return videos
        
    except Exception as e:
        st.error(f"Error running yt-dlp: {str(e)}")
        return []

def download_playlist(url, quality, current_song_placeholder):
    # Create downloads directory
    download_dir = "/tmp/downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    command = [
        "yt-dlp",
        "-f", "bestaudio",
        "-x",
        "--audio-format", "mp3",
        f"--audio-quality", quality,
        "--add-metadata",
        "--embed-thumbnail",
        "--no-warnings",
        "-o", f"{download_dir}/%(title)s.%(ext)s",
        url
    ]

    try:
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
        
    except Exception as e:
        yield f"Error during download: {str(e)}"

def main():
    st.title("🎧 YouTube Music Playlist Downloader")
    st.markdown("Paste your YouTube Music Playlist URL below:")

    url = st.text_input("Playlist URL", placeholder="https://music.youtube.com/playlist?list=...")
    quality = st.selectbox("Select Audio Quality", options=["128K", "192K", "320K"], index=1)

    # Test yt-dlp installation
    if st.button("Test yt-dlp Installation"):
        try:
            result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                st.success(f"✅ yt-dlp is installed. Version: {result.stdout.strip()}")
            else:
                st.error(f"❌ yt-dlp error: {result.stderr}")
        except subprocess.TimeoutExpired:
            st.error("❌ yt-dlp command timed out")
        except Exception as e:
            st.error(f"❌ yt-dlp not found or error: {str(e)}")

    if st.button("Analyze Playlist"):
        if not url:
            st.error("⚠️ Please enter a valid playlist URL.")
            return

        if "youtube.com" not in url and "youtu.be" not in url:
            st.error("⚠️ Please enter a valid YouTube/YouTube Music URL.")
            return

        with st.spinner("🔍 Fetching playlist info..."):
            videos = get_playlist_info(url)
            
        if videos:
            total_songs = len(videos)
            st.success(f"✅ Found **{total_songs} songs** in the playlist.")
            
            # Show first few song titles for verification
            with st.expander("📋 Preview Songs", expanded=False):
                for i, video in enumerate(videos[:10]):  # Show first 10
                    title = video.get('title', 'Unknown Title')
                    uploader = video.get('uploader', 'Unknown Artist')
                    st.write(f"{i+1}. {title} - {uploader}")
                if len(videos) > 10:
                    st.write(f"... and {len(videos) - 10} more songs")
            
            st.session_state["videos"] = videos
            st.session_state["total_songs"] = total_songs
            st.session_state["url"] = url
        else:
            st.error("❌ Could not fetch playlist information. Please check the URL and try again.")

    if st.button("Start Download"):
        if "total_songs" not in st.session_state:
            st.error("⚠️ Please analyze playlist first.")
            return

        total_songs = st.session_state["total_songs"]
        url = st.session_state["url"]

        st.info(f"📥 Starting download of {total_songs} songs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.warning("⚠️ **Note:** Files will be stored temporarily on the server. Download may not be accessible directly due to hosting limitations.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        song_counter_text = st.empty()

        try:
            log_container = st.expander("📋 Download Log", expanded=True)
            log_lines = []
            total_lines = total_songs * 10  # approximate

            for i, output in enumerate(download_playlist(url, quality, song_counter_text)):
                log_lines.append(output)
                status_text.text(output.strip()[:100] + "..." if len(output.strip()) > 100 else output.strip())
                progress = min(i / total_lines, 1.0)
                progress_bar.progress(progress)
                
                # Show recent log lines
                with log_container:
                    if len(log_lines) > 15:
                        st.text("\n".join(log_lines[-15:]))  # Show last 15 lines
                    else:
                        st.text("\n".join(log_lines))

            st.success("✅ Download process completed!")
            
            # Check if files were downloaded
            download_dir = "/tmp/downloads"
            if os.path.exists(download_dir):
                files = [f for f in os.listdir(download_dir) if f.endswith('.mp3')]
                if files:
                    st.info(f"🎵 {len(files)} MP3 files were processed.")
                    st.warning("📝 **Note:** For actual downloads to your device, please run this app locally on your computer.")
            
        except Exception as e:
            st.error(f"❌ Download failed: {str(e)}")

    # Usage tips
    with st.expander("💡 Usage Tips & Local Installation"):
        st.markdown("""
        **For downloading files to your device, run locally:**
        
        1. **Install Requirements:**
        ```bash
        pip install streamlit yt-dlp
        ```
        
        2. **Run the App:**
        ```bash
        streamlit run app.py
        ```
        
        **URL Formats that work:**
        - `https://music.youtube.com/playlist?list=PLxxxxx`
        - `https://www.youtube.com/playlist?list=PLxxxxx`
        
        **Download Quality:**
        - 128K: Good quality, smaller file size
        - 192K: Better quality (recommended)
        - 320K: Best quality, larger file size
        """)

if __name__ == "__main__":
    # Configure Streamlit for Render
    st.set_page_config(
        page_title="YouTube Music Downloader",
        page_icon="🎧",
        layout="wide"
    )
    main()
