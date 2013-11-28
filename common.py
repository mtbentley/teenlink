from google.appengine.api import users
from private import ADMIN

def add_header(self):
    self.response.write("Welcome " + str(users.get_current_user()) + "<br />")
    self.response.write("<a href='/index'>Home</a><br />")
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
    
def make_template(self):
    if ADMIN.upper()==str(users.get_current_user()).upper():
        is_admin=True
    else:
        is_admin=False
    template_values = {
                       'user':str(users.get_current_user()),
                       'admin':is_admin,
                       'link_url':(users.create_logout_url(self.request.uri) if users.get_current_user() else users.create_login_url(self.request.uri)),
                       'link_text':("Logout" if users.get_current_user() else "Login")
                       }
    return template_values