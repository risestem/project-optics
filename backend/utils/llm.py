import json

from google import genai
from google.genai import types

client = genai.Client()

SYSTEM_INSTRUCTIONS = """You are an educational explainer that produces step-by-step lessons on a given topic. Each step pairs a written explanation with a visual animation that reinforces what is being taught.

# OUTPUT FORMAT
You MUST respond with ONLY a single valid JSON object. No prose before or after. No markdown code fences. No commentary. The JSON must exactly match this schema:

{
  "topic": "<the topic being explained>",
  "total_duration_seconds": <integer, sum of all step durations>,
  "steps": [
    {
      "step_number": <integer, starting at 1>,
      "explanation": "<clear, self-contained text explanation of this step>",
      "animation": {
        "description": "<concrete visual description of the animation that should play during this step>",
        "start_time_seconds": <integer, cumulative start offset from the beginning of the lesson>,
        "duration_seconds": <integer, how long this animation plays, between 3 and 30>,
        "end_time_seconds": <integer, equals start_time_seconds + duration_seconds>
      }
    }
  ]
}

# RULES
1. Output MUST be valid, parseable JSON. No trailing commas. Use double quotes for all keys and string values.
2. Produce between 3 and 8 steps. Each step builds on the previous one in a logical teaching order.
3. The first step's `start_time_seconds` MUST be 0. Each subsequent step's `start_time_seconds` MUST equal the previous step's `end_time_seconds` (no gaps, no overlaps).
4. `total_duration_seconds` MUST equal the `end_time_seconds` of the final step.
5. `explanation` should be 2-5 sentences, plain text, no markdown, no newlines inside the string.
6. `animation.description` MUST be visually concrete (describe shapes, motion, colors, labels) so it can be rendered. Do NOT describe abstract ideas — describe what is on screen.
7. The animation MUST directly reinforce the explanation in the same step.
8. Do NOT include any field not listed in the schema. Do NOT include any text outside the JSON object.

# ANIMATION SIMPLICITY RULES (CRITICAL)
The animations you describe will later be rendered by a separate model into Manim (Community Edition) code. Complex or ambitious animation ideas fail to render correctly, so every `animation.description` MUST be deliberately simple and minimal. A good animation conveys ONE idea with a handful of shapes — not a cinematic scene.
- Use at most 5-6 on-screen elements per step (shapes, labels, arrows combined).
- Stick to basic 2D primitives only: circles, squares, rectangles, lines, arrows, dots, short text labels, simple math formulas. No 3D, no perspective, no camera moves, no particle effects, no gradients, no custom graphics.
- Prefer simple motions: fade in, fade out, draw/create, move along a straight path, scale, transform one shape into another. Avoid choreographed or multi-stage motion.
- At most ~3-5 distinct visual actions per step. If an idea needs more, split it across multiple steps.
- Use plain named colors (blue, red, green, yellow, white). Do not invent custom palettes.
- Do NOT describe things that are hard to render: realistic objects, handwriting, images, photos, audio, voiceover, physics simulations, or anything requiring external assets.
- When in doubt, pick the simpler visual. Minimal animations that clearly land the concept are strongly preferred over ambitious ones.
"""

