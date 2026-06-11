"""餐廳搜尋"""

import requests
from operator import itemgetter
import googlemaps

from config import GMAP_API_KEY


def find_nearby_restaurants(place_name: str):
    """搜尋附近餐廳，回傳 flex message content"""
    gmaps = googlemaps.Client(key=GMAP_API_KEY)

    geocode_result = gmaps.geocode(place_name, language='zh-TW')
    if not geocode_result:
        return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": f"找不到'{place_name}'地點"}
        ]}}

    location = geocode_result[0]['geometry']['location']
    lat, lng = location['lat'], location['lng']

    places_result = gmaps.places_nearby(location=(lat, lng), radius=1000, type='restaurant', language='zh-TW')

    if not places_result['results']:
        return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": f"'{place_name}'地點附近找不到餐廳"}
        ]}}

    restaurants = places_result['results']
    sorted_restaurants = sorted(restaurants, key=itemgetter('rating'), reverse=True)
    top_restaurants = sorted_restaurants[:5]

    ranked_restaurants = []
    short_links = []
    for restaurant in top_restaurants:
        name = restaurant.get('name')
        rating = restaurant.get('rating', 'N/A')
        address = restaurant.get('vicinity', 'N/A')
        place_id = restaurant.get('place_id')
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={place_id}"
        short_links.append(requests.get("https://tinyurl.com/api-create.php?url=" + google_maps_url).text)
        ranked_restaurants.append(f"{name} (評分: {rating}) - {address}\n")

    bubbles = []
    for i in range(len(ranked_restaurants)):
        bubbles.append({
            "type": "bubble", "size": "micro",
            "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                {"type": "text", "wrap": True, "weight": "bold", "size": "sm", "text": ranked_restaurants[i]}
            ]},
            "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                {"type": "button", "style": "primary", "action": {"type": "uri", "label": "前往連結", "uri": short_links[i]}, "height": "sm"}
            ]}
        })

    return {"type": "carousel", "contents": bubbles}
