import os
os.chdir("C:/Users/benny/movie_recommender")
import numpy as np
import pandas as pd
import math
import time
import matplotlib.pyplot as plt
from all_movies_scraper import info_all_movies

# Modelling
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer


def recommend():
    print("-----------------------------------------------\n")
    print("           Letterboxd Movie Scraper\n")
    print("-----------------------------------------------")
    
    # Determine profile and whether to scrape
    rerun = input("Would you like to scrape a profile? Y or N: ")
    if rerun == "Y":    
        profile = str(input("Enter Letterboxd profile name: "))
        print("-----------------------------------------------")
        start_time = time.time()
        info_all_movies(profile, pages=100)
    elif rerun == "N":
        profile = input("Enter Letterboxd profile for recommendations: ")
        print("-----------------------------------------------")
        start_time = time.time()
    else:
        print("Invalid input")
        return
    
    
    # Read data
    try:
        df = pd.read_excel("top_movies.xlsx", header=0, sheet_name=f'{profile} movies')
    except ValueError:
        print("User not in database. Please scrape profile first.")
    
    print("Loading data...")
    # Group release dates by decade
    df['year'] = df['year'].apply(lambda x: math.floor(x/10)*10)
    # Seperate categorical data into single phrases
    df.themes = df.themes.str.replace(', ', '')
    df.themes = df.themes.str.replace(' ', '')
    df.themes = df.themes.str.replace(',', ' ')
    df.themes = df.themes.str.replace('-', '')
    df.genres = df.genres.str.replace(',', ' ')
    df.actors = df.actors.str.replace(' ', '')
    df.actors = df.actors.str.replace(',', ' ')
    df.director = df.director.str.replace(' ', '')
    df.director = df.director.str.replace(',', ' ')
    
    
    feature_cols = ['title', 'year', 'director', 'actors', 'genres', 'themes', 'language', 'rating']
    target_col = f'{profile} score'
    
    # Replace unwatched movie scores with nan value
    df.loc[df[target_col] == -1, target_col] = np.nan
    
    # Split the dataset into watched and unwatched movies
    watched_df = df[df[target_col].notna()]
    unwatched_df = df[df[target_col].isna()]
    
    
    # Split the watched data into training and testing sets
    X_watched = watched_df[feature_cols]
    y_watched = watched_df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(X_watched, y_watched, test_size=0.1, random_state=42)
    
    # Define preprocessing for each column
    preprocessor = ColumnTransformer(
        transformers=[
            ('year', StandardScaler(), ['year']),
            ('rating', StandardScaler(), ['rating']),
            ('genres', OneHotEncoder(handle_unknown='ignore'), ['genres']),
            ('actors', TfidfVectorizer(), 'actors'),
            ('director', TfidfVectorizer(), 'director'),
            ('themes', TfidfVectorizer(), 'themes')
        ],
        remainder='drop'
    )
    
    # Define the pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('imputer', SimpleImputer(strategy='mean')),  # Impute missing user ratings with the mean value
        ('regressor', RandomForestRegressor(n_estimators=1000, random_state=42, n_jobs=-1, verbose=0, oob_score=True))
    ])
    
    print("Training Model")
    # Train the model on watched movies
    model = pipeline.fit(X_train, y_train)
    
    print(f"RF train accuracy: {model.score(X_train, y_train):.3f}")
    print(f"RF test accuracy: {model.score(X_test, y_test):.3f}")
    print("-----------------------------------------------")
    
    # Predict ratings for the unwatched movies
    X_unwatched = unwatched_df[feature_cols]
    try:
        print("Predicting recommendations...")
        unwatched_df = unwatched_df.copy()
        unwatched_df.loc[:, 'predicted_rating'] = model.predict(X_unwatched)
    except ValueError:
        print(f"All movies in database watched by {profile}. Scrape more movies for recommendations.")
        return

    
    # Display top n recommended unwatched movies
    top_n = 20
    recommended_movies = unwatched_df.sort_values(by='predicted_rating', ascending=False)
    print(f'Top {top_n} recommended unwatched movies:')
    for i in range(1, top_n+1):
        print(f"{i}. {recommended_movies.iloc[i-1, 0]}")
    print("-----------------------------------------------")
    end_time = time.time()
    print(f"Final time elapsed: {end_time-start_time:.1f}s")
    
    # Calculate most important features for predicting and plot
    feature_names = model[:-1].get_feature_names_out()
    mdi_importances = pd.Series(
        model[-1].feature_importances_, index=feature_names
    ).sort_values(ascending=True)
    
    plt.figure()
    ax = mdi_importances.iloc[-20:-1].plot.barh()
    ax.set_title("Random Forest Feature Importances (MDI)")
    plt.tight_layout()
    

reccommend()