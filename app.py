import pandas as pd
from flask import Flask, render_template
from flask import Flask, render_template, url_for, request, jsonify
import csv
from flask import Flask, render_template
import pandas as pd
import csv
from flask_cors import CORS
from flask_paginate import Pagination, get_page_args

app = Flask(__name__)
CORS(app)

your_name = "Your Name"
student_id_last_5_digits = "12345"

#-------------------------------------------------------------------------------------------------------------
# @app.route('/')
# def index():
#     picture_filename = url_for('static', filename='baidi.jpg')
#     return render_template('index.html', name=your_name, id_last_5_digits=student_id_last_5_digits)


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

#-------------------------------------------------------------------------------------------------------------
@app.route('/')
def words():
    return render_template('words.html')


amazon_reviews = pd.read_csv('data/amazon-reviews.csv')
us_cities = pd.read_csv('data/us-cities.csv')

@app.route('/popular_words', methods=['GET'])
def popular_words():
    city_name = request.args.get('city')
    limit = request.args.get('limit', type=int)

    # 如果提供了城市名称，则过滤评论
    if city_name:
        reviews = amazon_reviews[amazon_reviews['city'] == city_name]
    else:
        reviews = amazon_reviews

    # 计算单词出现次数
    word_counts = {}
    for review in reviews['review']:
        for word in review.split():
            word_counts[word] = word_counts.get(word, 0) + 1

    # 将单词计数转换为排序列表
    popular_words_list = [{'term': word, 'popularity': count} for word, count in word_counts.items()]
    popular_words_list.sort(key=lambda x: x['popularity'], reverse=True)

    # 应用限制
    if limit is not None and limit < len(popular_words_list):
        popular_words_list = popular_words_list[:limit]

    return jsonify(popular_words_list)


@app.route('/substitute_words', methods=['POST'])
def substitute_words():
    data = request.get_json()
    original_word = data['word']
    substitute_word = data['substitute']

    # 计算受影响的评论数量并替换单词
    affected_reviews = 0
    for i, review in amazon_reviews['review'].items():
        if original_word in review:
            new_review = review.replace(original_word, substitute_word)
            amazon_reviews.at[i, 'review'] = new_review
            affected_reviews += 1

    # 返回 JSON 响应
    return jsonify({"affected_reviews": affected_reviews})


city_population = {}
with open('data/us-cities.csv', mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        city_population[row['city']] = int(row['population'])

# 读取 amazon-reviews.csv 文件，构建单词到城市的映射
word_to_city = {}
with open('data/amazon-reviews.csv', mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        city = row['city']
        review_text = row['review']
        words = review_text.lower().split()
        for word in words:
            if word not in word_to_city:
                word_to_city[word] = set()
            word_to_city[word].add(city)


@app.route('/popular_words1', methods=['GET'])
def popular_words1():
    # city_name = request.args.get('city')
    # word = request.args.get('word')
    limit1 = request.args.get('num', type=int)  # 默认为返回前10个受欢迎的词

    popular_words_list = []
    for word, cities in word_to_city.items():
        popularity = 0
        for city in cities:
            popularity += city_population[city]
        popular_words_list.append({"term": word, "popularity": popularity})
    popular_words_list.sort(key=lambda x: x['popularity'], reverse=True)
    print(len(popular_words_list))
    if limit1 is not None and limit1 < len(popular_words_list):
        popular_words_list = popular_words_list[:limit1]

    return jsonify(popular_words_list)




if __name__ == '__main__':
    app.run()