MANIM_SYSTEM_INSTRUCTIONS = """You are a Manim code generator. Given a complete lesson plan with multiple steps, you produce ONE runnable Manim Community Edition Python script that renders ALL segments back-to-back inside a SINGLE Scene. The resulting video will be played in a frontend that seeks to specific timestamps to jump between steps, so the timing of each segment MUST be exact.

# OUTPUT FORMAT
You MUST respond with ONLY raw Python code. No prose. No markdown code fences. No commentary before or after. The first line of your response MUST be a Python import statement.

# HARD REQUIREMENTS
1. Use `from manim import *` at the top.
2. Define exactly ONE Scene subclass named `LessonScene` with a `construct(self)` method.
3. The script must render ALL steps from the plan, in order, inside that single `construct` method.
4. For each step N, the cumulative scene time at the START of step N's animations MUST equal the step's `start_time_seconds`, and the cumulative scene time at the END MUST equal the step's `end_time_seconds`. Use `self.wait(...)` and animation `run_time=` arguments to hit these targets exactly.
5. Before each step's animations begin, insert a Python comment of the form `# === STEP <n>: t=<start>s -> t=<end>s ===` so the timestamps are visible in the source.
6. Between steps, clear the previous step's mobjects from the screen (use `FadeOut(*self.mobjects)` or equivalent) so segments don't visually pile up. The clear-out counts toward the previous step's duration, not the next step's.
7. The total scene runtime MUST equal the plan's `total_duration_seconds`.
8. The script MUST be self-contained and runnable with: `manim -ql script.py LessonScene`.
9. Do NOT import anything outside of `manim` and the Python standard library.
10. Do NOT read external files, fetch URLs, or rely on external assets (no SVGs, images, or fonts).

# MINIMALISM RULES (CRITICAL — animations must be cheap to render)
- Keep each segment as SIMPLE as possible while still conveying the idea. Render time and resource cost matter, and the whole script renders as one video.
- Use no more than 5-6 mobjects on screen at any time.
- Prefer basic primitives: `Circle`, `Square`, `Rectangle`, `Line`, `Arrow`, `Dot`, `Text`, `MathTex`.
- Avoid: 3D scenes, `ThreeDScene`, complex `ValueTracker` chains, heavy `updater` functions, particle effects, long `Transform` sequences, and more than ~6 animation calls per step.
- Prefer `Create`, `Write`, `FadeIn`, `FadeOut`, `Transform` over exotic animation classes.
- Use short `run_time` values (0.5-2 seconds per animation call) and fill remaining time with `self.wait()` to land exactly on each step's `end_time_seconds`.
- Use plain colors (`BLUE`, `RED`, `GREEN`, `WHITE`, `YELLOW`). No gradients, no custom shaders.
- No voiceovers, no sound, no camera movement unless absolutely required.

# STYLE
- Clear variable names. No comments other than the required `# === STEP ... ===` markers.
- Keep the entire script under ~150 lines total even with many steps.
"""


def generate_plan(topic):
    response = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTIONS,
                response_mime_type="application/json",
            ),
            contents=f"Topic to explain: {topic}",
                )

    return response.text


def generate_manim_code(instructions):
    """Generate a single Manim script that renders every lesson step back-to-back.

    The returned script defines one `LessonScene` whose cumulative timing
    matches the per-step timestamps in the plan, so the frontend can play one
    video and seek between `start_time_seconds` markers to jump between steps.

    Args:
        instructions: JSON string returned by `generate_plan` (matches the
            schema defined in SYSTEM_INSTRUCTIONS).

    Returns:
        {
            "topic": str,
            "total_duration_seconds": int,
            "manim_code": str,          # single runnable script, Scene = LessonScene
            "segments": [               # timestamp map for the frontend
                {
                    "step_number": int,
                    "explanation": str,
                    "animation_description": str,
                    "start_time_seconds": int,
                    "end_time_seconds": int,
                    "duration_seconds": int,
                },
                ...
            ],
        }
    """
    plan = json.loads(instructions)
    topic = plan.get("topic", "")

    segments = [
        {
            "step_number": step["step_number"],
            "explanation": step["explanation"],
            "animation_description": step["animation"]["description"],
            "start_time_seconds": step["animation"]["start_time_seconds"],
            "end_time_seconds": step["animation"]["end_time_seconds"],
            "duration_seconds": step["animation"]["duration_seconds"],
        }
        for step in plan["steps"]
    ]

    prompt = (
        f"Lesson topic: {topic}\n"
        f"Total duration (seconds): {plan['total_duration_seconds']}\n\n"
        "Full lesson plan (JSON):\n"
        f"{json.dumps(plan, indent=2)}\n\n"
        "Generate ONE Manim script that renders every step back-to-back inside "
        "a single LessonScene. Each step must begin at its start_time_seconds "
        "and end exactly at its end_time_seconds. Insert the required "
        "# === STEP n: t=Xs -> t=Ys === comment before each step's animations. "
        "Keep every segment minimal."
    )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction=MANIM_SYSTEM_INSTRUCTIONS,
        ),
        contents=prompt,
    )

    code = response.text.strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[1] if "\n" in code else code
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()
    if code.startswith("python\n"):
        code = code[len("python\n"):]

    return {
        "topic": topic,
        "total_duration_seconds": plan["total_duration_seconds"],
        "manim_code": code,
        "segments": segments,
    }


