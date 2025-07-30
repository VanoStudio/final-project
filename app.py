import streamlit as st
import re
import urllib.parse
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIG ===
OPENROUTER_API_KEY = "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"  # Replace with your OpenRouter key
MODEL = "deepseek/deepseek-chat-v3-0324:free"

# === FUNCTION: EXTRACT MOVIE NAME ===
def extract_movie_name(user_input):
    match = re.search(r"(watch|about|think|review|film|movie|ulasan)\s+(.+)", user_input, re.IGNORECASE)
    if match:
        return match.group(2).strip(" ?!.")
    return user_input.strip(" ?!.")

# === FUNCTION: SCRAPE REVIEWS ===
def get_reviews(film):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    search_url = f"https://www.rottentomatoes.com/search?search={urllib.parse.quote(film)}"
    driver.get(search_url)
    time.sleep(2)

    try:
        first_result = driver.find_element(By.CSS_SELECTOR, 'search-page-media-row a')
    except:
        driver.quit()
        return []

    film_url = first_result.get_attribute("href")
    review_url = film_url.rstrip("/") + "/reviews"
    driver.get(review_url)
    time.sleep(2)

    reviews = [r.text for r in driver.find_elements(By.CSS_SELECTOR, '.review-text') if r.text.strip()]
    driver.quit()
    return reviews

# === FUNCTION: ANALYZE WITH LLM ===
def analyze_reviews(movie, reviews):
    prompt = f"""
    You are a movie critic AI.
    Analyze the Rotten Tomatoes reviews for the movie '{movie}':
    {reviews[:8]}

    1. Summarize the main opinions.
    2. Perform sentiment analysis (positive/negative/mixed).
    3. Decide if the film is worth watching or not, and explain why.
    """

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        result = response.json()
        ai_text = result.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ AI did not return a response.")
    except Exception as e:
        ai_text = f"⚠️ Error calling OpenRouter API: {e}"

    # 🔥 Add movie title as header
    return f"## 🎬 {movie}\n\n{ai_text}"

# === STREAMLIT CHATBOT ===
st.title("🎥 Rotten Tomatoes Movie Review Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask me about a movie..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    movie_name = extract_movie_name(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Searching reviews for '{movie_name}'..."):
            reviews = get_reviews(movie_name)

            if not reviews:
                reply = f"❌ Sorry, I couldn't find reviews for '{movie_name}'."
            else:
                reply = analyze_reviews(movie_name, reviews)

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
