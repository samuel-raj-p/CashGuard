import streamlit as st, subprocess, os, sys

st.set_page_config(page_title="CashGuard Launcher", page_icon="🛡️", layout="centered")

st.title("🛡️ CashGuard | CV @samuel-raj-p")
st.markdown("Use this interface to launch your computer vision app securely and easily.")

alarm_file = st.file_uploader("🔊 Upload Alarm Sound File (MP3)", type=["mp3"])
save_dir = st.text_input("💾 Enter Directory to Save Logs and Photos", value="C:/Users/Samuel Raj/Downloads")

start = st.button("🚀 Start CashGuard")

if start:
    if not alarm_file or not save_dir:
        st.error("❌ Please upload the alarm file and enter a save path.")
    else:
        # Save the alarm locally
        alarm_path = os.path.join(save_dir, "alarm.mp3")
        with open(alarm_path, "wb") as f:
            f.write(alarm_file.read())

        # Run CashGuard
        command = ["python", "CashGuard.py", save_dir, alarm_path]
        st.success("✅ Running... (Check your terminal window)")
        subprocess.Popen(command)
