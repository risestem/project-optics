from utils.llm import generate_plan, generate_manim_code
from utils.helpers import animate_scene, generate_session

if __name__ == "__main__":
    topic = "binary search"
    plan = generate_plan(topic)
    print("Generated Plan:")
    print(plan)
    manim_result = generate_manim_code(plan)
    print("Code:")
    print(manim_result["manim_code"])
    session_id=12345
    video_path = animate_scene(manim_result["manim_code"], session_id)
    print("Video:")
    print(video_path)
 
 
