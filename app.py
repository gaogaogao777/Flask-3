import pandas as pd
from flask import Flask, render_template
from flask import Flask, render_template, url_for, request, jsonify
import csv
from flask import Flask, render_template
from flask_paginate import Pagination, get_page_args

app = Flask(__name__)

your_name = "Your Name"
student_id_last_5_digits = "12345"


@app.route('/')
def index():
    # You can add your picture filename or URL here
    # picture_filename = "static/baidi.jpg"  # Replace with the actual file name
    picture_filename = url_for('static', filename='baidi.jpg')
    return render_template('index.html', name=your_name, id_last_5_digits=student_id_last_5_digits)


@app.route('/reviews')
def reviews():
    reviews_df = pd.read_csv('data/amazon-reviews.csv')
    cities_df = pd.read_csv('data/us-cities.csv')

    all_reviews = []
    for index, row in reviews_df.iterrows():
        city_details = cities_df[cities_df['city'] == row['city']].iloc[0]
        all_reviews.append({
            'score': row['score'],
            'title': row['title'],
            'review': row['review'],
            'city': row['city'],
            'city_link': f'#',
            'city_details': f'City: {city_details["city"]}<br>Latitude: {city_details["lat"]}<br>Longitude: {city_details["lng"]}<br>Country: {city_details["country"]}<br>State: {city_details["state"]}<br>Population: {city_details["population"]}',
            'image_path': f'static/score-{row["score"]}.jpg'
        })

    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')

    total = len(all_reviews)

    all_reviews  = all_reviews[offset: offset + per_page]

    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4')
    return render_template('reviews.html', reviews=all_reviews,page=page,
                           per_page=per_page, pagination=pagination)


if __name__ == '__main__':
    app.run()
