import webapp2
import jinja2
import cgi
import os
from google.appengine.ext import ndb
from time import sleep
from common import add_header
from common import make_template

class User(ndb.Model):
    """Model for the user db"""
    fullname = ndb.StringProperty(indexed=True)
    phone_number = ndb.StringProperty(indexed=True)
    phone_worker = ndb.BooleanProperty()
    can_text = ndb.BooleanProperty()
    PAB = ndb.BooleanProperty()
    
class Group(ndb.Model):
    """Model for groups db"""
    groupname = ndb.StringProperty(indexed=True)
    

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Manage(webapp2.RequestHandler):
    """This really is only for adding users...I should rename it"""
    def get(self):
        template_values = make_template(self)
        
        template = JINJA_ENVIRONMENT.get_template('manage.jinja')
        self.response.write(template.render(template_values))
            
class UserAdd(webapp2.RequestHandler):
    """The backend of adding and modifying users.  You never see this page"""
    def get(self):
        can_edit = add_header(self)
        if can_edit:
            if not self.request.get('id'):
                user=User()
                user.fullname = cgi.escape(self.request.get("name"))
            if self.request.get('id'):
                user_key = ndb.Key(User, int(self.request.get('id')))
                user = user_key.get()
            user.phone_number = cgi.escape(self.request.get("phone"))
            user.phone_worker = (self.request.get("pw") == "on")
            user.can_text = (self.request.get("text") == "on")
            user.PAB = (self.request.get("PAB") == "on")
            user.put()
        sleep(1)
        self.redirect('/users/list')
        
class ListUser(webapp2.RequestHandler):
    """Lists all users, with option to edit or delete each one"""
    def get(self):
        template_values = make_template(self)
        info = ndb.gql("SELECT * FROM User")
        user_list = []
        for i in info:
            to_append = {}
            to_append['fullname'] = i.fullname
            to_append['phone_number'] = i.phone_number
            to_append['can_text'] = i.can_text
            to_append['phone_worker'] = i.phone_worker
            to_append['pab'] = i.PAB
            to_append['id'] = str(i.key.id())
            user_list.append(to_append)
        template_values['user_list'] = user_list
        
        template = JINJA_ENVIRONMENT.get_template('list.jinja')
        self.response.write(template.render(template_values))
        
class EditUser(webapp2.RequestHandler):
    """This page actually edits users marked in ListUser, and deletes users marked for deletion"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write("<html><body>")
        can_edit = add_header(self)
        if can_edit:
            self.response.write("<form action=/users/add method='GET'>")
            for i in self.request.get_all('delete'):
                user_key = ndb.Key(User, int(i))
                user = user_key.get()
                user.key.delete()
            
        if not self.request.get_all('id') or not can_edit:
            sleep(1)
            self.redirect('/users/list')
        if can_edit:
            for i in self.request.get_all('id'):
                user_key = ndb.Key(User, int(i))
                user = user_key.get()
                print user
                self.response.write("<div>Full Name: %s</div>" % (user.fullname))
                self.response.write("<input type='hidden' name='id' value='%s' />" % (i))
                self.response.write("<div>Phone Number: <input type='text' name='phone' value='%s' /></div>" % (user.phone_number))
                self.response.write("<div>Phone Worker? <input type='checkbox' name='pw' %s /></div>" % (("checked='yes'" if (user.phone_worker) else "")))
                self.response.write("<div>Can Text? <input type='checkbox' name='text' %s /></div>" % (("checked='yes'" if (user.can_text) else "")))
                self.response.write("<div>PAB member? <input type='checkbox' name='PAB' %s /></div>" % (("checked='yes'" if (user.PAB) else "")))
                self.response.write("<br />")
                break
            self.response.write("<input type='submit' value='update' />")
            self.response.write("</form>")
        self.response.write("</body></html>")


app = webapp2.WSGIApplication([
                               ('/users/manage', Manage),
                               ('/users/add', UserAdd),
                               ('/users/list', ListUser),
                               ('/users/edit', EditUser)],
                              debug=True)