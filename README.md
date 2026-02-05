# Encode Video to Target Filesize

Makes a smaller copy of a video.
Just drag and drop a video on to the script file.

Attempts to target **10MB** (i.e. the current Discord upload limit). 

By default, it resizes videos down to 720p and 30fps (does not upscale). Uses H.264 video and 96kbps opus audio. The video bitrate is dynamically adjusted to fit the target filesize.

Almost all defaults can be overridden via command line arguments.

Supports basically any format that FFMpeg supports. 
Cross-platform (Windows, Linux, MacOS). Cross-architecture (x86, x64, ARM, ARM64). Cross-really-everything (if Python+FFMpeg runs on it, it works).

## Installation
Right-click **[here](https://raw.githubusercontent.com/MissingNO123/encode-video-to-target-filesize/refs/heads/main/encode-to-filesize.py)** and save-as

## Requirements

### Python

Make sure you have Python 3 installed. Any version works. **On Windows**, make sure you select "Add Python to PATH" during installation.

### FFMpeg

#### **On Windows:** 
Either use Winget:
```powershell
winget install --id=Gyan.FFmpeg -e
```
or, if you want to do it manually (or [WinGet breaks](https://autistic.vision/images/microsoft.png)), go to FFMpeg's [website](https://www.gyan.dev/ffmpeg/builds/), download `ffmpeg-git-full.7z`, extract the [7z](https://www.7-zip.org/) file to somewhere cool, then manually add the `bin` folder to your [PATH](https://letmegooglethat.com/?q=how+to+add+to+path+on+windows).



#### **On Linux:**
Get it from your package manager, e.g.
```bash
# Debian/Ubuntu
sudo apt install ffmpeg
# Fedora
sudo dnf install ffmpeg
# Arch
sudo pacman -S ffmpeg 
# ...etc
# If you're on Linux you already know what to do
```

## Usage

### From the File Explorer

Drag and drop a video file on top of the script. It will make a smaller copy of the video, using the default settings, and put the finished video right next to the source video.

### From the Command Line

For more advanced functionality, you can use the command line. To get started, type `-h` or `--help` to show the entire list of functions. You'll get something like this:

```powershell
$ python encode-to-filesize.py --help
usage: encode-to-filesize.py [-h] [-n NAME] [-t TARGET_SIZE] [-vw WIDTH] [-vh HEIGHT] [-f FPS] [-i IN_POINT] [-o OUT_POINT] [-cv VIDEO_CODEC]
                             [-ca AUDIO_CODEC] [-ba AUDIO_BITRATE] [-m] [-at AUDIO_TRACKS] [--audio-track-name AUDIO_TRACK_NAME] [-y] [-v]
                             file

Encode a video to a target file size. By default, resizes videos down to 720p and 30fps (does not upscale), uses 96kbps AAC audio, H.264 video,
attempts to target 10MB (i.e. the current Discord upload limit), and saves to the same directory as the input file. Supports dragging and dropping
files onto the script.

positional arguments:
  file                  Input video file

options:
  -h, --help            show this help message and exit
  -n, --name NAME       Output file name
  -t, --target-size TARGET_SIZE
                        Target file size in MB
  -vw, --width WIDTH    Scale to this Width
  -vh, --height HEIGHT  Scale to this Height
  -f, --fps FPS         Target frame rate
  -i, --in-point IN_POINT
                        Trim start time in HH:MM:SS format
  -o, --out-point OUT_POINT
                        Trim end time in HH:MM:SS format
  -cv, --video-codec VIDEO_CODEC
                        Override the video codec to use
  -ca, --audio-codec AUDIO_CODEC
                        Override the audio codec to use
  -ba, --audio-bitrate AUDIO_BITRATE
                        Target audio bitrate in kbps
  -m, --merge-audio     Merge all audio tracks into one (by default only first audio track is used)
  -at, --audio-tracks AUDIO_TRACKS
                        A list of which specific audio tracks to merge, comma separated (e.g. "0,2")
  --audio-track-name AUDIO_TRACK_NAME
                        Name for the final merged audio track
  -y, --yes             Overwrite output files without asking
  -v, --verbose         Enable verbose output (e.g. show ffmpeg output)
```

## CLI Examples

#### Trim a video to the first 60 seconds, auto-scale to 480p/60fps, and target 5MB:
```bash
python encode-to-filesize.py input.mp4 -o 60 -vh 480 -f 60 -t 5
```
Height is scaled to 480p and width is auto-scaled to maintain aspect ratio.
Times can just be entered as seconds. 
`-i` does not need to be specified if you trim from the start. 
Likewise, `-o` does not need to be specified if you're trimming to the end.

#### Select the first two audio tracks and merge them, name the final audio track "Merged Audio"
```bash
python encode-to-filesize.py input.mp4 -at 0,1 --audio-track-name "Merged Audio"
```
Exceptionally useful if you use something like OBS or Nvidia ShadowPlay that records multiple audio tracks (e.g. game audio and microphone) separately.

#### Encode a video to 50MB using HEVC video codec and AAC audio codec, with 128kbps audio:
```bash
python encode-to-filesize.py input.mp4 -t 50 -cv libx265 -ca aac -ba 128
```
Overriding the audio bitrate can give better quality but cuts into the video bitrate.

## Overriding Defaults
If you have e.g. Nitro and want to always make high quality videos or something, make a `.sh` or `.bat` file with your preferred settings so you don't have to type them every time. You can drop files onto that instead.

#### Linux / MacOS `.sh`:
```bash
#!/bin/bash
python /path/to/encode-to-filesize.py "$@" -vh 720 -f 60 -t 50 -ca aac -cv libx265 -ba 128
```
#### Windows `.bat`:
```bat
@echo off
python C:\path\to\encode-to-filesize.py %* -vh 720 -f 60 -t 50 -ca aac -cv libx265 -ba 128
```

You can make a bunch of these for different presets if you want, like if you upload to different sites with different filesize limits.