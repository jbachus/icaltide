import requests
import arrow
import json
import os
from flask import Flask, make_response, redirect
from flask_caching import Cache
from ics import Calendar, Event
from timezonefinder import TimezoneFinder

required_vars = ('API_KEY')
if not all(key in os.environ for key in required_vars):
    print("API_KEY is required")
    sys.exit(os.EX_CONFIG)

url = "https://tides.p.rapidapi.com/tides"
headers = {
    'x-rapidapi-key': os.environ.get("API_KEY"),
    'x-rapidapi-host': "tides.p.rapidapi.com"
    }

cache = Cache(config={"CACHE_TYPE": "simple"})
app = Flask(__name__)
cache.init_app(app)

with app.app_context():
  bad_resp = make_response("Invalid Input", 404)
  bad_resp.headers["Cache-Control"] = "public, max-age=15552000"

@app.route('/<lat>/<lon>', methods=['GET'])
@cache.cached(timeout=15552000)
def build_ical(lat, lon):
  try:
    latitude = float(lat)
    longitude = float(lon)

    if latitude > 90.0 or latitude < -90.0:
      return bad_resp
    if longitude > 180.0 or longitude < -180.0:
      return bad_resp
  except:
    return bad_resp
  
  if lat == '{:.2f}'.format(latitude) or lon == '{:.2f}'.format(longitude):
    c = Calendar()
    tf = TimezoneFinder()
    lat = float(lat)
    lon = float(lon)
    querystring = {"latitude":str(latitude),"longitude":str(longitude),"interval":"0","duration":"263520"}
    with requests.request("GET", url, headers=headers, params=querystring) as response:
      extremes = json.loads(response.text).get('extremes')

    for extreme in extremes:
      event = Event()
      event.name = "{} ({:.2f}m)".format(extreme.get('state').title(), float(extreme.get('height')))
      event.begin = arrow.get(extreme.get('timestamp')).to(tf.timezone_at(lat=latitude, lng=longitude))
      event.duration = {"minutes": 30}
      c.events.add(event)

    resp = make_response(str(c), 200)
    resp.headers["Content-Type"] = "text/calendar"
    resp.headers["Content-Disposition"] = "attachment;filename=icaltide.ics"
    resp.headers["Cache-Control"] = "public, max-age=15552000"
    return resp
  else:
    resp = redirect("/{:.2f}/{:.2f}".format(float(latitude),float(longitude)))
    resp.headers["Cache-Control"] = "public, max-age:15552000"
    return resp

@app.errorhandler(404)
def not_found(e):
  return bad_resp

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
