import modal

manim_image = (
    modal.Image.debian_slim()
    .apt_install(
        "ffmpeg",
        "libcairo2-dev",
        "libpango1.0-dev",
        "texlive",
        "texlive-latex-extra",
        "texlive-fonts-recommended",
        "texlive-science",
    )
    .pip_install("manim", "boto3")
    .add_local_file("utils.py", "/root/utils.py")
)

app = modal.App("manim-renderer", image=manim_image)

@app.function(
    cpu=2.0,
    memory=2048,
    timeout=300,
    secrets=[modal.Secret.from_name("r2-credentials")],
)
def render_and_upload(scene_code: str, id: str) -> str | None:
    from utils import animate_scene, create_light_version, upload_to_r2

    video_path = animate_scene(scene_code, id)
    if not video_path:
        return None

    video_url = upload_to_r2(video_path, f"{id}.mp4")

    light_path = video_path.replace(f"{id}.mp4", f"{id}-light.mp4")
    if create_light_version(video_path, light_path):
        upload_to_r2(light_path, f"{id}-light.mp4")

    return video_url