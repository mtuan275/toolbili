import os
import telebot
import yt_dlp
import whisper
import subprocess
from flask import Flask
from threading import Thread

API_TOKEN = '8773811366:AAHEYTrg7KZqKST2t93VngaJVozZLpaT35E'
bot = telebot.TeleBot(API_TOKEN)

print("Đang tải mô hình Whisper AI...")
model = whisper.load_model("tiny") 
print("Bot Render đã sẵn sàng!")

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Bot Render Online: Hãy gửi link video để tải và làm phụ đề!")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def handle_video_link(message):
    url = message.text
    chat_id = message.chat.id
    bot.send_message(chat_id, "📥 Đang tải video từ server...")
    
    ydl_opts = {'outtmpl': 'video_goc.%(ext)s', 'format': 'best[ext=mp4]/best'}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            video_input = "video_goc.mp4"
            if os.path.exists(filename) and filename != video_input:
                os.rename(filename, video_input)

        bot.send_message(chat_id, "🧠 AI đang tạo phụ đề (Sub)...")
        result = model.transcribe(video_input)
        
        srt_path = "sub.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result['segments'], start=1):
                start = format_time(segment['start'])
                end = format_time(segment['end'])
                text = segment['text'].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

        bot.send_message(chat_id, "🎬 Đang add phụ đề vào video...")
        video_output = "video_hoanthien.mp4"
        ffmpeg_cmd = f'ffmpeg -y -i {video_input} -vf "subtitles={srt_path}" -c:a copy {video_output}'
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        bot.send_message(chat_id, "✅ Thành công! Đang gửi video...")
        with open(video_output, 'rb') as video:
            bot.send_video(chat_id, video)
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Lỗi: {str(e)}")
    finally:
        for file in ["video_goc.mp4", "sub.srt", "video_hoanthien.mp4"]:
            if os.path.exists(file): os.remove(file)

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.polling(none_stop=True)
    