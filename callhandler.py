import webapp2
from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio.util import RequestValidator
from google.appengine.ext import db
import logging
 
from private import account_sid, auth_token

class Call(db.Model):
    calls = db.StringListProperty()
    
from common import add_header

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
        if not validator.validate(url, params, twilio_signature) or 1==1:
            r.record(action="/handle-recording?call_id=%s" % (self.request.get('call_id')), method="GET")
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
                                           method="GET")
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
            self.response.headers['Content-Type'] = 'text/xml'
            self.response.write(str(r))
        else:
            self.response.headers['Content-Type'] = 'text/html'
            self.response.write("Please don't try to hack me.")
        
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
                               ('/index', MainPage),
                               ('/', MainPage)],
                              debug=True)