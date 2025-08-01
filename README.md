# 🎥 Rotten Tomatoes Movie Review Chatbot

This is a **Streamlit-based web app** that acts as a movie review assistant.  
It scrapes **Rotten Tomatoes** for critic and audience reviews of a movie, analyzes them using AI (via the OpenRouter API), and provides a **summary, sentiment analysis, and watch recommendation**.

---

## ⚠️ Usage Warning

> ❗ **Do not use this tool excessively or in rapid succession.**

This scraper accesses Rotten Tomatoes using **Selenium**, which may be detected as bot activity. If overused, Rotten Tomatoes can:

- Temporarily or permanently **block your IP address**
- Redirect you to error or captcha pages
- Prevent scraping and return no reviews

---

### ✅ How to Avoid Being Blocked

- Use only **1–2 times per minute**
- **Wait a few minutes** between each review request
- If you see errors or "not found" messages even for known films:
  - Try **switching your internet connection** (different IP)
  - Use a **VPN or mobile hotspot**
  - Run it from a different browser or device if needed

---

## 📸 DOCUMENTATION

### 1. Prompting and Searching the Film
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f0bccf12-7d10-4069-97f2-31d1a80ab89b" />

### 2. Make sure the title of the Film
<img width="1904" height="930" alt="image" src="https://github.com/user-attachments/assets/dcbea31b-65bd-48eb-8daf-db60b397d06f" />

### 3. Scrapping data & Process to the LLM
<img width="1920" height="924" alt="image" src="https://github.com/user-attachments/assets/cf334644-60b5-4c14-8663-94716efa038b" />

### 4. Result from the LLM
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/3620de09-f107-415c-a7fe-7f6083417e19" />


## 🚀 Features
- 🔍 **Movie Search:** Automatically searches Rotten Tomatoes based on user input.
- 📜 **Review Scraping:** Collects both critic and audience reviews using Selenium.
- 🤖 **AI Analysis:** Uses OpenRouter's LLM API to summarize reviews and determine sentiment.
- 💬 **Chat Interface:** Interactive chat-style UI with Streamlit.
- 🖥️ **Auto Movie Selection:** Displays search results for the user to choose the correct movie.
- ✅ **Real-time Sentiment:** AI decides if the movie is worth watching.

---

