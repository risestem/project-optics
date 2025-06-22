import google.generativeai as genai

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

generation_config = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2000,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name = "gemini-2.0-flash",
    generation_config = generation_config,
    system_instruction = """
        You are the world's best teacher, with proficiency especially in a variety of mathematics, engineering, and computer science, including but not limited to Algorithms and Data Structures.
        You believe very strongly in the power of visual learning, and so you have trained yourself extensively in manim animations.
        
        You will assist the user by helping animate their thought process to assist with visual learning.
        What this means is that while the user is explaining their thought process, you will use python code for manim animation to draw out whatever they say.
        
        For example, if the user says "how does a queue work," you will animate the queue.
        If the user says "how do we remove items from a queue" you will reanimate the queue accordingly.
        The user will not necessarily say these words verbatim, but the general idea is that you will animate every single step.
        
        The user will not always be addressing you directly. You are an assistant, so even if the user appears to be addressing an audience, animate as if it is speaking to you.
        For example, if the user says "let's do __", interpret it as a command
        
        You are also a minimalist. Animate the least amount as possible while still communicating the user's point. Try to go step by step, only animating one line at a time.
        """
)

def call_llm(user_prompt, session_history):
    system_prompt = """
        # Your goal:
        For every concept or operation the user asks about, you must create a visual animation using Manim CE that explains the concept or operation visually.

        # Rules:
        - All code must be inside a class called [video(Scene)]
        - Do NOT import anything (assume all imports are handled).
        - Do not use any formatting wrappers like backticks (```), <tool_code>, etc. Return only the raw class code.
        - Escape all backslashes in LaTeX strings.
        - Do NOT include waits or time.sleep.
        """
    chat = model.start_chat(history=session_history, enable_automatic_function_calling=False)

    prompt = f"{system_prompt}\nGenerate a Manim animation for the following concept or operation:\n{user_prompt}"

    response = chat.send_message(prompt)
    content = response.text
    if content.strip().startswith("```"):
        content = content.strip().lstrip("`python").strip("`").strip()
    return content