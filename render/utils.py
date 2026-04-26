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
    # 1. negate: inverts colors (#11121d bg → #eeede2)
    # 2. hue=H=PI: rotate hue 180° to restore accent colors
    # 3. curves: remap so white point lands at #d5d6db
    #    Input bg after negate: R≈0.933 G≈0.929 B≈0.886
    #    Target bg: R=0.835 G=0.839 B=0.859
    #    Black stays black (0/0), bg maps to target (in/out per channel)
    vf = (
        'negate,'
        'hue=H=PI,'
        'curves='
        'r=\'0/0 0.933/0.835 1/0.9\':'
        'g=\'0/0 0.929/0.839 1/0.9\':'
        'b=\'0/0 0.886/0.859 1/0.92\''
    )
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vf', vf,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'copy',
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
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