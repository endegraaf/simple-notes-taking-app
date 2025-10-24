from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

import uuid

app = Flask(__name__)
DATA_FILE = 'people_data.json'


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"people": []}


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def calculate_dob(age):
    try:
        age = int(age)
        today = datetime.today()
        dob = today.replace(year=today.year - age)
        return dob.strftime('%Y-%m-%d')
    except:
        return ""


@app.route('/')
def index():
    data = load_data()
    people = data['people']
    today = datetime.today().strftime('%Y-%m-%d')

    # Get filters from query parameters
    selected_like = request.args.get("like", "").lower()
    name_query = request.args.get("name", "").lower()

    # Apply filters
    if selected_like:
        people = [p for p in people if selected_like in [l.lower() for l in p.get("likes", [])]]
    if name_query:
        people = [p for p in people if name_query in p.get("name", "").lower()]

    # Extract likes for dropdown
    all_likes = set()
    for person in people:
        all_likes.update(person.get("likes", []))
    likes_filter = sorted(all_likes)

    view_mode = request.args.get("view", "cards")  # default to cards

    # Pagination
    page = int(request.args.get("page", 1))
    per_page = 10
    total = len(people)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_people = people[start:end]

    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page

    return render_template("index.html", people=paginated_people, likes_filter=likes_filter, today=today,
                           view_mode=view_mode, page=page, total_pages=total_pages)


@app.route('/add', methods=['GET', 'POST'])
def add_person():
    if request.method == 'POST':
        data = load_data()

        new_person = {
            "id": str(uuid.uuid4()),  # ✅ Generate a unique ID
            "name": request.form.get('name', ''),
            "age": int(request.form.get('age', 0)),
            "dob": request.form.get('dob', ''),
            "location": request.form.get('location', ''),
            "school": request.form.get('school', ''),
            "likes": [like.strip() for like in request.form.get('likes', '').split(',') if like.strip()],
            "notes": [note.strip() for note in request.form.get('notes', '').split(',') if note.strip()],
            "children": []
        }

        # Handle children if provided
        child_names = request.form.getlist('child_name')
        child_ages = request.form.getlist('child_age')
        for cname, cage in zip(child_names, child_ages):
            if cname.strip():
                try:
                    age = int(cage)
                except ValueError:
                    age = 0
                new_person["children"].append({"name": cname.strip(), "age": age})

        data['people'].append(new_person)
        save_data(data)
        return redirect(url_for('index'))

    return render_template('add.html')


@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_person(id):
    data = load_data()
    person = next((p for p in data['people'] if p['id'] == id), None)
    if not person:
        return "Person not found", 404

    if request.method == 'POST':
        #person['id'] = request.form.get('id', '')
        person['name'] = request.form.get('name', '')
        person['location'] = request.form.get('location', '')
        person['school'] = request.form.get('school', '')
        person['likes'] = [like.strip() for like in request.form.get('likes', '').split(',') if like.strip()]
        person['notes'] = [note.strip() for note in request.form.get('notes', '').split(',') if note.strip()]
        age = request.form.get('age', '')
        person['age'] = int(age) if age.isdigit() else None
        person['dob'] = calculate_dob(age)

        child_names = request.form.getlist('child_name')
        child_ages = request.form.getlist('child_age')
        children = []
        for cname, cage in zip(child_names, child_ages):
            if cname.strip():
                try:
                    age = int(cage)
                except ValueError:
                    age = 0
                children.append({"name": cname.strip(), "age": age})
        person['children'] = children

        save_data(data)
        return redirect(url_for('index'))

    return render_template('edit.html', person=person)


@app.route('/delete/<id>', methods=['POST'])
def delete_person(id):
    data = load_data()
    data['people'] = [p for p in data['people'] if p['id'] != id]
    save_data(data)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
