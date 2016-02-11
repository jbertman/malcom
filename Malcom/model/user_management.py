import dateutil
import threading
import os
import string
import random
import re
import datetime

from pymongo import MongoClient
from pymongo.son_manipulator import SONManipulator
from pymongo.read_preferences import ReadPreference
import pymongo.errors
from passlib.hash import pbkdf2_sha512
from flask.ext.login import make_secure_token

from Malcom.auxiliary.toolbox import debug_output


class UserTransform(SONManipulator):
	def transform_incoming(self, son, collection):
		for (key, value) in son.items():
			if isinstance(value, User):
				son[key] = self.transform_incoming(value, collection)
		return son

	def transform_outgoing(self, son, collection):
		if 'username' in son:
			return User.from_dict(son)
		else:
			return son
		

class UserManager():
	"""Class to manage Malcom users"""
	def __init__(self, setup={}):
		read_pref = {'PRIMARY': ReadPreference.PRIMARY, 'PRIMARY_PREFERRED': ReadPreference.PRIMARY_PREFERRED, 'SECONDARY': ReadPreference.SECONDARY, 'SECONDARY_PREFERRED': ReadPreference.SECONDARY_PREFERRED, 'NEAREST': ReadPreference.NEAREST}
		db_setup = setup.get('DATABASE', {})
		self._connection = MongoClient(host = db_setup.get('HOSTS', 'localhost'), replicaSet = db_setup.get('REPLSET', None), read_preference = read_pref[db_setup.get('READ_PREF', 'PRIMARY')])
		self._db = self._connection[db_setup.get('NAME', 'malcom')]
		if 'USERNAME' in db_setup:
			self._db.authenticate(db_setup['USERNAME'], password = db_setup.get('PASSWORD', None), source = db_setup.get('SOURCE', None))

		self.users = self._db.users
		self.users.ensure_index('username', unique=True)
		
		self.public_api = self._db.public_api

		self._db.add_son_manipulator(UserTransform())

	# ============ User operations =====================

	def get_default_user(self):
		m = self.get_user(username='malcom')
		# we'll run into this case when the database is new or does not contain a malcom user
		if m == None:
			m = self.add_user('malcom', 'malcom')
			m.anonymous = True
			m.authenticated = False
			m.admin = True
			self.save_user(m)

		return m

	def add_user(self, username, password=None, apikey=True):
		u = self.get_user(username=username)
		
		if not u:
			debug_output("User not found, creating...")
			u = User(username)
		
			password = u.reset_password(password)

			if apikey:
				u.generate_api_key()
			u.joined = datetime.datetime.utcnow()
			u.last_activity = None
			u = self.save_user(u)

			debug_output("Account successfully created.\nUsername: %s\nPassword:%s" % (username, password))
			return u
		else:
			return None

	def get_user(self, **kwargs):
		user = self.users.find_one(kwargs)
		if user:
			user = User.from_dict(user)
		else:
			user = None
		return user

	def list_users(self):
		users = list(self.users.find(fields=['username']))
		return users

	def remove_user(self, username):
		self.users.remove({'username': username})

	def reset_password_for_user(self, username, password=None):
		# generate a random password
		if not password:
			password = self.generate_password(length=25)
		pwhash = pbkdf2_sha512.encrypt(password)

		self.users.update({"username":username}, {'$set':{'pwhash': pwhash}})

		return self.get_user(username=username)

	def save_user(self, user):
		d = dict(user)
		if '_id' in d: del d['_id']
		# u = self.users.find_and_modify({'username': user['username']}, {'$set': d}, upsert=True, new=True)
		u = self.users.find_and_modify({'username': user['username']}, d, upsert=True, new=True)
		return User.from_dict(u)

	# ============ Public API operations ===============

	def add_tag_to_key(self, apikey, tag):
		k = self.public_api.find_one({'api_key': apikey})
		if not k:
			k = self.public_api.save({'api_key': apikey, 'available-tags': [tag]})
		else:
			if tag not in k['available-tags']:
				k['available-tags'].append(tag)
				self.public_api.save(k)

	def get_tags_for_key(self, apikey):
		tags = self.public_api.find_one({'api_key': apikey})
		if not tags:
			return []
		else:
			return tags.get('available-tags', [])


class User(dict):

	def __init__(self, username):
		self.username = username
		self.admin = False
		self.joined = None
		self.last_activity = None
		self.api_last_activity = None
		self.api_request_count = 0
		self.sniffer_sessions = {}

		# This is necessary to distinguish between
		# registered users and anonymous users
		#
		# The anonymous user is the 'malcom' user
		# that is only given access when 'auth' is 
		# set to 'false' in the configuration file

		self.authenticated = True
		self.anonymous = False

	def add_sniffer_session(self, session_id):
		self.sniffer_sessions[session_id] = True

	def remove_sniffer_session(self, session_id):
		if session_id in self.sniffer_sessions:
			del self.sniffer_sessions[session_id]

	def check_password(self, password):
		stored_hash = self['pwhash']

		if pbkdf2_sha512.verify(password, stored_hash):
			return True
		else:
			return False

	def reset_password(self, password=None):
		# generate a random password
		if not password:
			password = self.generate_password(length=25)

		self['pwhash'] = pbkdf2_sha512.encrypt(password)
		return password

	@staticmethod
	def generate_password(length=25):
		charset = string.ascii_letters
		random.seed(os.urandom(1024))

		password = ""
		for i in xrange(length):
			password += random.choice(charset)
			if i % 5 == 0 and i > 0:
				password += "-"
		
		return password

	def generate_api_key(self):
		k = os.urandom(32).encode('hex')
		kk = ""
		for i in xrange(32):
			kk += k[i]
			if i % 8 == 0 and i > 0:
				kk += '-'

		self['api_key'] = kk

	def get_auth_token(self):
		if not self.token:
			self.token = make_secure_token(self.username, self.pwhash, os.urandom(1024))
		return self.token

	def is_authenticated(self):
		return self.authenticated

	def is_active(self):
		return True

	def is_anonymous(self):
		return self.anonymous

	def is_admin(self):
		return self.admin

	def get_id(self):
		return unicode(self.username)

	@staticmethod
	def from_dict(d):
		u = User(d['username'])
		for key in d:
			u[key] = d[key]
		return u

	def __unicode__(self):
		return str(self)

	def to_dict(self):
		return self.__dict__

	def __getattr__(self, name):
		return self.get(name, None)

	def __setattr__(self, name, value):
		self[name] = value
