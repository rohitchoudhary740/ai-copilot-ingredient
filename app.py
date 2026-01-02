# PASTE YOUR FULL STREAMLIT CODE BELOW THIS LINE

import streamlit as st
from PIL import Image
import json
import os
from openai import OpenAI

st.set_page_config(page_title="Ingredient AI Co-Pilot", layout="centered")

st.title("🥗 Ingredient AI Co-Pilot")
st.write("Upload a packaged food ingredient label. The AI explains what matters.")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("data/ingredients.json") as f:
    ING_DB = json.load(f)

def match_ingredients(text):
    text = text.lower()
    return [i for i in ING_DB if i["name"] in text]

def ai_copilot(raw_text, evidence):
    system_prompt = """
You are an AI-native consumer health co-pilot.

Your job is NOT to explain every ingredient.
Your job is to help a person make a confident decision with minimal mental effort.

Core principles:
- Be intent-first
- Be reasoning-first
- Prioritize what matters MOST
- Communicate uncertainty honestly
- Reduce unnecessary fear

You must respond using:
What stands out
Why it matters
Why this might not matter
What is uncertain
Bottom line
"""

    evidence_block = "\n".join(
        f"- {e['name']}: {e['consensus']}" for e in evidence
    ) if evidence else "No strong evidence matched."

    user_prompt = f"""
Raw ingredient text:
{raw_text}

Evidence:
{evidence_block}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content

uploaded = st.file_uploader(
    "Upload ingredient label image (optional)",
    type=["jpg", "jpeg", "png"]
)

raw_text = ""

if uploaded:
    image = Image.open(uploaded)
    st.image(image, use_column_width=True)

st.subheader("Ingredient text")
raw_text = st.text_area(
    "Paste or edit ingredients here (AI will reason on this text):",
    height=180,
    placeholder="e.g. Whole wheat flour, sugar, maltodextrin, vitamins..."
)
if st.button("🧠 Explain as AI Co-Pilot"):
    if not raw_text.strip():
        st.warning("Please provide ingredient text for analysis.")
        st.stop()

    evidence = match_ingredients(raw_text)

    with st.spinner("AI is reasoning for you…"):
        output = ai_copilot(raw_text, evidence)

    st.subheader("AI Insight")
    st.write(output)

    st.info(
        "This is evidence-aware decision support, not medical advice."
    )
