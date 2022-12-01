"""Authorize Etrade API client and obtain access token"""

import configparser
import pickle
import webbrowser
from rauth import OAuth1Service

config = configparser.ConfigParser()
config.read('config.ini')


def oauth():
    """Allows user authorization for the sample application with OAuth 1"""
    etrade = OAuth1Service(
        name="etrade",
        consumer_key=config["DEFAULT"]["CONSUMER_KEY"],
        consumer_secret=config["DEFAULT"]["CONSUMER_SECRET"],
        request_token_url="https://api.etrade.com/oauth/request_token",
        access_token_url="https://api.etrade.com/oauth/access_token",
        authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
        base_url="https://api.etrade.com")

    # Step 1: Get OAuth 1 request token and secret
    request_token, request_token_secret = etrade.get_request_token(
        params={"oauth_callback": "oob", "format": "json"})

    # Step 2: Go through the authentication flow. Login to E*TRADE.
    authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
    webbrowser.open(authorize_url)
    text_code = input("Please accept agreement and enter verification code from browser: ")

    # Step 3: Exchange the authorized request token for an authenticated OAuth 1 session
    session = etrade.get_auth_session(request_token,
            request_token_secret,
            params={"oauth_verifier": text_code})

    print("access_token_response:", session.access_token_response)
    print('access_token:', session.access_token)
    print('access_token_secret:', session.access_token_secret)

    with open('session.pickle', mode='wb') as f:
        print("writing oauth session state to file")
        pickle.dump(session, f)


if __name__ == "__main__":
    oauth()
