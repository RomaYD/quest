import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Base import Group, Base, Station, User, Settings

engine = create_engine('sqlite:///kvestinfa.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
# from pymongo import MongoClient

# db = MongoClient()['am-cp']
# id": 19,
#       "name": "Архив",
#       "geo": "280 аудитория",
#       "reward": 130,
#       "group": 0

with open('db.json', 'r', encoding='UTF-8') as file:
    stations_json = json.load(file)
    for i in stations_json['stations']:
        stations = Station(id=i['id'], name=i['name'], geo=i['geo'], reward=i['reward'], group=i['group'])
        session.add(stations)
        session.commit()
    session.close()
