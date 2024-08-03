import requests
from bs4 import BeautifulSoup
from lxml import html
from concurrent.futures import ThreadPoolExecutor
from ratelimit import limits, sleep_and_retry
import pandas as pd
import os
from profile_scraper import info_profile


# Check how many requests are being made per minute and limit to avoid errors
@sleep_and_retry
@limits(calls=72, period=60)
def check_limit():
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


def info_all_movies(username, pages, comp=""):
    # Gather movie urls and scores from user profile
    profile_data = info_profile(username)
    profile_titles = list(profile_data["title"])
    profile_ratings = list(profile_data["rating"])
    profile_score = list(profile_data["score"])
    film_titles, film_urls, score, rating = [], [], [], []
    # If user is already in database, only add new entries to list of movies to fetch
    try:
        database = pd.read_excel("top_movies.xlsx", sheet_name=f"{username} movies")
        db_series = database["title"]
        for i in range(len(profile_titles)):
            if profile_titles[i] not in db_series:
                film_titles.append(profile_titles[i])
                film_urls.append('https://letterboxd.com/film/' + profile_titles[i])
                score.append(profile_score[i])
                rating.append(profile_ratings[i])
    except:
        for i in range(len(profile_titles)):
            film_titles.append(profile_titles[i])
            film_urls.append('https://letterboxd.com/film/' + profile_titles[i])
            score.append(profile_score[i])
            rating.append(profile_ratings[i])
    

    url = "https://letterboxd.com/films/ajax/popular"
    print("-----------------------------------------------")
    print(f"Collecting {pages*72+len(film_titles)} Movie URLs")
    page_urls = [url + "/" if i == 1 else f"{url}/page/{i}/" for i in range(1, pages+1)]
    
    # Get movie titles and average ratings from page data
    for u in page_urls:
        soup = BeautifulSoup(requests.get(u).text, features="lxml")
        for e in soup.select('li.listitem'):
            title = e.div.get('data-film-slug')
            rate = e.get('data-average-rating')
            if title not in profile_titles:
                film_titles.append(title)
                film_urls.append('https://letterboxd.com/film/' + title)
                rating.append(rate)

    print("Scores and Movie URLs Collected")
    print("-----------------------------------------------")
    print("Collecting Movie Webpages")
    production = request(film_urls)
    print("Webpages Collected")
    print("-----------------------------------------------")
    print("Compiling Movie Data")

    direct, cast, category, themes = [], [], [], []
    year, language = [], []
    # Tracks how many movies have been collected
    n = 0
    for html_content in production:
        if n < len(profile_titles) and html_content is None:
            year.append("-999")
            direct.append("-999")
            cast.append("-999")
            category.append("-999")
            themes.append("-999")
            language.append("-999")
            n+=1
            continue
        
        if n >= len(profile_titles) and html_content is None:
            year.append("-999")
            direct.append("-999")
            cast.append("-999")
            category.append("-999")
            themes.append("-999")
            language.append("-999")
            score.append("-999")
            n+=1
            continue
        
        # Appends -1 to movies if they were not watched
        if n >= len(profile_titles) and html_content is not None:
            score.append("-1")
    
        
        # Gather relevant data from movie webpages
        tree = html.fromstring(html_content)
        
        release = tree.xpath('//*[@id="film-page-wrapper"]/div[2]/section[1]/div/div/div/a/text()')
        year.append(release)

        region = tree.xpath('//*[@id="tab-details"]/div[3]/p/a/text()')
        language.append(region)

        director = tree.xpath('//div[@id="tabbed-content"]/div[@id="tab-crew"]/div[1]/p/a/text()')
        direct.append(director)

        actor = tree.xpath('//div[@id="tab-cast"]/div/p/a/text()')
        cast.append(actor[:10])

        genre = tree.xpath('//div[@id="tab-genres"]/div[1]/p/a/text()')
        category.append(genre)

        theme = tree.xpath('//div[@id="tab-genres"]/div[2]/p/a/text()')
        themes.append([t for t in theme if t != "Show All…"])
        
        n += 1
        
    
    print("All Movie Data Collected")
    print("-----------------------------------------------")
    
    # Store data in dataframe
    df_movies = pd.DataFrame({
        "title": film_titles,
        "year": [','.join(l) for l in year],
        "director": [','.join(l) for l in direct],
        "actors": [','.join(l) for l in cast],
        "genres": [','.join(l) for l in category],
        "themes": [','.join(l) for l in themes],
        "language": [','.join(l) for l in language],
        "rating": rating,
        f"{username} score": score
    })
    
    # Clean data of empty values and failed fetch requests
    df_movies = df_movies[df_movies.year != "-999"]
    df_movies = df_movies[df_movies.year != "-,9,9,9"]
    df_movies = df_movies[df_movies.genres != ""]
    df_movies = df_movies[df_movies.themes != ""]
    df_movies = df_movies[df_movies.rating != ""]
    df_movies = df_movies[df_movies.language != ""]
    df_movies = df_movies[df_movies.actors != ""]
    df_movies.dropna()

    # Write data to unique sheet in spreadsheet
    os.chdir("C:/Users/benny/movie_recommender")
    with pd.ExcelWriter('top_movies.xlsx', mode='a', if_sheet_exists="overlay") as writer:  
        df_movies.to_excel(writer, sheet_name=f"{username} movies", index=False)

    return df_movies