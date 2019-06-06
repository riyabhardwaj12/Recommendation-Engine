from __future__ import print_function 
from flask import Flask,request,jsonify
import pickle
import math
import operator
import boto3
import json
import decimal

from boto3.dynamodb.conditions import Key, Attr

import os
os.environ["NO_PROXY"] = "s3.amazonaws.com"

dynamodb=boto3.resource('dynamodb')


app = Flask(__name__)

#w= pickle.load(open('model.pkl','rb'))
@app.route('/')
def home():
    return ("hye :-) -->>>add '/api/cust_id' url with cust_id of user whose prediction is to be made like 1100 :)")

@app.route('/api/<x>',methods=['GET'])
def predict(x):
    table=dynamodb.Table('hungrymind-mobilehub-593518188-BookBorrow')
    data=table.scan()
    print("finished scan")

    review=dict()
    for i in data["Items"]:
        custid=i['CustID']
        bookid=i['BookID']
        rat=i['Rating']
        if custid in review.keys():
            review[custid][bookid]=float(rat)
        else:
            review[custid]=dict()
            review[custid][bookid]=float(rat)



    def get_common_books(criticA,criticB):
        return [book for book in review[criticA] if book in review[criticB]]


    def get_reviews(criticA,criticB):
        common_books = get_common_books(criticA,criticB)
        return [(review[criticA][book], review[criticB][book]) for book in common_books]


    def euclidean_distance(points):
        squared_diffs = [(point[0] - point[1]) ** 2 for point in points]
        summed_squared_diffs = sum(squared_diffs)
        distance = math.sqrt(summed_squared_diffs)
        return distance

    def similarity(reviews):
        return 1/ (1 + euclidean_distance(reviews))

    def get_critic_similarity(criticA, criticB):
        reviews = get_reviews(criticA,criticB)
        return similarity(reviews)


    def recommend_books(critic, num_suggestions):
        similarity_scores = [(get_critic_similarity(critic, other), other) for other in review if other != critic]
        similarity_scores.sort() 
        similarity_scores.reverse()
        similarity_scores = similarity_scores[0:num_suggestions]
        recommendations = {}
        
        for similarity, other in similarity_scores:
            reviewed = review[other]
            
            for book in reviewed:
                if book not in review[critic]:
                    weight = similarity * reviewed[book]
                    
                    if book in recommendations:
                        sim, weights = recommendations[book]
                        recommendations[book] = (sim + similarity, weights + [weight])
                        
                    else:
                        recommendations[book] = (similarity, [weight])
                        
        for recommendation in recommendations:
            similarity, book = recommendations[recommendation]
            recommendations[recommendation] = sum(book) / similarity
            

        sorted_recommendations = sorted(recommendations.items(), key=operator.itemgetter(1), reverse=True)
        return sorted_recommendations

    #print("Recommended Books to this user are :- ")

    w=(recommend_books(int(x),4))#here we need to give the user_id as input

    f=""
    table=dynamodb.Table('hungrymind-mobilehub-593518188-Books')
    for i in w:
        response = table.query(
        KeyConditionExpression=Key('ISBN').eq(i[0])
        )
        if(len(response['Items'])>0):
            f+=(response['Items'][0]['BookName'])+" <br>"
    return f

if __name__ == '__main__':
    app.run(debug=True)
