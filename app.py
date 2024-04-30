from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
# import json
import pickle
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
# Importez la classe Query pour effectuer des requêtes sur la base de données Firestore
from google.cloud.firestore import Query

app = Flask(__name__)
CORS(app)
# Charger le modèle de clustering
with open("rest_model2.pkl", "rb") as file:
    rest_model = pickle.load(file)

# Charger le modèle TF-IDF
# tfidf = joblib.load("tfidf_model2.pkl")
with open("tfidf_model2.pkl", "rb") as file:
    tfidf = pickle.load(file)

# Initialiser Firestore
cred = credentials.Certificate("restaurant-812f8-firebase-adminsdk-g2av2-bf9da32758.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Fonction pour récupérer les données des restaurants des utilisateurs
restaurants = []
menuData = []

def get_restaurants_from_users():
    users_ref = db.collection("users")
    users = users_ref.get()

    for user in users:
        user_data = user.to_dict()
        if "restaurantData" in user_data:
            restaurants.append(user_data["restaurantData"])
    return restaurants

# Route pour afficher les données des restaurants
@app.route("/")
def get_restaurants():
    restaurants = get_restaurants_from_users()
    if restaurants:
        # print("restaurants:",restaurants)
        return jsonify(restaurants)
    else:
        print("Aucun restaurant trouvé.")
        return "Aucun restaurant trouvé."

@app.route("/get_menu", methods=["POST"])
def get_menu():
    data = request.json
    # print("data : ", data)
    restaurantName = data.get("restaurantName")  # Récupérer l'UID du restaurant depuis les données envoyées par le frontend
    # print("restaurantName : ", restaurantName)

    if not restaurantName:
        print("restaurantName du restaurant non fourni")
        return jsonify({"error": "restaurantName du restaurant non fourni"}), 400
    
    # Effectuer une requête pour obtenir l'UID du restaurant en utilisant le nom du restaurant comme filtre
    users_ref = db.collection("users").where("restaurantData.restaurantName", "==", restaurantName)
    users = users_ref.get()
    # print("users : ", users)
    # Si aucun utilisateur correspondant n'est trouvé, renvoyer une erreur
    if not users:
        print("Aucun utilisateur correspondant trouvé pour ce nom de restaurant")
        return jsonify({"error": "Aucun utilisateur correspondant trouvé pour ce nom de restaurant"}), 404

    # Supposons qu'il n'y a qu'un seul utilisateur correspondant, donc nous prenons le premier
    user = users[0].to_dict()
    # print("user : ", user)
    restaurant_uid = user.get("uid")
    # print("restaurant_uid : ", restaurant_uid)

    # Récupérer le premier menu correspondant à l'UID du restaurant avec limit(1)
    # menus_ref = db.collection("menus").where("uid", "==", restaurant_uid).limit(1)
    menus_ref = db.collection("menus").where("uid", "==", restaurant_uid).order_by("jour", direction=Query.DESCENDING).limit(1)
    menus = menus_ref.get()
    # print("menus : ", menus)
    
    if not menus:
        return jsonify({"error": "Aucun menu trouvé pour cet UID de restaurant"}), 404
    restaurant_menus = []
    for menu in menus:
        menu_data = menu.to_dict()
        # print("menu_data le plus récent: ", menu_data)
        restaurant_menus.append(menu_data)

    if not restaurant_menus:
        return jsonify({"error": "Aucun menu trouvé pour cet UID de restaurant"}), 404
    # print("restaurant_menus : ", restaurant_menus)   
    return jsonify({"restaurant_menus": restaurant_menus})
pass


@app.route("/predict_sentiment", methods=["POST"])
def predict_sentiment():
    data = request.json
    # print("data: ", data)
    text = data["text"]
    text_vectorized = tfidf.transform([text])
    sentiment = rest_model.predict(text_vectorized)[0]
    return jsonify({"sentiment": sentiment})

if __name__ == "__main__":
    app.run(debug=True)
