import unittest
import app as program
import random
import bs4

UNAME="admin"
PWORD="badpassword"
PIN="19008675309"

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        app = program.create_app()
        app.debug = True
        self.app = app.test_client()

    def test_route_login(self):
        res = self.app.get("/login")
        assert res.status_code == 200
        assert b"Login" in res.data

    def test_route_register(self):
        res = self.app.get("/register")
        assert res.status_code == 200
        assert b"Register" in res.data

    def test_register(self):
        response = self.app.get('/register')
        html = bs4.BeautifulSoup(response.data,"html.parser")
        csrf_token = html.find('input', {'id': 'csrf_token'}).get('value')      
        uname = "username"+str(random.randint(1, 1000000))
        pword = "password"+str(random.randint(1, 1000000))
        pin = random.randint(10000000000, 99999999999)
        data = dict(
            csrf_token=csrf_token,
            uname=uname,
            pword=pword,
            pin=pin
        )
        response = self.app.post('/register', data=data, follow_redirects=True)
        # print("response: %s" % response.data)
        assert b"Success" in response.data  
  
    def test_login_success(self):
        response = self.app.get('/login')
        csrf_token = bs4.BeautifulSoup(response.data,"html.parser").find('input', {'id': 'csrf_token'}).get('value')      
        data = dict(
            csrf_token=csrf_token,
            uname=UNAME,
            pword=PWORD,
            pin=PIN
        )
        response = self.app.post('/login', data=data, follow_redirects=True)
        assert b"Success" in response.data  

    def test_login_2fa_failure(self):
        response = self.app.get('/login')
        csrf_token = bs4.BeautifulSoup(response.data,"html.parser").find('input', {'id': 'csrf_token'}).get('value')      
        data = dict(
            csrf_token=csrf_token,
            uname=UNAME,
            pword=PWORD,
            pin="29008675309"
        )        
        response = self.app.post('/login', data=data, follow_redirects=True)
        assert b"Two-factor failure" in response.data  

    def test_login_user_failure(self):
        response = self.app.get('/login')
        csrf_token = bs4.BeautifulSoup(response.data,"html.parser").find('input', {'id': 'csrf_token'}).get('value')      
        uname = "bobby"
        pword = "sacamano"
        pin = ""
        data = dict(
            csrf_token=csrf_token,
            uname=uname,
            pword=pword,
            pin=pin
        )        
        response = self.app.post('/login', data=data, follow_redirects=True)
        assert b"Incorrect username or password" in response.data                       
            
    def test_csrf(self):
        data = dict(
            csrf_token=str(random.randint(1, 1000000)),
            uname=UNAME,
            pword=PWORD,
            pin=PIN
        )
        response = self.app.post('/register', data=data, follow_redirects=True)
        assert b"try again" in response.data          

    def test_spell_check(self):
        response = self.app.get('/login')
        csrf_token = bs4.BeautifulSoup(response.data,"html.parser").find('input', {'id': 'csrf_token'}).get('value')
        data = dict(
            csrf_token=csrf_token,
            uname=UNAME,
            pword=PWORD,
            pin=PIN
        )
        response = self.app.post('/login', data=data, follow_redirects=True) 

        inputtext = """ I know someday you'll have a byootiful life
                        I know you'll be a starr in somebody else's sky, but why
                        Why, why can't it be, oh can't it be myne?
                        Ooh, ah yeah, ah ooh """
        data = dict(
            csrf_token=csrf_token,
            inputtext=inputtext
        )
        response = self.app.post('/spell_check', data=data, follow_redirects=True) 
        html = bs4.BeautifulSoup(response.data,"html.parser")
        textout = html.find("textarea", {'id': 'textout'}).get_text() 
        misspelled = html.find("textarea", {'id': 'misspelled'}).get_text() 
        assert(textout == inputtext)        
        assert(misspelled == "byootiful, else's, myne")  

if __name__ == '__main__':
    unittest.main()