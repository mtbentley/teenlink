import webapp2
from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio.util import RequestValidator
from google.appengine.ext import ndb
import logging
import json
 
from private import account_sid, auth_token

class Call(ndb.Model):
    calls = ndb.StringProperty(indexed=True)
    
class User(ndb.Model):
    """Model for the user ndb"""
    fullname = ndb.StringProperty(indexed=True)
    phone_number = ndb.StringProperty(indexed=True)
    phone_worker = ndb.BooleanProperty()
    can_text = ndb.BooleanProperty()
    PAB = ndb.BooleanProperty()
    
class Group(ndb.Model):
    """Model for groups ndb"""
    groupname = ndb.StringProperty(indexed=True)

    
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
        if validator.validate(url, params, twilio_signature):
            logging.debug(self.request.get('to_call'))
            r.record(action="/handle-recording?to_call=%s" % (self.request.get('to_call')), method="GET")
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
            logging.debug(twilio_signature)
        except:
            twilio_signature = ""
        if validator.validate(url, params, twilio_signature) or 1==1:
            logging.debug("Validated")
            call_id = self.request.get('to_call')
            print call_id
            infos = Call.query(Call.key==ndb.Key(Call, int(call_id))).fetch()
            print infos
            for info in infos:
                print info
                for i in json.loads(info.calls):
                    print i
                    call_out = client.calls.create(to=i, from_="2065576875",
                                url="https://teen-link.appspot.com/make-calls?RecordingUrl=" + self.request.get("RecordingUrl"),
                                method="GET")
                    print call_out
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
        
class Test(webapp2.RequestHandler):
    def get(self):
#        if self.request.get('group'):
#            group=Group(key_name=self.request.get('group'))
#            group.groupname = self.request.get('group')
#            group.put()
        if self.request.get('user') and self.request.get('group'):
#            print self.request.get('user')
#            print self.request.get('group')
            info = ndb.gql("SELECT * FROM User WHERE fullname=:1", self.request.get('user'))
            group=Group(parent=info.next().key())
            group.groupname = self.request.get('group')
            group.put()
#            info = ndb.GqlQuery("SELECT * FROM Group WHERE groupname=:1", self.request.get('group'))
#            print info.next().parent().fullname
#            print info.next()
#            info = ndb.GqlQuery("SELECT * FROM User WHERE fullname=:1", self.request.get('user'))
#            key = info.next()
#            infog = Group.all().next().parent()
#            info = User.all().filter("fullname ==", self.request.get('user'))
#            info2 = info
#            print infog.fullname
#            print dir(infog.ancestor(key).next())
            

app = webapp2.WSGIApplication([
                               ('/twiml', StartHere),
                               ('/handle-recording', HandleRecording),
                               ('/make-calls', MakeCalls),
                               ('/index', MainPage),
                               ('/', MainPage),
                               ('/test', Test)],
                              debug=True)