from dotenv import load_dotenv
import os
import certifi
from flask import Flask, request, render_template
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
load_dotenv()

app = Flask(__name__)


MONGO_URI = os.environ.get('MONGO_URI')


client = MongoClient(MONGO_URI,
                     tls=True,
                     tlsCAFile=certifi.where())
db = client['microcluster']
collection = db['registrations']

collection.create_index([('email', 1), ('event', 1)], unique=True)

@app.template_filter('format_time')
def format_time(value):
    if value:
        return value.strftime('%d-%m-%Y %H:%M')
    return ""

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/event')
def event():
    event = request.args.get('event', 'General Event')
    return render_template('register.html', event=event)

@app.route('/register', methods=['POST'])
def register():
    data = request.form
    name = data.get('name')
    email = data.get('email')
    dept = data.get('dept')
    event = data.get('event')

    if not name or not name.strip():
        return render_template('error.html', message='Please enter a name.')
    if not email or "@" not in email:
        return render_template('error.html', message='Please enter a valid email address.')
    if not dept:
        return render_template('error.html', message='Please enter your Department.')

    user = {
        "name": name,
        "email": email,
        "dept": dept,
        "event": event,
        "registered_at": datetime.utcnow()
    }

    try:
        collection.insert_one(user)
        return render_template('success.html', message='Registered successfully.')
    except DuplicateKeyError:
        return render_template('error.html', message='You are already registered.')
    except Exception:
        return render_template('error.html', message='Something went wrong.')

@app.route('/admin')
def admin():
    data = list(collection.find({}, {'_id': 0}).sort("registered_at", -1))
    count = collection.count_documents({})
    return render_template('admin.html', data=data, count=count)

@app.route('/admin/search')
def search():
    return render_template('search.html')

@app.route('/admin/search/event', methods=['POST'])
def search_event():
    event = request.form.get('event')
    dept = request.form.get('dept')

    query = {}

    if dept:
        query['dept'] = dept
    if event:
        query['event'] = event

    data = list(collection.find(query, {'_id':0}).sort("registered_at", -1))
    count = len(data)

    return render_template('admin.html', data=data, count=count)

if __name__ == '__main__':
    app.run(debug=True)




