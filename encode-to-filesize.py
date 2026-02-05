#!/usr/bin/env python3

### 
# encode-to-filesize.py
# Encodes a video to a target file size using ffmpeg
# Made to fit Discord's stupid 10MB upload limit
# MissingNO123, 2024
###

import sys
import os
import argparse
import subprocess


# Check if FFMPeg and FFProbe are installed and accessible
try:
    subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['ffprobe', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    print('Error: ffmpeg and/or ffprobe not found. Please install ffmpeg to use this script.')
    print('If they are installed, make sure they are in your system PATH or in the same directory as this script.')
    sys.exit(1)


def timecode_to_seconds(time_str):
    '''
    Converts timecodes from a string in HH:MM:SS format to number of seconds as a float.
    
    :param time_str: Video time in HH:MM:SS format
    :return: Time as seconds
    '''
    parts = time_str.split(':')
    parts = [float(part) for part in parts]
    while len(parts) < 3:
        parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


argparser = argparse.ArgumentParser(
    description="""Encode a video to a target file size.
By default, resizes videos down to 720p and 30fps (does not upscale),
uses 96kbps AAC audio, H.264 video,
attempts to target 10MB (i.e. the current Discord upload limit), 
and saves to the same directory as the input file.
Supports dragging and dropping files onto the script.
"""
)
argparser.add_argument('file', help='Input video file')
argparser.add_argument('-t', '--target-size', type=int, help='Target file size in MB', default=10)
argparser.add_argument('-ba', '--audio-bitrate', type=int, help='Audio bitrate in kbps', default=96)
argparser.add_argument('-vw', '--width', type=int, help='Width of the video')
argparser.add_argument('-vh', '--height', type=int, help='Height of the video')
argparser.add_argument('-i', '--in-point', type=str, help='Start time in HH:MM:SS format')
argparser.add_argument('-o', '--out-point', type=str, help='End time in HH:MM:SS format')
argparser.add_argument('-n', '--name', type=str, help='Output file name')
argparser.add_argument('-y', '--yes', action='store_true', help='Overwrite output files without asking')
argparser.add_argument('-m', '--merge-audio', action='store_true', help='Merge all audio tracks')
argparser.add_argument('-at', '--audio-tracks', type=str, help='List of specific audio tracks to merge, comma separated (e.g. "0,2")')
argparser.add_argument('--audio-track-name', type=str, help='Name for the audio track', default='Why are you looking at this?')
argparser.add_argument('-f', '--fps', type=int, help='Output frame rate', default=30)
argparser.add_argument('-ca', '--audio-codec', type=str, help='Audio codec to use', default='libopus')
argparser.add_argument('-cv', '--video-codec', type=str, help='Video codec to use', default='libx264')
argparser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output (e.g. show ffmpeg output)')

args = argparser.parse_args()

# Test for invalid args
if args.audio_tracks and args.merge_audio:
    print("""
Invalid Input: Cannot use --merge-audio and --audio-tracks together.
                --audio-tracks already merges specified audio tracks.
                Use either --merge-audio to merge all audio tracks,
                or use --audio-tracks to specify individual audio tracks to merge.""")
    sys.exit(1)
if args.fps and args.fps < 1:
    print('Invalid Input: FPS must be at least 1')
    sys.exit(1)
if args.target_size and args.target_size < 1:
    print('Invalid Input: Target size must be at least 1 MB')
    sys.exit(1)
if args.audio_bitrate and args.audio_bitrate < 1:
    print('Invalid Input: Audio bitrate must be at least 1 kbps')
    sys.exit(1)
if (args.width != None and args.width < 2) or (args.height != None and args.height < 2):
    print('Invalid Input: Width and Height must be at least 2 pixels')
    sys.exit(1)

file = args.file
file = os.path.normpath(file)
target_size_mb = args.target_size
if not os.path.isfile(file):
    print('File not found or valid: ' + file)
    sys.exit(1)

if args.name:
    file_name = args.name
else:
    file_name = os.path.basename(file)
    file_name = os.path.splitext(file_name)[0]
folder_path = os.path.dirname(file)

target_size = target_size_mb * 1000 * 1000 * 8 # 8Mbit
if target_size > 1_000_000_000: # 1 GB
    input_str = input(f'Target file size is {target_size_mb/1000:.3g} GB, are you sure you want to proceed? (y/n): ')
    if input_str.lower() != 'y':
        sys.exit(1)

# Get video duration and trim it if specified
video_duration_in_seconds = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file]))
video_trim_length = 0
if args.in_point and args.out_point:
    in_seconds = timecode_to_seconds(args.in_point)
    out_seconds = timecode_to_seconds(args.out_point)
    video_trim_length = out_seconds - in_seconds
    if video_trim_length < 0:
        print('Error: Invalid time range. Check your in and out points.')
        sys.exit(1)
    if video_trim_length > video_duration_in_seconds:
        video_trim_length = video_duration_in_seconds
elif args.in_point and not args.out_point:
    in_seconds = timecode_to_seconds(args.in_point)
    video_trim_length = video_duration_in_seconds - in_seconds
    if video_trim_length < 0:
        print('Error: Invalid time range. Check your in point.')
        sys.exit(1)
elif not args.in_point and args.out_point:
    out_seconds = timecode_to_seconds(args.out_point)
    video_trim_length = out_seconds
    if video_trim_length > video_duration_in_seconds:
        print('Error: Invalid time range. Check your out point.')
        sys.exit(1)
