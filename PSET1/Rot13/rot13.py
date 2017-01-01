import os

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

class MainPage(Handler):
	def get(self):
		self.render("index.html", text = "")

	def post(self):
		text = self.request.get("text", "")
		self.render("index.html", text = self.rot13(text))

	def rot13(self, text=""):

		ans = ""
		if text:
			for c in text:
				if c.isalpha():
					newC = ord(c) + 13
					if ( c.islower() and newC > ord('z') ):
						newC = newC - ord('z') + ord('a') - 1
					elif ( c.isupper() and newC > ord('Z') ):
						newC = newC - ord('Z') + ord('A') - 1
					ans += chr(newC)
				else:
					ans += c

		return ans

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ], debug=True)
