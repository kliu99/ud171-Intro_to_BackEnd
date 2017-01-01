import os
import re

import jinja2
import webapp2

import hmac
import hashlib
import random
from string import letters

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


SECRET = "rtyubn5678i%^&"

def hash_str(val):
    val = str(val)
    return hmac.new(SECRET, val).hexdigest()

def make_cookie_str(val):
    return "%s|%s" % (val, hash_str(val))

def check_cookie_str(h):
    val = h.split("|")[0]
    if make_cookie_str(val) == h:
        return val


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

    ##
    # Hash cookie with SECRET key 
    def set_cookie(self, name, val):
        val = make_cookie_str(val)
        self.response.headers.add_header('Set-Cookie', str('%s=%s;Path=/' % (name, val)))


class MainPage(Handler):
    def get(self):
        self.write("Hello world!")


class SignUpPage(Handler):
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

            if User.by_name(username):
                error_username = "User already exist"
                self.render("index.html",
                    username = username,
                    password = password,
                    verify = verify,
                    email = email,
                    error_username = error_username,
                    error_password = error_password,
                    error_verify = error_verify,
                    error_email = error_email)
            else:
                # Write to DB
                user = User.sign_up(username, password, email)
                user.put()

                # Add cookie
                self.set_cookie("user_id", user.key().id())

                # Redirect
                self.redirect("/welcome")
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


class LogInPage(Handler):
    def render_login(self, username="", error=""):
        self.render("login.html",
            username = username,
            error = error)

    def get(self):
        self.render_login()

    def post(self):
        input_username = self.request.get("username", "")
        input_password = self.request.get("password", "")

        isValid = False
        if input_username and input_password:
            user = User.by_name(input_username)
            if user:
                password = user.password
                salt = password.split("|")[1]
                input_password_hash = User.hash_password(input_username, input_password, salt)
                if (input_password_hash == password):
                    isValid = True

        # Validate password
        if isValid:
            self.set_cookie("user_id", user.key().id())
            self.redirect("/welcome")
        else:
            error = "Invalid username or password"
            self.render_login(input_username, error)

class LogOutPage(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id;Path=/')
        self.redirect("/signup")

class WelcomePage(Handler):
    def get(self):
        cookie_str = self.request.cookies.get("user_id")
        user_id = check_cookie_str(cookie_str)

        if user_id:
            user = User.by_id(int(user_id))
            if user:
                self.render("welcome.html", username = user.username)
            else:
                self.redirect('/signup')
        else:
            self.redirect('/signup')




class User(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def users_key(cls, group = 'default'):
        return db.Key.from_path('users', group)

    @classmethod
    def make_salt(cls, length = 5):
        return ''.join(random.choice(letters) for x in xrange(length))

    @classmethod
    def hash_password(cls, name, pw, salt=None):
        if not salt:
            salt = User.make_salt()

        pwStr = name + pw + salt
        pwHash = hashlib.sha256(pwStr).hexdigest()
        return "%s|%s" % (pwHash, salt)

    @classmethod
    def valid_password(cls, name, pw, hashStr):
        salt = hashStr.split("|")[1]
        return User.hash_password(name, pw, salt) == hashStr

    @classmethod
    def sign_up(cls, name, pw, email=None):
        pw = User.hash_password(name, pw)
        return User(parent = User.users_key(),
            username = name,
            password = pw,
            email = email)

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = User.users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('username =', name).get()
        return u



app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', SignUpPage),
    ('/login', LogInPage),
    ('/logout', LogOutPage),
    ('/welcome', WelcomePage)
    ], debug=True)
