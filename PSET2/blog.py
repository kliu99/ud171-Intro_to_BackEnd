import os
import re

import jinja2
import webapp2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
							   autoescape = True)


class Article(db.Model):
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	time = db.DateTimeProperty(auto_now_add = True)

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
		articles = db.GqlQuery("SELECT * FROM Article ORDER BY time DESC LIMIT 10")

		self.render("front.html", articles = articles)


class NewPostPage(Handler):

	def render_form(self, subject="", content="", error=""):
		self.render("newpost.html",
			subject = subject,
			content = content,
			error = error)

	def get(self):
		self.render_form()

	def post(self):
		subject = self.request.get("subject")
		content = self.request.get("content")

		if subject and content:
			article = Article(subject = subject, content = content)
			article.put()

			self.redirect("/%s" % article.key().id())

		else:
			error = "Both subject and content are required"
			self.render_form(subject, content, error)


class BlogPage(Handler):

	def render_content(self, art):
			art._render_text = art.content.replace('\n', '<br>')
			self.render("blog.html", article = art)

	def get(self, blog_id):
		if blog_id:
			blog_id = int(blog_id)
			article = Article.get_by_id(blog_id)
			self.render_content(article)
		else:
			self.write("error")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newpost', NewPostPage),
    (r'/(\d+)', BlogPage)
    ], debug=True)
