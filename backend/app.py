from utils.llm import generate_plan, generate_manim_code 

if __name__ == "__main__":
    topic = "Pythagorean theorem"
    plan = generate_plan(topic)
    print("Generated Plan:")
    print(plan)
    manim_result = generate_manim_code(plan)
    print("Code:")
    print(manim_result["manim_code"])
 

