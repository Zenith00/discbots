
from imgurpython import ImgurClient

client_id = '5e1b2fcfcf0f36e'
client_secret = 'd919f14c31fa97819b1e9c82e2be40aef8bd9682'
client = ImgurClient(client_id, client_secret)

# Authorization flow, pin example (see docs for other auth types)
authorization_url = client.get_auth_url('pin')

# ... redirect user to `authorization_url`, obtain pin (or code or token) ...

credentials = client.authorize('PIN OBTAINED FROM AUTHORIZATION', 'afc2380eaf')
client.set_user_auth(credentials['access_token'], credentials['refresh_token'])