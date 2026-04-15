import modal

render_and_upload = modal.Function.from_name("manim-renderer", "render_and_upload")

test_code = """
from manim import *

class LessonScene(Scene):
    def construct(self):
        circle = Circle(color=BLUE)
        self.play(Create(circle))
        self.wait(2)
"""

url = render_and_upload.remote(test_code, "test_001")
print(f"Video URL: {url}")