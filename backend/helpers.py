import tempfile
import subprocess

def animate_scene(scene_code):
    print(scene_code)
    # Always ensure import is present
    if "from manim import *" not in scene_code:
        scene_code = "from manim import *\n" + scene_code

    with tempfile.NamedTemporaryFile('w', prefix='manim_', suffix='.py', delete=False) as temp_file:
        temp_file.write(scene_code)
        temp_file_path = temp_file.name

    try:
        cmd = [
            'manim',
            '-qh',
            temp_file_path,
            'video',
            '--media_dir', '../media',
            '--output_file', 'video.mp4'
            '--disable_caching'
        ]
        subprocess.run(cmd, check=True)
    finally:
        os.remove(temp_file_path)

def fetch_history(session_id):
    pass
