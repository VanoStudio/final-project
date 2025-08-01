import streamlit as st
import re
import urllib.parse
import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIG ===
# Replace with your OpenRouter key

with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("Customize the chatbot here.")

    OPENROUTER_API_KEY = st.text_input("🔑 OpenRouter API Key", type="password")
    MODEL = st.selectbox("🤖 Model", ["deepseek/deepseek-chat-v3-0324:free"])

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.search_results = []
        st.session_state.selected_movie = None
        st.rerun()
# === EXTRACT MOVIE NAME ===
def extract_movie_name(user_input):
    match = re.search(r"(watch|about|think|review|film|movie|ulasan)\s+(.+)", user_input, re.IGNORECASE)
    if match:
        return match.group(2).strip(" ?!.")
    return user_input.strip(" ?!.")

# === SEARCH MOVIES ===
def search_movies(film):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    search_url = f"https://www.rottentomatoes.com/search?search={urllib.parse.quote(film)}"
    driver.get(search_url)

    try:
        results = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'search-page-media-row a, search-page-result a'))
        )
    except:
        driver.quit()
        return []

    movies = []
    for r in results:
        href = r.get_attribute("href")
        title = r.text.strip()
        if href and title:
            movies.append((title, href))

    driver.quit()
    return movies

# === GET CRITIC + AUDIENCE REVIEWS WITH SCROLL AND WAIT ===
def get_reviews(movie_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    critic_url = movie_url.rstrip("/") + "/reviews"
    audience_url = movie_url.rstrip("/") + "/reviews?type=user"
    all_reviews = []

    selectors = ".review-text, .review-text__text, .audience-reviews__review"

    # 1️⃣ Critics
    driver.get(critic_url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selectors))
        )
    except:
        pass
    critic_reviews = [r.text for r in driver.find_elements(By.CSS_SELECTOR, selectors) if r.text.strip()]
    all_reviews.extend(critic_reviews)

    # 2️⃣ Audience
    driver.get(audience_url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selectors))
        )
    except:
        pass
    audience_reviews = [r.text for r in driver.find_elements(By.CSS_SELECTOR, selectors) if r.text.strip()]
    all_reviews.extend(audience_reviews)

    driver.quit()
    return all_reviews

# === CALL AI ===
def analyze_reviews(movie, reviews):
    sample_reviews = [r[:300] for r in reviews[:8]]

    prompt = f"""
    You are a movie critic AI.
    Analyze the Rotten Tomatoes reviews (critics and audience) for the movie '{movie}':
    {json.dumps(sample_reviews, indent=2)}

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
            timeout=180
        )
        result = response.json()
        if "choices" not in result:
            return f"## 🎬 {movie}\n\n⚠️ AI did not return a response. Check ur API OPENROUTER OR Ur Connection ‼️"
        ai_text = result["choices"][0]["message"]["content"]
    except Exception as e:
        ai_text = f"⚠️ Error calling OpenRouter API: {e}"

    return f"## 🎬 {movie}\n\n{ai_text}"

# === STREAMLIT UI ===
st.title("🎥 Rotten Tomatoes Movie Review Chatbot")
st.markdown("This is Suggestion for Prompt")
st.code(f"""Review Inception\nWhat do you think about Interstellar?\nIs Oppenheimer worth watching?\nGive me a summary of Barbie reviews""")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# Step 1: User input
if prompt := st.chat_input("Ask me about a movie..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    movie_query = extract_movie_name(prompt)
    with st.chat_message("assistant"):
        with st.spinner(f"Searching for '{movie_query}'..."):
            results = search_movies(movie_query)

        if not results:
            reply = f"❌ Sorry, I couldn't find any movies for '{movie_query}'."
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.session_state.search_results = results
            st.rerun()

# Step 2: Movie selection
if st.session_state.search_results and not st.session_state.selected_movie:
    st.subheader("Select the correct movie:")
    options = [title for title, _ in st.session_state.search_results]
    choice = st.selectbox("Choose a movie", options)

    if st.button("Get Reviews"):
        for title, url in st.session_state.search_results:
            if title == choice:
                st.session_state.selected_movie = (title, url)
                st.rerun()

# Step 3: Scrape reviews and analyze
if st.session_state.selected_movie:
    title, url = st.session_state.selected_movie
    with st.chat_message("assistant"):
        with st.spinner(f"Scraping critic and audience reviews for '{title}'..."):
            reviews = get_reviews(url)
            st.write(f"DEBUG: {len(reviews)} reviews scraped")
            if not reviews:
                reply = f"❌ Sorry, I couldn't find reviews for '{title}'."
            else:
                reply = analyze_reviews(title, reviews)

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

    # Reset state
    st.session_state.search_results = []
    st.session_state.selected_movie = None
