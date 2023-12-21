import numpy as np
from sklearn.metrics import pairwise_distances
from collections import defaultdict
from sklearn.metrics.pairwise import euclidean_distances
from azure.cosmos import CosmosClient, PartitionKey
import numpy as np
from collections import defaultdict

ENDPOINT = 'https://tutorial-uta-cse6332.documents.azure.com:443/'
KEY = 'fSDt8pk5P1EH0NlvfiolgZF332ILOkKhMdLY6iMS2yjVqdpWx4XtnVgBoJBCBaHA8PIHnAbFY4N9ACDbMdwaEw=='
client = CosmosClient(url=ENDPOINT, credential=KEY)

database = client.get_database_client('tutorial')
reviews = database.get_container_client('reviews')
cities = database.get_container_client('us_cities')


def initialize_seeds(distance_matrix, n_seeds):
    # 随机选择N个种子城市
    seeds = np.random.choice(distance_matrix.shape[0], n_seeds, replace=False)
    return seeds


def assign_to_nearest_seeds(distance_matrix, seeds, k):
    # 为每个城市分配类别
    categories = defaultdict(list)
    for city in range(distance_matrix.shape[0]):
        # 计算到种子城市的距离
        distances = distance_matrix[city, seeds]
        nearest_seeds = np.argsort(distances)[:k]
        for seed in nearest_seeds:
            categories[seed].append(city)
        # 分配类别
        # categories[city] = nearest_seeds
        k_categories = dict(list(categories.items())[:k])
    print(len(categories))
    return categories, k_categories


def find_category_centers(categories, distance_matrix):
    # 找到每个类别的中心城市
    category_centers = {}
    for category, cities in categories.items():
        center_city = min(cities, key=lambda city: np.mean(distance_matrix[city, cities]))
        category_centers[f'category{category}'] = center_city
    return category_centers


city_locations = []
query = "SELECT us_cities.lat, us_cities.lng FROM us_cities"
items = cities.query_items(query=query, enable_cross_partition_query=True)
for item in items:
    city_locations.append(list(item.values()))
distance_matrix = euclidean_distances(city_locations, city_locations)


def knn(n_seeds, k, words_number):
    # 初始化种子城市
    seeds = initialize_seeds(distance_matrix, n_seeds=n_seeds)
    print(seeds)
    # 为每个城市分配类别
    categories,k_categories = assign_to_nearest_seeds(distance_matrix, seeds, k=k)
    # print(categories)
    # 找到每个类别的中心城市
    category_centers = find_category_centers(categories, distance_matrix)
    print(f'category_centers:{category_centers}')
    # read stopwords.txt
    stopwords = []
    with open('stopwords.txt', mode='r', encoding='utf-8') as f:
        for line in f:
            stopwords.append(line.strip())
    category_words_counts = {}
    category_scores = {}
    city_list = []
    city_dict = {}
    for category, citys in k_categories.items():
        ids = ["item-" + str(city) for city in citys]
        formatted_ids = ', '.join(f"'{id}'" for id in ids)
        sql_query = f"SELECT reviews.city,reviews.id,reviews.review,reviews.score FROM reviews WHERE reviews.id IN ({formatted_ids})"
        items_reviews = reviews.query_items(query=sql_query, enable_cross_partition_query=True)
        for item in items_reviews:
            city_list.append(item['city'])
        city_dict[f'category{category}'] = city_list[:k]
    for category, citys in categories.items():
        ids = ["item-" + str(city) for city in citys]
        formatted_ids = ', '.join(f"'{id}'" for id in ids)
        sql_query = f"SELECT reviews.city,reviews.id,reviews.review,reviews.score FROM reviews WHERE reviews.id IN ({formatted_ids})"
        sql_query2 = f"SELECT cities.id,cities.population FROM cities WHERE cities.id IN ({formatted_ids})"
        items_reviews = reviews.query_items(query=sql_query, enable_cross_partition_query=True)
        items_citys = cities.query_items(query=sql_query2, enable_cross_partition_query=True)
        # def items_reviews():
        #     return reviews.query_items(query=sql_query, enable_cross_partition_query=True)
        # def items_citys():
        #     return cities.query_items(query=sql_query2, enable_cross_partition_query=True)
        word_counts = {}
        for item in items_reviews:
            # city_list.append(item['city'])
            review_text = item['review']
            words = review_text.lower().split()
            for word in words:
                if word not in stopwords:
                    word_counts[word] = word_counts.get(word, 0) + 1
        # 属于该类别的城市列表
        # city_dict[f'category{category}'] = city_list
        # print(f'city_dict:{city_dict}')
        sorted_items = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)
        # 如果你想要一个排序后的字典
        sorted_dict = dict(sorted_items)
        # print(sorted_dict)
        category_words_counts[category] = sorted_dict
        split_category_words_counts = {}
        for category, words_counts in category_words_counts.items():
            split_words_count = dict(list(words_counts.items())[:words_number])
            split_category_words_counts[f'category{category}'] = split_words_count

        # ---------------------------------------------------------------
        pop_socre = {}
        sum_score = 0
        avg_score = 0
        sum_pop = 0
        # for item_c in items_citys:
        #     print(item_c)
        for item_r in items_reviews:
            for item_c in items_citys:
                print(item_c['id'], item_r['id'])
                if item_c.get('id') == item_r.get('id'):
                    print(item_c['population'], item_r['score'])
                    sum_score += item_c['population'] * item_r['score']
                    sum_pop += int(item_c['population'])
        # avg_score = sum_score / sum_pop
        category_scores[f'category{category}'] = avg_score
    print(f'category_centers:{category_centers}')
    print(f'category_scores:{category_scores}')
    print(f'split_category_words_counts:{split_category_words_counts}')
    print(f'city_dict:{city_dict}')

    result = {}
    result['1-category_centers'] = category_centers
    result['2-category_scores'] = category_scores
    result['3-popular_word'] = split_category_words_counts
    result['6-city_list'] = city_dict

    return result
