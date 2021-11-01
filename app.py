from flask import Flask, render_template
import requests, json, re

from requests.models import Response

# Assign the Flask package to the app variable
app = Flask(__name__)

# Establish variables to use API
APP_ID = 'f558db23',
API_KEY = '2cc229e87584ee796a51f86e729084d6',
JUICY_ID = '51db37d0176fe9790a899db2'
headers = {"Content-Type": "application/json; charset=utf-8"}



# Use Flask to route data to the localhost endpoint JuicyJuice via GET
@app.route("/")
# Begin logic for getting items
def get_juicy_total():
    # Template for responses
    offset = 0
    url = 'https://api.nutritionix.com/v1_1/search'
    payload = {
        "appId": APP_ID,
        "appKey": API_KEY,
        "fields": [
            "item_name",
            "brand_name",
            "brand_id",
            "nf_calories",
            "nf_serving_size_qty",
            "nf_serving_size_unit"
        ],
        # Offset is dynamic, just in case there are more than the initial 90
        "offset": offset,
        "limit": 50,
        "filters": {
            "brand_id": JUICY_ID
        }
    }
    # Get a response based on the API url, types, and create a JSON output from the payload
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # Convert the response to JSON and assign it
    res = response.json()
    # Access lower levels of API
    total = res['total']
    juices = []

    # Use the total number of returned items against the offset of current items
    while total > offset:
        payload = {
            "appId": APP_ID,
            "appKey": API_KEY,
            "fields": [
                "item_name",
                "brand_name",
                "brand_id",
                "nf_calories",
                "nf_serving_size_qty",
                "nf_serving_size_unit",
                "nf_ingredient_statement"                
            ],
            "offset": offset,
            "limit": 50,
            "filters": {
                "brand_id": JUICY_ID
            }
        }
        # There are only 50 offsets/results at a time, so it needs to add onto the current amount for each response
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        offset = offset + 50
        res = response.json()
        hits = res['hits']
        # Iterate each hit and append a field onto it
        for hit in hits:
            juices.append(hit['fields'])

    with open('templates/total_products.json', 'w') as out:
        json.dump(juices , out)

    # For Of loop that seeks out fluid ounces and uses it to divide the calories
    for juice in juices:
        if juice['nf_serving_size_unit'] == 'fl oz':
            juice['avg_calories'] = juice['nf_calories'] / juice['nf_serving_size_qty']

    # After calculating and appending, create a JSON file
    with open('templates/nutrition.json', 'w') as out:
        json.dump(juices , out)

    ingredients_kv = {}

    for juice in juices:
        # Get the ingredient statement
        ingredient_stmt = juice['nf_ingredient_statement']
        # Check to see if ingredient statement exists
        if ingredient_stmt:
            # If it does, break it up into a list by commas, replace . and use uppercase
            ingredient_stmt = ingredient_stmt.replace(".", "").upper()
            ingredients = re.split(r',\s*(?![^()]*\))', ingredient_stmt)
            for ingredient in ingredients:
                # If an ingredient doesn't exist, create a dict with keys as ingredients and flavors appended to them
                if ingredient not in ingredients_kv:
                    ingredients_kv[ingredient] = [juice['item_name']]
                else:
                    ingredients_kv[ingredient].append(juice['item_name'])

    # Create CSV with that ingredient information
    with open('templates/ingredients.csv', 'w') as f:
        for key in ingredients_kv.keys():
            f.write("\"%s\",\"%s\"\n"%(key,ingredients_kv[key]))

    return render_template('nutrition.json'), 201, {'Content-Type': 'application/json'}