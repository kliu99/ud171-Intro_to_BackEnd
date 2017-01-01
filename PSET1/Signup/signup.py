import os
import re

import jinja2
import webapp2


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

	def verify_username(self, username):
		if username:
			return re.match("^[a-zA-Z0-9_-]{3,20}$", username)
		return False

	def verify_password(self, password):
		if password:
			return re.match("^.{3,20}$", password)
		return False

	def verify_verify(self, password, verify):
		if password and verify:
			return password == verify
		return False

	def verify_email(self, email):
		if len(email) == 0:
			return True
		return re.match("^[\S]+@[\S]+.[\S]+$", email)


class MainPage(Handler):
	def get(self):
		self.render("index.html", 
			username = "",
			password = "",
			verify = "",
			email = "",
			error_username = "",
			error_password = "",
			error_verify = "")

	def post(self):
		username = self.request.get("username", "")
		password = self.request.get("password", "")
		verify = self.request.get("verify", "")
		email = self.request.get("email", "")

		error_username = ""
		error_password = ""	
		error_verify = ""
		error_email = ""

		valid_username = self.verify_username(username)
		valid_password = self.verify_password(password)
		valid_verify = self.verify_verify(password, verify)
		valid_email = self.verify_email(email)

		if not valid_username:
			error_username = "That's not a username."

		if not valid_password:
			error_password = "That's not a password"
			password = ""
			verify = ""

		if not valid_verify:
			error_verify = "That's not a match"
			password = ""
			verify = ""

		if not valid_email:
			error_email = "That's not a email"

		if valid_username and valid_password and valid_verify and valid_email:
			self.redirect("/welcome?username=" + username)
			# self.render("welcome.html", 
			# 	username = username)
		else:
			self.render("index.html",
				username = username,
				password = password,
				verify = verify,
				email = email,
				error_username = error_username,
				error_password = error_password,
				error_verify = error_verify,
				error_email = error_email)


class WelcomePage(Handler):
	def get(self):
		username = self.request.get("username")
		if self.verify_username(username):
			self.render("welcome.html", username = username)
		else:
			self.redirect('/')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/welcome', WelcomePage)
    ], debug=True)
