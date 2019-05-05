from flask import Flask, request, flash, redirect, url_for
from flask import render_template
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from pymongo import MongoClient, errors
import random
import string
import datetime
import os
import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)


DEBUG = False  # False is for production
try:
    m = os.environ['MONGO_URL']
    logging.info(m)
    gym_users_collection = MongoClient(os.environ.get('MONGO_URL')).gym.users
    gym_classes_collection = MongoClient(
        os.environ.get('MONGO_URL')).gym.reservations
except:
    logging.info('MONGO_URL env variable does not exist!')
    from credentials import MONGO_URL
    gym_users_collection = MongoClient(MONGO_URL).gym.users
    gym_classes_collection = MongoClient(MONGO_URL).gym.reservations
    


class RegistrationForm(Form):
    name = StringField('First Name', [validators.Length(min=4, max=25)])
    membership_id = StringField(
        'Membership Number', [validators.Length(min=9, max=9)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    birthday = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST':
        bd = form.birthday.data.split('/')
        password = bd[0] + bd[1] + bd[2][-2:]
        user = {
            '_id': form.membership_id.data,
            'name': form.name.data,
            'email': form.email.data,
            'password': password
        }
        try:
            gym_users_collection.insert_one(user)
            flash('Thanks for registering')
        except errors.DuplicateKeyError:
            flash('User already exists...')
            flash('Updating info')
            gym_users_collection.update(
                {'_id': user['_id']},
                {'$set': {
                    'name': form.name.data,
                    'email': form.email.data,
                    'password': form.password.data
                }}
            )

        return redirect(url_for('booking', membership_id=form.membership_id.data))
    return render_template('register.html', form=form)

@app.route('/test')
def test():
    return render_template('index.html', test='Test ID is 123123123')

@app.route('/booking/', methods=['GET', 'POST'])
@app.route('/booking/<membership_id>', methods=['GET', 'POST'])
def booking(membership_id=None):
    if request.method == 'POST':
        membership_id = request.form.get('membership_id')
        gym_class_id = request.form.get('gym_class_id')
        if not gym_class_id:
            return redirect(url_for('booking', membership_id=membership_id))
        gym_class = gym_classes_collection.find_one({'_id': gym_class_id})
        register_members = gym_class.get('register_members', [])
        if len(register_members):
            if membership_id in register_members:
                gym_classes_collection.update(
                    {'_id': gym_class_id},
                    {'$pull': {'register_members': membership_id}})
            else:
                gym_classes_collection.update(
                    {'_id': gym_class_id},
                    {'$push': {'register_members': membership_id}})
        else:
            gym_classes_collection.update(
                {'_id': gym_class_id},
                {'$set': {'register_members': [membership_id]}})
        return redirect(url_for('booking', membership_id=membership_id))
    if not membership_id:
        return render_template('index.html', error='Missing membership ID.')
    elif len(membership_id) != 9:
        return render_template('index.html', error='Membership ID is 9 numbers.')
    elif not list(gym_users_collection.find({'_id': membership_id})):
        return render_template('index.html', error='Membership ID not registered. Please register first.')

    gym_classes = gym_classes_collection.find({
        'start_time': {'$gte': datetime.datetime.now()},
    },
        {
        '_id': 1,
        'class_name': 1,
        'capacity_free': 1,
        'start_time': 1,
        'register_members_done': 1,
        'register_members': 1,
    })
    gym_classes = list(gym_classes)
    gym_classes = sorted(gym_classes, key=lambda k: k['start_time'])
    gym_classes_by_day = []
    one_day = []
    for i in range(len(gym_classes)):
        gym_class = gym_classes[i]
        gym_class['register_members_done'] = True if membership_id in gym_class.get(
            'register_members_done', []) else ''
        gym_class['register_members'] = True if membership_id in gym_class.get(
            'register_members', []) else ''
        start_time = gym_class['start_time']
        gym_class['time'] = start_time.strftime("%H:%M")
        gym_class['date'] = start_time.strftime("%A %-dth of %b")
        del gym_class['start_time']
        if one_day:
            if gym_class['date'] == one_day[0]['date']:
                one_day.append(gym_class)
            else:
                gym_classes_by_day.append(one_day)
                one_day = [gym_class]
        else:
            one_day = [gym_class]
    gym_classes_by_day.append(one_day)
    return render_template(
        'booking.html',
        gym_classes_by_day=gym_classes_by_day,
        membership_id=membership_id,)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=DEBUG)
