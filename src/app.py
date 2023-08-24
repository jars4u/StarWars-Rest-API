"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Fav_people, Fav_planet
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# GET ALL PEOPLE
@app.route('/people')
def get_people():
    all_people = People.query.all()
    return jsonify(list(map(lambda item: item.serialize(), all_people))), 200


# GET ONE PEOPLE'S INFO
@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_people(people_id = None):

    one_people = People.query.filter_by(id = people_id).one_or_none()
    
    if one_people is None:
        return jsonify({"message": "PEOPLE DOESN'T EXIST"}), 400
    return jsonify(one_people.serialize()), 200


#ADD PEOPLE
@app.route('/people', methods=['POST'])
def add_people():

    data = request.json

    if data is None or data is {}:
        return jsonify({"message": "there's no data"}), 400
    
    people = People()
    people.name = data.get('name', None)
    people.gender = data.get('gender', None)
    people.birth_year = data.get('birth_year', None)

    db.session.add(people)

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return jsonify({'message': err.args}), 500    
    return jsonify({"message" : "PEOPLE ADDED"}), 200  



# GET ALL PLANET
@app.route('/planet')
def get_planet():
    all_planet = Planet.query.all()
    return jsonify(list(map(lambda item: item.serialize(), all_planet))), 200


# GET ONE PLANET'S INFO
@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_one_planet(planet_id = None):

    one_planet = Planet.query.filter_by(id = planet_id).one_or_none()
    
    if one_planet is None:
        return jsonify({"message": "PLANET DOESN'T EXIST"}), 400
    return jsonify(one_planet.serialize()), 200


#ADD PLANET
@app.route('/planet', methods=['POST'])
def add_planet():

    data = request.json

    if data is None or data is {}:
        return jsonify({"message": "there's no data"}), 400
    
    planet = Planet()
    planet.name = data.get('name', None)
    planet.population = data.get('population', None)
    planet.terrain = data.get('terrain', None)

    db.session.add(planet)

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return jsonify({'message': err.args}), 500    
    return jsonify({"message" : "PLANET ADDED"}), 200 



# la única forma de crear usuarios es directamente en la base de datos usando el admin.
# GET USERS
@app.route('/user', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(list(map(lambda item: item.serialize(), users))), 200


# GET ALL FAVORITES FROM A USER
@app.route('/user/<int:user_id>/favorites', methods=['GET'])
def get_favorites(user_id = None):

    fav_people = Fav_people.query.filter_by(user_id = user_id)
    fav_planet = Fav_planet.query.filter_by(user_id = user_id)
    fav = list(map(lambda item: item.serialize(), fav_people))
    fav.append(list(map(lambda item: item.serialize(), fav_planet)))
    return jsonify(fav), 200


# USER'S FAVORITE PEOPLE
@app.route('/user/<int:user_id>/favorites/people/<int:people_id>', methods=['POST'])
def fav_people(user_id = None, people_id = None):

    user = User.query.filter_by(id = user_id).one_or_none()
    if user is None:
        return jsonify({"message" : "USER DOESN'T EXIST"}), 400
    
    add_people = People.query.filter_by(id = people_id).one_or_none()
    if add_people is None:
        return jsonify({"message" : "PEOPLE DOESN'T EXIST"}), 400
    
    fav = Fav_people()
    fav.user_id = user.id
    fav.people_id = add_people.id

    db.session.add(fav)

    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({'message' : error.args}), 500
    return jsonify({'message' : 'People add to favorites'}), 200





# USER'S FAVORITE PLANET
@app.route('/user/<int:user_id>/favorites/planet/<int:planet_id>', methods=['POST'])
def fav_planet(user_id = None, planet_id = None):

    user = User.query.filter_by(id = user_id).one_or_none()
    if user is None:
        return jsonify({"message" : "USER DOESN'T EXIST"}), 400
    
    add_planet = Planet.query.filter_by(id = planet_id).one_or_none()
    if add_planet is None:
        return jsonify({"message" : "PLANET DOESN'T EXIST"}), 400
    
    fav = Fav_planet()
    fav.user_id = user.id
    fav.planet_id = add_planet.id

    db.session.add(fav)

    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({'message' : error.args}), 500
    return jsonify({'message' : 'Planet add to favorites'}), 200



# DELETE PEOPLE FROM FAVORITES
@app.route('/user/<int:user_id>/favorites/people/<int:people_id>', methods=['DELETE'])
def delete_people(user_id = None, people_id = None):

    del_people = Fav_people.query.filter_by(user_id=user_id, people_id=people_id).first()
    if del_people is None:
        return jsonify({'message': 'PEOPLE NOT FOUND'}), 400

    db.session.delete(del_people)

    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({'message': error.args}), 500
    return jsonify({'message': 'PEOPLE DELETED FROM FAVORITES'}), 200


# DELETE PLANET FROM FAVORITES
@app.route('/user/<int:user_id>/favorites/planet/<int:planet_id>', methods=['DELETE'])
def delete_planet(user_id = None, planet_id = None):

    del_planet = Fav_planet.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if del_planet is None:
        return jsonify({'message': 'PLANET NOT FOUND'}), 400

    db.session.delete(del_planet)

    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({'message': error.args}), 500
    return jsonify({'message': 'PLANET DELETED FROM FAVORITES'}), 200










# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
