import tempfile
import subprocess
import os
from google.cloud import storage
import shutil

def animate_scene(scene_code, id):
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
            '--media_dir', f'/tmp/{id}',
            '--output_file', f'{id}.mp4',
            '--disable_caching'
        ]
        subprocess.run(cmd, check=True)
    finally:
        os.remove(temp_file_path)
    return f'/tmp/{id}/{id}.mp4'

def upload_to_gcs(file_path, bucket_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    return blob.public_url

def clear_tmp(id):
    shutil.rmtree(f'/tmp/{id}', ignore_errors=True)