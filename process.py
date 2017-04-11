import csv
from pymongo import MongoClient

connection = MongoClient()
db= connection.weibo
collection = db.users

usersfile = open("users.csv","w")
relationfile = open("relation.csv","w")
user_writer = csv.writer(usersfile)
user_writer.writerow(('id', 'location', 'nike', 'layer', 'gender'))
relation_writer = csv.writer(relationfile)
relation_writer.writerow(('from','to'))
for user in collection.find({}):
    user_writer.writerow((user['_id'], user.get('location',''), user.get('nike',''), user.get('layer',''), user.get('gender','')))
    for id in user.get('following'):
        relation_writer.writerow((user['_id'],id))
usersfile.close()
relationfile.close()