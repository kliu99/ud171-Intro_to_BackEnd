import os
import hashlib
import hmac

import jinja2
import webapp2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
							   autoescape = True)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

SECRET = 'asdl;kja'
class MainPage(Handler):

	def hash_str(self, value):
		return hmac.new(SECRET, value).hexdigest()
		# return hashlib.sha256(value).hexdigest()

	def check_hash_str(self, visits_cookie_str):
		val = visits_cookie_str.split('|')[0]
		if visits_cookie_str == self.make_hash_str(val):
			return val

	def make_hash_str(self, value):
		return "%s|%s" % (value, self.hash_str(value))

	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'

		visits = 0

		visits_cookie_str = self.request.cookies.get('visit')

		if visits_cookie_str:
			cookies_val = self.check_hash_str(visits_cookie_str)
			if cookies_val:
				visits = int(cookies_val)

		visits += 1

		new_cookie_str = self.make_hash_str(str(visits))
		self.response.headers.add_header('Set-Cookie',  'visit=%s' % new_cookie_str)

		if visits > 10:
			self.write("You are the best ever!")
		else:
			self.write("You've been here %s times!" % visits)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ], debug=True)
