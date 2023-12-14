from flask import Flask, request, jsonify, render_template
import pandas as pd
from flask_cors import CORS
app = Flask(__name__)
from flask_cors import CORS
CORS(app)
# 加载数据
amazon_reviews = pd.read_csv('data/amazon-reviews.csv')
us_cities = pd.read_csv('data/us-cities.csv')

@app.route('/')
def index():
    return render_template('words.html')

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


@app.route('/popular_words1', methods=['GET'])
def popular_words1():
    city_name = request.args.get('city')
    limit = request.args.get('limit', type=int)

    # 如果提供了城市名称，则过滤评论
    if city_name:
        reviews = amazon_reviews[amazon_reviews['city'] == city_name]
    else:
        reviews = amazon_reviews

    # 计算单词的热度
    word_popularity = {}
    for _, row in reviews.iterrows():
        city = row['city']
        population = us_cities[us_cities['city'] == city]['population'].iloc[0]
        for word in row['review'].split():
            if word not in word_popularity:
                word_popularity[word] = {'cities': set(), 'popularity': 0}
            if city not in word_popularity[word]['cities']:
                word_popularity[word]['cities'].add(city)
                word_popularity[word]['popularity'] += population

    # 将单词热度转换为排序列表
    popular_words_list = [{'term': word, 'popularity': info['popularity']} for word, info in word_popularity.items()]
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
    for i, review in amazon_reviews['review'].iteritems():
        if original_word in review:
            new_review = review.replace(original_word, substitute_word)
            amazon_reviews.at[i, 'review'] = new_review
            affected_reviews += 1

    # 返回 JSON 响应
    return jsonify({"affected_reviews": affected_reviews})

if __name__ == '__main__':
    app.run(debug=True)
