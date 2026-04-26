import os
import subprocess
import tempfile
import boto3

def animate_scene(scene_code, id):
    if "from manim import *" not in scene_code:
        scene_code = "from manim import *\n" + scene_code

    with tempfile.NamedTemporaryFile('w', prefix='manim_', suffix='.py', delete=False) as temp_file:
        temp_file.write(scene_code)
        temp_file_path = temp_file.name

    file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    try:
        cmd = [
            'manim',
            '-qh',
            temp_file_path,
            'LessonScene',
            '--media_dir', f'/tmp/{id}',
            '--output_file', f'{id}.mp4',
            '--disable_caching',
        ]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Error: {e}")
        return None
    return f'/tmp/{id}/videos/{file_name}/1080p60/{id}.mp4'

def create_light_version(video_path, output_path):
    # 1. negate: invert colors
    # 2. hue=H=PI: rotate hue 180° to restore accent colors
    # 3. colorchannelmixer: per-channel multiply to match #d5d6db bg
    #    Calibrated from measured output #d7d9f5 → target #d5d6db
    # 4. format=yuv420p: ensure pixel format is compatible with libx264
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vf', 'negate,hue=H=PI,colorchannelmixer=rr=0.887:gg=0.890:bb=0.866,format=yuv420p',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'copy',
        output_path,
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            print(f"Light mode conversion produced empty file")
            return None
        return output_path
    except Exception as e:
        print(f"Light mode conversion error: {e}")
        return None

def upload_to_r2(file_path, destination_key):

    s3 = boto3.client(
        "s3",
        endpoint_url="https://dd67a598299321e22ac175612949d61d.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY"],
        aws_secret_access_key=os.environ["R2_SECRET_KEY"],
        region_name="auto",
    )

    s3.upload_file(file_path, "optics-renders", destination_key)

    return f"https://pub-5237fee679584978874e2fc440c7ef08.r2.dev/{destination_key}"