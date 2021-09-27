from datetime import datetime, timedelta
from flask import Flask, request, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import json
import uuid

import os
basedir = os.path.abspath(os.path.dirname(__file__))



app = Flask(__name__)
ALLOWED_EXTENSIONS = ['json']
N_RECORDS = 10
app.config['SECRET_KEY'] = 'simplesecret1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, './dbTest.db')
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(80))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    user_role = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    expired_at = db.Column(db.DateTime)
    admin = db.Column(db.Boolean, default=False)


def complete_data(in_data, parameters):
    for field in parameters:
        if not in_data.get(field):
            return False
    return True


@app.route('/user', methods=['GET'])
def get_all_users():
    users = User.query.all()
    output = []
    for user in users:
        user_data = {}
        user_data['id'] = user.id
        user_data['public_id'] = user.public_id
        user_data['first_name'] = user.first_name
        user_data['last_name'] = user.last_name
        user_data['email'] = user.email
        user_data['password'] = user.password
        user_data['user_role'] = user.user_role
        user_data['created_at'] = user.created_at
        user_data['updated_at'] = user.updated_at
        user_data['expired_at'] = user.expired_at
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify(dict(users=output))


@app.route('/user/<public_id>', methods=['GET'])
def get_one_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'No user found!'})

    user_data = {}
    user_data['id'] = user.id
    user_data['public_id'] = user.public_id
    user_data['first_name'] = user.first_name
    user_data['last_name'] = user.last_name
    user_data['email'] = user.email
    user_data['password'] = user.password
    user_data['user_role'] = user.user_role
    user_data['created_at'] = user.created_at
    user_data['updated_at'] = user.updated_at
    user_data['expired_at'] = user.expired_at
    user_data['admin'] = user.admin
    return jsonify({'user': user_data})


@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json(force=True)
    if not complete_data(data, ['first_name', 'last_name', 'email', 'password']):
        return jsonify(dict(message='Incorrect input data!'))
    hashed_password = generate_password_hash(data['password'], method='sha256')
    expired_date = datetime.now() + timedelta(days=30)
    new_user = User(public_id=str(uuid.uuid4()),
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data['email'],
                    password=hashed_password,
                    expired_at=expired_date)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(dict(message='New user CREATED.'))


@app.route('/update_user/<public_id>', methods=['PUT'])
def update_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'User not found!'})

    data = request.get_json(force=True)
    if not complete_data(data, ['first_name', 'last_name', 'email']):
        return jsonify(dict(message='Incorrect input data!'))

    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.email = data['email']
    db.session.commit()
    return jsonify({'message': 'User has been UPDATED'})



@app.route('/update_password/<public_id>', methods=['PUT'])
def update_password(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'User not found!'})

    data = request.get_json(force=True)
    if not complete_data(data, ['password']):
        return jsonify(dict(message='Incorrect input data!'))

    new_hashed_password = generate_password_hash(data['password'], method='sha256')
    user.password = new_hashed_password
    db.session.commit()
    return jsonify({'message': 'User password has been UPDATED'})


# UPDATE set_admin role
@app.route('/set_admin/<public_id>', methods=['PUT'])
def set_admin_role(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'User not found!'})

    user.admin = True
    db.session.commit()
    return jsonify({'message': 'Admin role updated'})


@app.route('/user/<public_id>', methods=['DELETE'])
def delete_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'User not found!'})

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User has been DELETED'})


# file update

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/file_import', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return jsonify({'message': 'No file part'})

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return jsonify({'message': 'No selected file'})

        if file and allowed_file(file.filename):
            data_dict = json.loads(file.read())
            print("data_dict:")
            print(data_dict)
            users_list = data_dict['users']
            bulk_insert = []
            if len(users_list) > N_RECORDS:
                return jsonify({'message': 'Too many records for insert!'})
            for user_in in users_list:
                hashed_password = generate_password_hash(user_in['password'], method='sha256')
                expired_date = datetime.now() + timedelta(days=30)
                user_in['public_id'] = str(uuid.uuid4())
                user_in['password'] = hashed_password
                user_in['expire_at'] = expired_date
                bulk_insert.append(user_in)
            db.session.bulk_update_mappings(User, bulk_insert)
            db.session.commit()
            # FIX NEED

            return "File UPLOADED !"

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
