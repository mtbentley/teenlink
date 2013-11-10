import webapp2
from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio.util import RequestValidator
from google.appengine.ext import db
from google.appengine.api import users
import logging
 
from private import account_sid, auth_token, ADMIN

class Call(db.Model):
    calls = db.StringListProperty()
    
def add_header(self):
    self.response.write("Welcome " + str(users.get_current_user()) + "<br />")
    self.response.write("<a href='/index'>Home</a>")
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

class StartHere(webapp2.RequestHandler):
    def get(self):
        validator = RequestValidator(auth_token)
        url = self.request.url
        params = {}
        try:
            twilio_signature = self.request.headers["X-Twilio-Signature"]
        except:
            twilio_signature = ""
        r = twiml.Response()
        if not validator.validate(url, params, twilio_signature):
            r.record(maxLength="45", action="/handle-recording?call_id=%s" % (self.request.get('call_id')), method="GET")
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.write(str(r))
        
class HandleRecording(webapp2.RedirectHandler):
    def get(self):
        client = TwilioRestClient(account_sid, auth_token)
        validator = RequestValidator(auth_token)
        url = self.request.url
        params = {}
        try:
            twilio_signature = self.request.headers["X-Twilio-Signature"]
        except:
            twilio_signature = ""
        if validator.validate(url, params, twilio_signature):
            info = Call.all()
            info.order('-__key__')
            info = info.run().next().calls
            for i in info:
                call = client.calls.create(to=i, from_="2065576875",
                                           url="https://teen-link.appspot.com/make-calls?RecordingUrl=" + self.request.get("RecordingUrl"),
                                           method="GET",
                                           if_machine='Continue',
                                           status_callback="https://teen-link.appspot.com/debug",
                                           status_callback_method="GET")
        else:
            self.response.headers['Content-Type'] = 'text/html'
            self.response.write("Please don't try to hack me.")

class MakeCalls(webapp2.RedirectHandler):
    def get(self):
        validator = RequestValidator(auth_token)
        url = self.request.url
        params = {}
        try:
            twilio_signature = self.request.headers["X-Twilio-Signature"]
        except:
            twilio_signature = ""
        if validator.validate(url, params, twilio_signature):
            r = twiml.Response()
            r.play(self.request.get("RecordingUrl"))
            r.play(self.request.get("RecordingUrl"))
            self.response.headers['Content-Type'] = 'text/xml'
            self.response.write(str(r))
        else:
            self.response.headers['Content-Type'] = 'text/html'
            self.response.write("Please don't try to hack me.")
            
class Debug(webapp2.RedirectHandler):
    def get(self):
        for i in self.request.headers:
            logging.debug("headers: " + i + ": " + self.request.headers[i])
        logging.debug("get: " + self.request.query_string)
        
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write('<html><body>')
        add_header(self)
        pages={"Add User":"/users/manage", "List and Edit Users":"/users/list", "Make New Call":"/action/newcall"}
        for i in pages:
            self.response.write("<h2><a href='%s'>%s</a></h2>" % (pages[i], i))
        self.response.write("</body></html>")
            

app = webapp2.WSGIApplication([
                               ('/twiml', StartHere),
                               ('/handle-recording', HandleRecording),
                               ('/make-calls', MakeCalls),
                               ('/debug', Debug),
                               ('/index', MainPage),
                               ('/', MainPage)],
                              debug=True)