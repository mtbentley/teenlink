import webapp2
import cgi
from google.appengine.ext import db
from google.appengine.api import users
from time import sleep

TEMPLATE="""
        <div>Full Name: <input type="text" name="name"/></div>
        <div>Phone Number: <input type="text" name="phone"/></div>
        <div>Phone worker? <input type="checkbox" name="pw" /></div>
        <div>Can text? <input type="checkbox" name="text" /></div>
        <div>PAB member? <input type="checkbox" name="PAB" /></div>
"""

DEFAULT_DB="all_users"
from private import account_sid, auth_token, ADMIN

def add_header(self):
    self.response.write("Welcome " + str(users.get_current_user()) + "<br />")
    if str(users.get_current_user())==ADMIN:
        self.response.write("You're an admin!<br />")
        self.response.write('<a href="%s">%s</a>' % (users.create_logout_url(self.request.uri), 'Logout'))
        self.response.write("<br /><br />")
        return True
    elif users.get_current_user():
        self.response.write("You're not an admin!<br />")
        self.response.write('<a href="%s">%s</a>' % (users.create_logout_url(self.request.uri), 'Logout'))
        self.response.write("<br /><br />")
        return False
    else:
        self.response.write("Please log in.<br />")
        self.response.write('<a href="%s">%s</a>' % (users.create_login_url(self.request.uri), 'Login'))
        self.response.write("<br /><br />")
        return False

class User(db.Model):
    """Model for the user db"""
    fullname = db.StringProperty(indexed=True)
    phone_number = db.StringProperty(indexed=True)
    phone_worker = db.BooleanProperty()
    can_text = db.BooleanProperty()
    PAB = db.BooleanProperty()
    

class Manage(webapp2.RequestHandler):
    """This really is only for adding users...I should rename it"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write("<html><body>")
        can_edit = add_header(self)
        if can_edit:
            self.response.write("<form action='/users/add' method='GET'>")
            self.response.write(TEMPLATE)
            self.response.write("<input type='submit' value='submit' /></form>")
        self.response.write("</body></html>")
            
            
class UserAdd(webapp2.RequestHandler):
    """The backend of adding and modifying users.  You never see this page"""
    def get(self):
        can_edit = add_header(self)
        if can_edit:
            user=User(key_name=cgi.escape(self.request.get("name")))
            user.fullname = cgi.escape(self.request.get("name"))
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
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write('<html><body>')
        can_edit = add_header(self)
        if can_edit:
            self.response.write("<form action='/users/edit' method='GET'>")
        self.response.write("<table border='1'><tr><td>Name</td><td>Phone Number</td><td>Can Text?</td><td>Phone Worker?</td><td>PAB?</td><td>Edit?</td><td>Delete?</td></tr>")
        info = db.GqlQuery("SELECT * FROM User")
        for i in info.run():
            self.response.write("<tr>")
            self.response.write("<td>" + i.fullname + "</td><td>" + i.phone_number + "</td><td>" + str(i.can_text) + "</td><td>" + str(i.phone_worker) + "</td><td>" + str(i.PAB) + "</td><td><input type='checkbox' name='name' value='" + i.fullname + "' /></td><td><input type='checkbox' name='delete' value='" + i.fullname + "' /></td>")
            self.response.write("</tr>")
        self.response.write("</table>")
        if can_edit:
            self.response.write("<input type='submit' value='submit' />")
            self.response.write("</form>")
            self.response.write("<a href='/users/manage'>Add a user</a>")
        self.response.write("</body></html>")
        
class EditUser(webapp2.RequestHandler):
    """This page actually edits users marked in ListUser, and deletes users marked for deletion"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write("<html><body>")
        can_edit = add_header(self)
        if can_edit:
            self.response.write("<form action=/users/add method='GET'>")
            for i in self.request.get_all('delete'):
                user = User(key_name=i)
                user.delete()
            
        if not self.request.get_all('name') or not can_edit:
            sleep(1)
            self.redirect('/users/list')
        if can_edit:
            for i in self.request.get_all('name'):
                info = db.GqlQuery("SELECT * FROM User WHERE fullname=:1", i)
                info = info.run().next()
                self.response.write("<div>Full Name: %s</div>" % (info.fullname))
                self.response.write("<input type='hidden' name='name' value='%s' />" % (info.fullname))
                self.response.write("<div>Phone Number: <input type='text' name='phone' value='%s' /></div>" % (info.phone_number))
                self.response.write("<div>Phone Worker? <input type='checkbox' name='pw' %s /></div>" % (("checked='yes'" if (info.phone_worker) else "")))
                self.response.write("<div>Can Text? <input type='checkbox' name='text' %s /></div>" % (("checked='yes'" if (info.can_text) else "")))
                self.response.write("<div>PAB member? <input type='checkbox' name='PAB' %s /></div>" % (("checked='yes'" if (info.PAB) else "")))
                self.response.write("<br />")
            self.response.write("<input type='submit' value='update' />")
            self.response.write("</form>")
        self.response.write("</body></html>")


app = webapp2.WSGIApplication([
                               ('/users/manage', Manage),
                               ('/users/add', UserAdd),
                               ('/users/list', ListUser),
                               ('/users/edit', EditUser)],
                              debug=True)