#!/usr/bin/env bash
# exit on error
set -o i扩展-e

# Cài đặt các thư viện python
pip install -r requirements.txt

# Tự động tải bản FFmpeg di động để chạy trên Render
mkdir -p ffmpeg_bin
cd ffmpeg_bin
wget https://johnvansickle.com
tar -xf ffmpeg_release-amd64-static.tar.xz --strip-components=1
cd ..
export PATH=$PATH:$(pwd)/ffmpeg_bin
