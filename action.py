import webapp2

from google.appengine.ext import db
from twilio.rest import TwilioRestClient
from time import time

from private import account_sid, auth_token

class User(db.Model):
    """Model for the user db"""
    fullname = db.StringProperty(indexed=True)
    phone_number = db.StringProperty(indexed=True)
    phone_worker = db.BooleanProperty()
    can_text = db.BooleanProperty()
    PAB = db.BooleanProperty()
    
class Call(db.Model):
    calls = db.StringListProperty()

from common import add_header


class NewCall(webapp2.RequestHandler):
    """This gives a page to make a call to any specified users"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write('<html><body>')
        can_edit = add_header(self)
        if can_edit:
            self.response.write("<form action='/action/makecall' method='GET'>")
        self.response.write("<table border='1'><tr><td>Name</td><td>Phone Number</td><td>Send SMS?</td><td>Send Voice message?</td></tr>")
        info = db.GqlQuery("SELECT * FROM User")
        for i in info.run():
            self.response.write("<tr>")
            self.response.write("<td>" + i.fullname + "</td><td>" + i.phone_number + "</td><td><input type='checkbox' name='text' value='%s' %s/></td><td><input type='checkbox' name='call' value='%s' /></td>" % (i.fullname, ("disabled" if (i.can_text==False) else ""), i.fullname))
            self.response.write("</tr>")
        self.response.write("<tr><td>All PAB</td><td>(Will only text if they can receive texts)</td><td><input type='checkbox' name='PAB_text' /></td><td><input type='checkbox' name='PAB_call' /></td><tr>")
        self.response.write("<tr><td>All Volunteers</td><td>(Will only text if they can receive texts)</td><td><input type='checkbox' name='ALL_text' /></td><td><input type='checkbox' name='ALL_call' /></td></tr>")
        self.response.write("</table>")
        self.response.write("Text to send as sms (max 140 chars): <input type='text' name='smstext' size=140 maxlength=140 /><br />")
        self.response.write("Your phone: <input type='text' name='your_phone' /><br />")
        if can_edit:
            self.response.write("<input type='submit' value='submit' />")
            self.response.write("</form>")
        self.response.write("</body></html>")
        
class MakeCall(webapp2.RequestHandler):
    """Actually does call and text type stuff.  Yay.""" 
    def get(self):
        can_edit = add_header(self)
        if can_edit:
            client = TwilioRestClient(account_sid, auth_token)
            
            to_text = self.request.get_all('text')
            if self.request.get('PAB_text')=="on":
                info = db.GqlQuery("SELECT * FROM User WHERE PAB=True")
                for i in info.run():
                    if i.can_text and i.fullname not in to_text:
                        to_text.append(i.fullname)
            if self.request.get('ALL_text')=="on":
                info = db.GqlQuery("SELECT * FROM User WHERE can_text=True")
                for i in info.run():
                    if i.fullname not in to_text:
                        to_text.append(i.fullname)
            for i in to_text:
                info = db.GqlQuery("SELECT * FROM User WHERE fullname=:1", i)
                info = info.run().next()
                message = client.messages.create(to=info.phone_number, from_='2065576875', body=self.request.get('smstext'))
            
            self.response.write("Calling your phone: answer it, make a recording after the beep, and then hang up.<br />")
            
            call_id = str(int(time()))
            call = Call(key_name=call_id)
            to_call = []
            for i in self.request.get_all('call'):
                info = db.GqlQuery("SELECT * FROM User WHERE fullname=:1", i)
                info = info.run().next()
                to_call.append(info.phone_number)
            if self.request.get('PAB_call')=="on":
                info = db.GqlQuery("SELECT * FROM User WHERE PAB=True")
                for i in info.run():
                    if i.phone_number not in to_call:
                        to_call.append(i.phone_number)
            if self.request.get('ALL_call')=='on':
                info = db.GqlQuery("SELECT * FROM User")
                for i in info.run():
                    if i.phone_number not in to_call:
                        to_call.append(i.phone_number)
            call.calls = to_call
            call.put()
            call = client.calls.create(to=self.request.get('your_phone'),
                                       from_='2065576875',
                                       url='https://teen-link.appspot.com/twiml?to_call=%s' % (call_id),
                                       method='GET',
                                       status_callback="https://teen-link.appspot.com/debug",
                                       status_callback_method="GET")
        

app = webapp2.WSGIApplication([
                               ('/action/newcall', NewCall),
                               ('/action/makecall', MakeCall)],
                              debug=True)