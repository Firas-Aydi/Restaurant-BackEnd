from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
# import json
import pickle
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

app = Flask(__name__)
CORS(app)
# Charger le modèle de clustering
with open("rest_model2.pkl", "rb") as file:
    rest_model = pickle.load(file)

# Charger le modèle TF-IDF
# tfidf = joblib.load("tfidf_model2.pkl")
with open("tfidf_model2.pkl", "rb") as file:
    tfidf = pickle.load(file)

# Charger les données des restaurants
# with open("restaurant_reviews_data.json", "r") as f:
# with open("r.json", "r") as f:
#     restaurants = json.load(f)
# Route pour afficher la carte des restaurants avec les avis
# @app.route("/")
# def get_restaurants():
#     return jsonify(restaurants)

# Initialiser Firestore
cred = credentials.Certificate("restaurant-812f8-firebase-adminsdk-g2av2-bf9da32758.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Fonction pour récupérer les données des restaurants des utilisateurs
restaurants = []
def get_restaurants_from_users():
    users_ref = db.collection('users')
    users = users_ref.get()

    for user in users:
        user_data = user.to_dict()
        if 'restaurantData' in user_data:
            restaurants.append(user_data['restaurantData'])
            print("Restaurant data:", user_data['restaurantData'])
    print('restaurants: ', restaurants)

    return restaurants

# Route pour afficher les données des restaurants
@app.route("/")
def get_restaurants():
    restaurants = get_restaurants_from_users()
    if restaurants:
        return jsonify(restaurants)
    else:
        return "Aucun restaurant trouvé."

@app.route("/predict_sentiment", methods=["POST"])
def predict_sentiment():
    data = request.json
    text = data["text"]
    text_vectorized = tfidf.transform([text])
    sentiment = rest_model.predict(text_vectorized)[0]
    return jsonify({"sentiment": sentiment})

if __name__ == "__main__":
    app.run(debug=True)
