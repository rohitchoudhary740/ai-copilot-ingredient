import streamlit as st
from PIL import Image
import json
import os
from openai import OpenAI
import base64
from io import BytesIO

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Ingredient AI Co-Pilot", layout="centered")
st.markdown(
    """
    <style>
    section.main > div { max-width: 720px; }
    </style>
    """,
    unsafe_allow_html=True
)


st.title("Ingredient AI Co-Pilot")

st.caption(
    "An AI-native assistant that interprets food ingredients and helps you decide — "
    "without overwhelming you."
)


# ----------------------------
# OpenAI client (defensive)
# ----------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY not found. Please set it in Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# ----------------------------
# Load ingredient database
# ----------------------------
with open("data/ingredients.json") as f:
    ING_DB = json.load(f)

def match_ingredients(text):
    text = text.lower()
    return [i for i in ING_DB if i["name"] in text]

# ----------------------------
# Image helpers
# ----------------------------
def image_to_base64(img):
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"

def extract_ingredients_from_image(image_b64):
    prompt = (
        "You are reading a food packet image.\n"
        "Extract ONLY the ingredient list text exactly as written.\n"
        "Do not explain. Do not summarize.\n"
        "If unclear, make your best guess."
    )

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_b64},
                ],
            }
        ],
    )

    return response.output_text

# ----------------------------
# AI copilot logic
# ----------------------------
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

You must respond using ALL of these sections:

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
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

# ----------------------------
# UI
# ----------------------------
st.subheader("1. Show the product")

uploaded = st.file_uploader(
    "Upload a food packet ingredient label",
    type=["jpg", "jpeg", "png"]
)

st.caption(
    "You can upload an image, paste ingredients manually, or do both."
)


raw_text = ""

if uploaded:
    image = Image.open(uploaded)
    st.image(image, use_column_width=True)

st.subheader("2. Ingredient information")

raw_text = st.text_area(
    "Ingredient text (auto-filled from image when possible):",
    height=160,
    placeholder="Example: Rolled oats, sugar, almonds, maltodextrin..."
)

st.divider()

if st.button("Explain ingredients", use_container_width=True):

    if uploaded:
        img_b64 = image_to_base64(image)
        with st.spinner("Reading ingredients from image…"):
            raw_text = extract_ingredients_from_image(img_b64)
            st.subheader("Extracted ingredients")
            st.text(raw_text)

    if not raw_text.strip():
        st.warning("Could not extract ingredients. Please paste text manually.")
        st.stop()

    evidence = match_ingredients(raw_text)

    with st.spinner("AI is reasoning for you…"):
        output = ai_copilot(raw_text, evidence)

    st.subheader("AI Insight")
    st.write(output)

  st.caption(
    "This is evidence-aware decision support, not medical or dietary advice."
)

