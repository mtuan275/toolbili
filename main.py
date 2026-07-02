import os
import telebot
import yt_dlp
import speech_recognition as sr
from pydub import AudioSegment
import subprocess
from flask import Flask
from threading import Thread

API_TOKEN = '8773811366:AAHEYTrg7KZqKST2t93VngaJVozZLpaT35E'
bot = telebot.TeleBot(API_TOKEN)

print("Bot Render (Bản Siêu Nhẹ) đã sẵn sàng!")

def format_time_srt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Bot Render Online: Hãy gửi link video để tải và làm phụ đề tự động!")

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

        bot.send_message(chat_id, "🧠 Đang xử lý âm thanh và tạo phụ đề...")
        
        # Trích xuất âm thanh từ video sang file wav để nhận diện
        audio_path = "audio.wav"
        subprocess.run(f'ffmpeg -y -i {video_input} -ac 1 -ar 16000 {audio_path}', shell=True, check=True)
        
        # Sử dụng Google Speech Recognition chia nhỏ file nhận diện để không tốn RAM
        r = sr.Recognizer()
        sound = AudioSegment.from_wav(audio_path)
        
        # Cắt âm thanh theo phân đoạn 5 giây để tạo sub
        chunk_length_ms = 5000 
        chunks = [sound[i:i + chunk_length_ms] for i in range(0, len(sound), chunk_length_ms)]
        
        srt_path = "sub.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks, start=1):
                chunk_file = f"chunk_{i}.wav"
                chunk.export(chunk_file, format="wav")
                
                start_sec = (i - 1) * 5
                end_sec = start_sec + (len(chunk) / 1000.0)
                
                text = ""
                with sr.AudioFile(chunk_file) as source:
                    audio_data = r.record(source)
                    try:
                        # Tự động nhận diện (hỗ trợ cả tiếng Việt vi-VN, tiếng Trung zh-CN, hoặc tiếng Anh en-US)
                        text = r.recognize_google(audio_data, language="vi-VN")
                    except:
                        text = "..." # Bỏ qua nếu đoạn đó là khoảng lặng hoặc không nghe rõ
                
                if text.strip() and text != "...":
                    f.write(f"{i}\n{format_time_srt(start_sec)} --> {format_time_srt(end_sec)}\n{text}\n\n")
                
                if os.path.exists(chunk_file): os.remove(chunk_file)

        bot.send_message(chat_id, "🎬 Đang tiến hành ghép phụ đề vào clip...")
        video_output = "video_hoanthien.mp4"
        ffmpeg_cmd = f'ffmpeg -y -i {video_input} -vf "subtitles={srt_path}" -c:a copy {video_output}'
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        bot.send_message(chat_id, "✅ Thành công! Đang gửi video...")
        with open(video_output, 'rb') as video:
            bot.send_video(chat_id, video)
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Lỗi: {str(e)}")
    finally:
        for file in ["video_goc.mp4", "audio.wav", "sub.srt", "video_hoanthien.mp4"]:
            if os.path.exists(file): os.remove(file)

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.polling(none_stop=True)