if video_trim_length > video_duration_in_seconds or video_trim_length == 0:
    print('Warning: Specified trim length exceeds video duration or is zero. Using full video length.')
    video_trim_length = video_duration_in_seconds

# Get video dimensions and calculate new dimensions
dimensions = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', file]).decode().strip().split('x')
width = int(dimensions[0])
height = int(dimensions[1])
if args.width != None and args.height != None:
    width = args.width
    height = args.height
elif args.width != None and args.height == None:
    resize_ratio = args.width / width
    width = args.width
    height = int(height * resize_ratio)
elif args.height != None and args.width == None:
    resize_ratio = args.height / height
    height = args.height
    width = int(width * resize_ratio)
# Resize video to 1280x720 if it's larger than 720p
elif width * height > 1280 * 720:
    # preserve original values for aspect ratio calculation
    orig_w = width
    orig_h = height
    if orig_w > orig_h:
        # scale width down to 1280 and compute height from original aspect ratio
        width = 1280
        height = int(1280 * orig_h / orig_w)
    else:
        # scale height down to 720 and compute width from original aspect ratio
        height = 720
        width = int(720 * orig_w / orig_h)
# ensure even dimensions
width  += width  % 2
height += height % 2

# Determine audio stream count (0 if no audio streams)
audio_streams_raw = subprocess.check_output([
    'ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', file
]).decode().strip()
if audio_streams_raw == '':
    audio_stream_count = 0
else:
    audio_stream_count = len([ln for ln in audio_streams_raw.splitlines() if ln.strip()])

# Get audio stream names and put them in a list
audio_stream_names = subprocess.check_output([
    'ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index:stream_tags=title', '-of', 'csv=p=0', file
]).decode().strip().splitlines()

length_rounded_up = int(video_trim_length) + 1
total_bitrate = target_size // length_rounded_up

# If there is audio, reserve the requested audio bitrate. Otherwise all bitrate goes to video.
if audio_stream_count > 0:
    audio_bitrate = args.audio_bitrate * 1000
else:
    audio_bitrate = 0

video_bitrate = total_bitrate - audio_bitrate
if video_bitrate <= 0:
    # ensure a sane minimum video bitrate
    video_bitrate = max(100_000, total_bitrate // 2)

ffmpeg_command = [
    'ffmpeg', '-i', file,
    '-c:v', args.video_codec,
    '-b:v', str(video_bitrate),
    '-maxrate:v', str(video_bitrate),
    '-bufsize:v', str(max(1, target_size // 20)),
    '-vf', f'scale={width}:{height}',
]

# Add audio parameters only when audio streams exist
if audio_stream_count > 0:
    ffmpeg_command.extend(['-metadata:s:a:0', 'title=' + args.audio_track_name])
    ffmpeg_command.extend(['-b:a', str(audio_bitrate), '-c:a', args.audio_codec])

# construct audio map string for merging audio streams when there are multiple audio streams
if args.merge_audio and audio_stream_count > 1:
    audio_map_string = ''
    for i in range(0, audio_stream_count):
        audio_map_string += f'[0:a:{i}]'
    audio_map_string += f'amix={audio_stream_count}:duration=longest:normalize=1[aout]'
    ffmpeg_command.extend(['-filter_complex', audio_map_string])
    ffmpeg_command.extend(['-map', '0:v:0'])
    ffmpeg_command.extend(['-map', '[aout]'])
# or merge selected audio tracks if specified
elif args.audio_tracks:
    track_indices = [int(idx) for idx in args.audio_tracks.split(',') if idx.strip().isdigit()]
    if len(track_indices) == 0:
        print('Error: No valid audio track indices provided.')
        sys.exit(1)
    audio_map_string = ''
    for i in track_indices:
        if i < audio_stream_count:
            audio_map_string += f'[0:a:{i}]'
            print(f'Including audio track index {i}: ' + (audio_stream_names[i] if i < len(audio_stream_names) else 'Unknown Title'))
        else:
            print(f'Warning: Audio track index {i} is out of range. Skipping.')
    if audio_map_string == '':
        print('Error: No valid audio tracks to merge after checking indices.')
        sys.exit(1)
    audio_map_string += f'amix={len(track_indices)}:duration=longest:normalize=1[aout]'
    ffmpeg_command.extend(['-filter_complex', audio_map_string])
    ffmpeg_command.extend(['-map', '0:v:0'])
    ffmpeg_command.extend(['-map', '[aout]'])
elif audio_stream_count > 0:
    # only use first audio track
    ffmpeg_command.extend(['-map', '0:v:0', '-map', '0:a:0'])
else:
    # no audio in source - map only video
    ffmpeg_command.extend(['-map', '0:v:0'])



if args.fps:
    orig_fps = int(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=s=x:p=0', file]).decode().strip().split('/')[0])
    if args.fps < orig_fps:
        ffmpeg_command.extend(['-r', str(args.fps)])

if args.in_point:
    ffmpeg_command.extend(['-ss', args.in_point])
if args.out_point:
    ffmpeg_command.extend(['-to', args.out_point])
if args.yes == True:
    ffmpeg_command.append('-y')

ffmpeg_command.append(f'{folder_path}/{file_name}-{str(target_size_mb)}mb.mp4')

print("FFMPEG Command:")
print(' '.join(ffmpeg_command))

if args.verbose:
    subprocess.run(ffmpeg_command)
else:
    subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
