from lxml import html
from concurrent.futures import ThreadPoolExecutor
from ratelimit import limits, sleep_and_retry
import requests
import pandas as pd
import re

# Checks if fetch limit has been exceeded to avoid errors
@sleep_and_retry
@limits(calls=72, period=60)
def check_limit():
    ''' Empty function just to check for calls to API '''
    return


# Get data from webpage
def fetch(url):
    check_limit()
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Ubuntu Chromium/71.0.3578.80 "
                      "Chrome/71.0.3578.80 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.text
    except requests.exceptions.RequestException:
        print(f"Request failed for {url} (Error 429)")
    return None


def request(urls):
    with ThreadPoolExecutor(max_workers=64) as executor:
        results = executor.map(fetch, urls)
    return results

# Transforms star symbols to rating
def info_profile(username,  comp = ""):
    def transform_valoration(val):
        value = -1
        if val:
            if val.__contains__("★") or val.__contains__("½"):
                value = val.count("★") + val.count("½")/2
        return value
    
    
    headers = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Ubuntu Chromium/71.0.3578.80 "
                            "Chrome/71.0.3578.80 Safari/537.36"}

    url = f"https://letterboxd.com/{username}/films/"
    
    # Find how many pages of movies have been watched
    page = requests.get(url, headers=headers)
    tree = html.fromstring(page.content)
    pages = tree.xpath('/html/body/div[1]/div/div/section/div[2]/div[3]/ul/li/a')[-1].text

    print("Collecting Profile Movie Data")
    page_urls = []
    for i in range(1, int(pages) + 1):
        page_urls += [f"https://letterboxd.com/{username}/films/page/" + str(i)]
    
    movie = request(page_urls)
    film_urls, film_titles, film_score = [], [], []
    
    for html_content in movie:
        # Get film titles, scores, and average ratings
        tree = html.fromstring(html_content)
        scores = tree.xpath('/html/body/div[1]/div/div/section/ul/li[@class="poster-container"]')
        for data in scores:
            div = data.find('div')
            title = div.attrib.get('data-target-link')
            title = re.findall(".*\/(.*)\/$", title)[0]
            film_titles += [title]
            span = data.find('p/span')
            if span is not None:
                film_score.append(span.text)
            else:
                film_score.append("No valorada")
        
        result = tree.xpath('/html/body/div[1]/div/div/section/ul/li/div')
        for film in result:
            link = "https://letterboxd.com" + film.attrib.get('data-target-link')
            film_urls += [link]
    
    production = request(film_urls)
    rating = []
    
    for html_content in production:
        tree = html.fromstring(html_content)
        rate = tree.xpath('//*[@id="html"]/body/script[3]/text()').__str__()
        # Slice rating number from html script
        try:
            idx = rate.index('ratingValue')
            number = [rate[int(idx+i)] for i in range(13,17)]
            if number[2] == '"':
                rating.append(int(number[0]))
            else:
                rating.append(''.join(number).replace(",", "0"))
        except:
            rating.append("-1")
    
    # Return dataframe to scraper
    df_movies = pd.DataFrame({
        "title": film_titles,
        "score" + comp: list(map(transform_valoration, film_score)),
        "rating": rating
        })

    print("All Profile Movie Data Collected")
    print("-----------------------------------------------")
    
    # Count how many unrated movies there were and remove them
    rated = df_movies.count().get('title')
    df_movies = df_movies.drop(df_movies[df_movies['score'] == -1].index)
    unrated = df_movies.count().get('title')
    print(f"Removing {rated-unrated} Unrated Movies")
    return df_movies
