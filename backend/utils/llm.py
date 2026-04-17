import ast
import json
import re

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

MANIM_SYSTEM_INSTRUCTIONS = """You are a Manim code generator. Given a complete lesson plan with multiple steps, you produce ONE runnable Manim Community Edition Python script that renders ALL segments back-to-back inside a SINGLE Scene. The resulting video will be played in a frontend that seeks to specific timestamps to jump between steps, so the timing of each segment must be exact.

# OUTPUT FORMAT
Respond with ONLY raw Python code — no prose, no markdown fences. First line MUST be `from manim import *`.

# HARD REQUIREMENTS
1. Use `from manim import *` at the top.
2. Define exactly ONE Scene subclass named `LessonScene` with a `construct(self)` method. Every animation call (`self.play`, `self.wait`, `self.add`, etc.) MUST live inside that method — never at module scope.
3. Render ALL steps from the plan, in order, inside that single `construct` method.
4. For each step N, the cumulative scene time at the START must equal `start_time_seconds` and at the END must equal `end_time_seconds`. Use `self.wait(...)` and `run_time=` values to land on the targets exactly.
5. Before each step's animations, insert `# === STEP <n>: t=<start>s -> t=<end>s ===`.
6. Steps MUST flow continuously. DO NOT fade to black between steps and DO NOT `FadeOut(*self.mobjects)` at the end of a step. Carry persistent elements (main diagram, axes, key labels) forward so the next step builds on what is already on screen. Only remove a specific mobject when the next step genuinely no longer needs it, and do it overlapped with new elements entering. The final step may clear all mobjects only if it is the last step in the lesson.
7. REUSE EXISTING MOBJECTS. If a shape or label is already on screen from an earlier step, reuse the existing Python variable — do not construct a new `Polygon`/`Square`/`MathTex` with the same geometry. Never animate `Create`/`FadeIn`/`Write` on a mobject already visible. To modify an existing mobject, use `.animate` (e.g. `square.animate.set_color(RED)`) or `Transform(existing, target)`.
8. Total scene runtime MUST equal the plan's `total_duration_seconds`.
9. Script must be self-contained and runnable with `manim -ql script.py LessonScene`. Import only `manim` and the Python standard library. No external files, URLs, or assets.

# MINIMALISM
- At most 5-6 mobjects on screen at any time.
- Primitives only: `Circle`, `Square`, `Rectangle`, `Line`, `Arrow`, `Dot`, `Text`, `MathTex`. Plain colors (`BLUE`, `RED`, `GREEN`, `WHITE`, `YELLOW`).
- At most ~6 animation calls per step. Prefer `Create`, `Write`, `FadeIn`, `FadeOut`, `Transform`.
- Avoid 3D scenes, heavy `updater` functions, `ValueTracker` chains, and particle effects.
- Animations must feel SNAPPY. `run_time` between 0.3 and 0.8 seconds per call (never above 1.0). Fill remaining step time with a single trailing `self.wait(...)` so the viewer has time to read.
- The first visual change in a new step should start within ~0.5 seconds of the step. No long leading `self.wait()`.
- No voiceovers, sound, or camera moves.

# STYLE
- Clear variable names. No comments other than the required `# === STEP ... ===` markers.
- Keep under ~150 lines total.
- The scene background MUST match the frontend (`#11121d`). As the first line inside `construct`, set `self.camera.background_color = "#11121d"` before any animations.
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


def _extract_code(raw):
    match = re.search(r"```(?:python)?\s*\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    start = raw.find("from manim")
    if start == -1:
        start = raw.find("import manim")
    if start != -1:
        raw = raw[start:]
    return raw.strip()


def _sanitize_manim_code(code):
    """Fix mechanical mistakes the LLM commonly makes in generated Manim scripts.

    - Rewrites `self.wait(0)` / `run_time=0` to `0.1` (Manim rejects non-positive durations).
    - Drops stray top-level statements (e.g. an orphaned `self.wait(...)` outside the class),
      which `ast.parse` alone can't catch because they're syntactically valid but blow up at
      import time with NameError.
    """
    code = re.sub(r"self\.wait\(\s*0(?:\.0+)?\s*\)", "self.wait(0.1)", code)
    code = re.sub(r"run_time\s*=\s*0(?:\.0+)?(?=\s*[,)])", "run_time=0.1", code)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        lines = code.split("\n")
        while lines:
            lines.pop()
            try:
                tree = ast.parse("\n".join(lines))
                code = "\n".join(lines)
                break
            except SyntaxError:
                continue
        else:
            return code

    allowed = (
        ast.Import,
        ast.ImportFrom,
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Assign,
        ast.AnnAssign,
        ast.If,
    )
    drop_lines = set()
    for node in tree.body:
        if isinstance(node, allowed):
            continue
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue  # module docstring
        end = node.end_lineno or node.lineno
        for ln in range(node.lineno, end + 1):
            drop_lines.add(ln)

    if drop_lines:
        source_lines = code.split("\n")
        code = "\n".join(
            line for i, line in enumerate(source_lines, start=1) if i not in drop_lines
        )

    return code.strip()


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

    code = _extract_code(response.text)
    code = _sanitize_manim_code(code)

    return {
        "topic": topic,
        "total_duration_seconds": plan["total_duration_seconds"],
        "manim_code": code,
        "segments": segments,
    }