## 🛠️ Tech Stack
- **Python 3.8+**
- [Streamlit](https://streamlit.io/) - for the web UI
- [Selenium](https://www.selenium.dev/) - for scraping Rotten Tomatoes
- [OpenRouter API](https://openrouter.ai/) - for AI-powered analysis
- [ChromeDriver Manager](https://pypi.org/project/webdriver-manager/) - for automatic Chrome driver handling

---

## 📌 Code Documentation


### 📌 Imports
```python
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

```
- streamlit: For building the interactive UI.

- re: Regular expressions to extract movie names from user input.

- urllib.parse: Encoding movie titles for URLs.

- requests: Sending API requests to OpenRouter.

- json: Formatting data for API communication.

- time: Sleep for scrolling and waiting during scraping.

- selenium: Web scraping Rotten Tomatoes.

- webdriver_manager: Automatically installs and manages ChromeDriver.


### 🎛️ Sidebar Configuration

```python
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("Customize the chatbot here.")

    # API key input field (hidden with password type)
    OPENROUTER_API_KEY = st.text_input("🔑 OpenRouter API Key", type="password")

    # Model selection dropdown (currently only one option)
    MODEL = st.selectbox("🤖 Model", ["deepseek/deepseek-chat-v3-0324:free"])

    # Button to clear session state (resets chat)
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.search_results = []
        st.session_state.selected_movie = None
        st.rerun()
```

### 🔍 Movie Name Extraction

```python
def extract_movie_name(user_input):
    """
    Extracts the movie name from user input using regex patterns.
    Example:
        'Review Inception' -> 'Inception'
        'What do you think about Interstellar?' -> 'Interstellar'
    """
    match = re.search(r"(watch|about|think|review|film|movie|ulasan)\s+(.+)", user_input, re.IGNORECASE)
    if match:
        return match.group(2).strip(" ?!.")
    return user_input.strip(" ?!.")

```


### 🎥 Movie Search (Rotten Tomatoes)

```python
def search_movies(film):
    """
    Searches Rotten Tomatoes for a given movie title.
    Uses Selenium to scrape search results.
    Returns a list of tuples: [(title, url), ...]
    """
    options = Options()
    options.add_argument("--headless")      # Run browser without UI
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    search_url = f"https://www.rottentomatoes.com/search?search={urllib.parse.quote(film)}"
    driver.get(search_url)

    try:
        # Wait until search results are loaded
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

```

### 📜 Review Scraping
```python
def get_reviews(movie_url):
    """
    Scrapes critic and audience reviews for the given movie URL.
    Scrolls the page to ensure all content is loaded.
    Returns a combined list of review texts.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    critic_url = movie_url.rstrip("/") + "/reviews"
    audience_url = movie_url.rstrip("/") + "/reviews?type=user"
    all_reviews = []

    # CSS selectors for review text elements
    selectors = ".review-text, .review-text__text, .audience-reviews__review"

    # 1️⃣ Critic Reviews
    driver.get(critic_url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selectors)))
    except:
        pass
    critic_reviews = [r.text for r in driver.find_elements(By.CSS_SELECTOR, selectors) if r.text.strip()]
    all_reviews.extend(critic_reviews)

    # 2️⃣ Audience Reviews
    driver.get(audience_url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selectors)))
    except:
        pass
    audience_reviews = [r.text for r in driver.find_elements(By.CSS_SELECTOR, selectors) if r.text.strip()]
    all_reviews.extend(audience_reviews)

    driver.quit()
    return all_reviews

```

### 🤖 AI Analysis
```python
def analyze_reviews(movie, reviews):
    """
    Sends the scraped reviews to OpenRouter AI for analysis.
    Produces:
        - Summary of opinions
        - Sentiment analysis (Positive/Negative/Mixed)
        - Watch recommendation
    """
    # Limit to 8 sample reviews and truncate text for performance
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
            return f"## 🎬 {movie}\n\n⚠️ AI did not return a response. Check your API key or connection."
        ai_text = result["choices"][0]["message"]["content"]
    except Exception as e:
        ai_text = f"⚠️ Error calling OpenRouter API: {e}"

    return f"## 🎬 {movie}\n\n{ai_text}"

```
### 💬 Streamlit UI
```python
st.title("🎥 Rotten Tomatoes Movie Review Chatbot")
st.markdown("💡 **Try these prompts:**")
st.code("""Review Inception
What do you think about Interstellar?
Is Oppenheimer worth watching?
Give me a summary of Barbie reviews""")

```

### 🔄 Session State Initialization
```python
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

```

## 💬 Chat Flow


### 1️⃣ User Input
```python
if prompt := st.chat_input("Ask me about a movie..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    movie_query = extract_movie_name(prompt)
    with st.chat_message("assistant"):
        with st.spinner(f"Searching for '{movie_query}'..."):
            results = search_movies(movie_query)

```

### 2️⃣ Movie Selection
```python
if st.session_state.search_results and not st.session_state.selected_movie:
    st.subheader("Select the correct movie:")
    options = [title for title, _ in st.session_state.search_results]
    choice = st.selectbox("Choose a movie", options)

    if st.button("Get Reviews"):
        for title, url in st.session_state.search_results:
            if title == choice:
                st.session_state.selected_movie = (title, url)
                st.rerun()

```

### 3️⃣ Scraping + Analysis
```python
if st.session_state.selected_movie:
    title, url = st.session_state.selected_movie
    with st.chat_message("assistant"):
        with st.spinner(f"Scraping critic and audience reviews for '{title}'..."):
            reviews = get_reviews(url)
            if not reviews:
                reply = f"❌ Sorry, I couldn't find reviews for '{title}'."
            else:
                reply = analyze_reviews(title, reviews)

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

    # Reset state to allow a new search
    st.session_state.search_results = []
    st.session_state.selected_movie = None

```

### 📌 Flow Summary:

- User asks about a movie → Extracts title → Searches Rotten Tomatoes.

- Displays options for selection → Scrapes reviews → AI analysis → Shows result.

## 📜 License

MIT License. Free to use and modify.

## 👨‍💻 Author

Built with ❤️ using Python, Streamlit, Selenium, and OpenRouter AI. By VanoStudio

