# Movie Recommendation (Random Forest Regression)
A machine learning model to predict movies that a Letterboxd user may like based on their previously watched movies. The machine learning model is a random forest regression model using Scikit learn. It is based on item-based collaborative filtering rather than user-based since this is a small personal project. 

The data for the model is scraped from their profile and stored in an Excel file. Additionally, the top few thousand movies are scraped to recommend unwatched movies. Data that is scraped for each movie includes:
- Movie Title
- Release Year (grouped by decade)
- Cast (top 5 actors listed)
- Director(s)
- Genre(s)
- Themes
- Primary Language
- Average Rating
- User Score (if applicable)

## How to Run the Code
Once again, this is mostly a personal project to learn new machine learning techniques, frameworks, and generally improve my coding skills. Some of the code is specifically written to use the directories on my computer which would need to be changed (e.g., line 2: recommend.py). I also haven't built a command line interface or anything to run it so the code will need to be downloaded and run on your local IDE.

## Further Improvements
- Develop a command line interface or app to run the code on any computer easier
- Generalise some code
- Make scraping code more efficient as right now it takes roughly [number of movies/72] minutes to scrape all movies as any more results in failed requests which affects the final dataset. Furthermore, make saving the data more efficient as right now it is scraping thousands of the most popular movies each time a new profile is scraped. Collating all data into a single Excel spreadsheet would reduce the scraping time immensely and would allow for user-based recommendations.
- Fine-tune the parameters of the model

## Acknowledgements
I had no experience with web scraping before this project and a lot of the code was based on and developed from [javipzv's code]((https://github.com/javipzv/letterbox-stats/blob/main/README.md)). 

