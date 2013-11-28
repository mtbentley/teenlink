import webapp2
import jinja2
import os
from google.appengine.ext import ndb
from twilio.rest import TwilioRestClient
from time import time
import json
import logging
from common import make_template
from private import account_sid, auth_token

class User(ndb.Model):
    """Model for the user db"""
    fullname = ndb.StringProperty(indexed=True)
    phone_number = ndb.StringProperty(indexed=True)
    phone_worker = ndb.BooleanProperty()
    can_text = ndb.BooleanProperty()
    PAB = ndb.BooleanProperty()
    
class Call(ndb.Model):
    """model for the calls db"""
    calls = ndb.StringProperty(indexed=True)
    
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class NewCall(webapp2.RequestHandler):
    """This gives a page to make a call to any specified users"""
    def get(self):
        template_values = make_template(self)
        
        info = ndb.gql("SELECT * FROM User")
        user_list = []
        for i in info:
            to_append = {}
            to_append['fullname'] = i.fullname
            to_append['phone_number'] = i.phone_number
            to_append['can_text'] = "disabled" if (i.can_text==False) else ""
            user_list.append(to_append)
        template_values['user_list'] = user_list
        
        template = JINJA_ENVIRONMENT.get_template('newcall.jinja')
        self.response.write(template.render(template_values))
        
class MakeCall(webapp2.RequestHandler):
    """Actually does call and text type stuff.  Yay.""" 
    def get(self):
        template_values = make_template(self)
        if template_values['admin']:
            client = TwilioRestClient(account_sid, auth_token)
            
            to_text = self.request.get_all('text')
            if self.request.get('PAB_text')=="on":
                info = ndb.gql("SELECT * FROM User WHERE PAB=True")
                for i in info:
                    if i.can_text and i.fullname not in to_text:
                        to_text.append(i.fullname)
            if self.request.get('ALL_text')=="on":
                info = ndb.gql("SELECT * FROM User WHERE can_text=True")
                for i in info:
                    if i.fullname not in to_text:
                        to_text.append(i.fullname)
            for i in to_text:
                infos = User.query(User.fullname==i).fetch(1, projection=[User.phone_number])
                for info in infos:
                    message_out = client.messages.create(to=info.phone_number, from_='2065576875', body=self.request.get('smstext'))
                    logging.debug(message_out)
            
            call_id=int(time())
            call = Call(key=ndb.Key(Call, call_id))
            to_call = []
            for i in self.request.get_all('call'):
                infos = ndb.gql("SELECT * FROM User WHERE fullname=:1", i)
                info = info
                to_call.append(info.phone_number)
            if self.request.get('PAB_call')=="on":
                info = ndb.gql("SELECT * FROM User WHERE PAB=True")
                for i in info:
                    if i.phone_number not in to_call:
                        to_call.append(i.phone_number)
            if self.request.get('ALL_call')=='on':
                info = ndb.gql("SELECT * FROM User")
                for i in info:
                    if i.phone_number not in to_call:
                        to_call.append(i.phone_number)
            call.calls = str(json.dumps(to_call))
            call_id = call.put()
            call_id = call_id.id()
            call_out = client.calls.create(to=self.request.get('your_phone'),
                                       from_='2065576875',
                                       url='https://teen-link.appspot.com/twiml?to_call=%s' % (str(call_id)),
                                       method='GET')
            logging.debug(call_out)
        template = JINJA_ENVIRONMENT.get_template('makecall.jinja')
        self.response.write(template.render(template_values))
        

app = webapp2.WSGIApplication([
                               ('/action/newcall', NewCall),
                               ('/action/makecall', MakeCall)],
                              debug=True)