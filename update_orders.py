"""Print orders"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import json
import pickle
import sys
import time
from tabulate import tabulate

config = configparser.ConfigParser()
config.read('config.ini')

BASE_URL = "https://api.etrade.com"
ACCT = {
    "accountId": config["DEFAULT"]["account_id"],
    "accountIdKey": config["DEFAULT"]["account_id_key"]
}

# this should be of the form key1=value,key2=value2
query_filter = None
if len(sys.argv) > 1:
    query_filter = sys.argv[1]

def parse_args(s):
    result = []
    if s is not None:
        result = s.split(",")
    return result


def load_oauth_session():
    """Load oauth session from pickle file"""
    with open('session.pickle', 'rb') as f:
        return pickle.load(f)


def preview_order_request(order_id):
    req = """
    <PreviewOrderRequest>
        <clientOrderId>1234567890asdfghjkl</clientOrderId>
        <orderType>SPREADS</orderType>
        <OrderDetail>
                <previewTime>{}</previewTime>
                <status>OPEN</status>
                <orderTerm>GOOD_UNTIL_CANCEL</orderTerm>
                <priceType>NET_DEBIT</priceType>
                <limitPrice>{}</limitPrice>
                <stopPrice>0</stopPrice>
                <marketSession>REGULAR</marketSession>
                <replacesOrderId>{}</replacesOrderId>
                <allOrNone>false</allOrNone>
                <Instrument>
                        <Product>
                                <symbol>SPX</symbol>
                                <securityType>OPTN</securityType>
                                <callPut>PUT</callPut>
                                <expiryYear>2023</expiryYear>
                                <expiryMonth>4</expiryMonth>
                                <expiryDay>21</expiryDay>
                                <strikePrice>3425</strikePrice>
                                <productId>
                                        <symbol>SPX---230421P03425000</symbol>
                                        <typeCode>OPTION</typeCode>
                                </productId>
                        </Product>
                        <symbolDescription>SPX Apr 21 \'23 $3425 Put</symbolDescription>
                        <orderAction>BUY_OPEN</orderAction>
                        <quantityType>QUANTITY</quantityType>
                        <orderedQuantity>2</orderedQuantity>
                </Instrument>
                <Instrument>
                        <Product>
                                <symbol>SPX</symbol>
                                <securityType>OPTN</securityType>
                                <callPut>PUT</callPut>
                                <expiryYear>2023</expiryYear>
                                <expiryMonth>4</expiryMonth>
                                <expiryDay>21</expiryDay>
                                <strikePrice>3420</strikePrice>
                                <productId>
                                        <symbol>SPX---230421P03420000</symbol>
                                        <typeCode>OPTION</typeCode>
                                </productId>
                        </Product>
                        <symbolDescription>SPX Apr 21 \'23 $3420 Put</symbolDescription>
                        <orderAction>SELL_OPEN</orderAction>
                        <quantityType>QUANTITY</quantityType>
                        <orderedQuantity>2</orderedQuantity>
                </Instrument>
        </OrderDetail>
    </PreviewOrderRequest>
    """.format(int(time.time()*1000), str('{:,.2f}'.format(0.40)), order_id)
    return req


def place_order_request():
    req = {
        "orderType": "OPTN",
        "clientOrderId": "123456789asdfghjkl", # 20 chars
        "order": [
            
        ],
        "previewIds": [
            {
                "previewId": "",
                "cashMargin": "MARGIN"
            }
        ]
    }
    return req


def update_orders(session, order_ids_arr):
    for o in order_ids_arr:
        change_order_url = "{}/v1/accounts/{}/orders/{}/change/place.json".format(
                BASE_URL, ACCT["accountIdKey"], o)
        print(change_order_url)
        headers = {"Content-Type": "application/xml", "consumerKey": config["DEFAULT"]["CONSUMER_KEY"]}
        req = preview_order_request(int(o))
        resp = session.put(change_order_url, header_auth=True, headers=headers, data=req)
        print(resp.status_code, resp.content)
        break # exit loop early

        #return resp.status_code, resp.json()


def list_orders_xml(session, order_status):
    orders_url = "{}/v1/accounts/{}/orders".format(BASE_URL, ACCT["accountIdKey"])
    headers = {"consumerkey": config["DEFAULT"]["CONSUMER_KEY"]}
    params_open = {"status": order_status}
    print('\n', 'GET', orders_url, '\n')
    resp = session.get(orders_url, header_auth=True, params=params_open, headers=headers)
    return resp.status_code, resp.content
    
def print_orders(response, status):
    """
    Formats and displays a list of orders

    :param response: response object of a list of orders
    :param status: order status related to the response object
    """
    table_header = [
        'Order #', 
        'Security Type', 
        'Symbol', 
        'Status', 
        'Price',
        'Quantity', 
        'Desc',
        'Term',
        'Price Type', 
    ]
    orders_arr = []
    filter_kws = parse_args(query_filter)

    if response is not None and "OrdersResponse" in response and "Order" in response["OrdersResponse"]:
        for order in response["OrdersResponse"]["Order"]:
            if order is not None and "OrderDetail" in order:
                order_row = []
                if order is not None and 'orderId' in order:
                    # col 0
                    order_row.append(order["orderId"])

                details = order["OrderDetail"]

                if len(details) == 1:
                    detail = details[0]
 
                    # this will have len=1 for single positions, and len=2 for vertical spreads
                    # see "col 6" where symbolDescription is formatted with orderAction
                    instrument = detail["Instrument"][0]
                
                    if 'Product' in instrument and 'securityType' in instrument["Product"]:
                        # col 1
                        order_row.append(instrument["Product"]["securityType"])

                    if 'Product' in instrument and 'symbol' in instrument["Product"]:
                        # col 2 
                        order_row.append(instrument["Product"]["symbol"])

                    if status != "expired" and status != "rejected" and 'status' in detail:
                        # col 3
                        order_row.append(detail["status"])

                    if 'limitPrice' in detail:
                        # col 4
                        order_row.append(str('${:,.2f}'.format(detail["limitPrice"])))

                    if 'orderedQuantity' in instrument:
                        # col 5
                        order_row.append(str("{:,}".format(instrument["orderedQuantity"])))

                    if 'symbolDescription' in instrument and 'orderAction' in instrument:
                        # col 6 
                        instruments = detail["Instrument"]
                        if len(instruments) == 2:
                            leg_0 = "{} {}".format(instruments[0]['orderAction'], instruments[0]['symbolDescription'])
                            leg_1 = "{} {}".format(instruments[1]['orderAction'], instruments[1]['symbolDescription'])
                            order_row.append("{} / {}".format(leg_0, leg_1))
                        else:
                            order_row.append("{} {}".format(instrument['orderAction'], instrument['symbolDescription']))

                    if 'orderTerm' in detail:
                        # col 7
                        order_row.append(detail["orderTerm"])

                    if 'priceType' in detail:
                        # col 8
                        order_row.append(detail["priceType"])

                orders_arr.append(order_row)

    filtered_orders = orders_arr
    if 'security_type' in filter_kws:
        filtered_orders = list(
            filter(lambda r: r[1] == filter_kws['security_type'], filtered_orders))
    if 'symbol' in filter_kws:
        filtered_orders = list(
            filter(lambda r: filter_kws['symbol'] in r[2], filtered_orders))

    filtered_orders = [table_header] + filtered_orders
    print(tabulate(filtered_orders, headers='firstrow'), '\n')


if __name__ == "__main__":
    s = load_oauth_session()

    #order_status = 'OPEN'
    #http_code, resp_text = list_orders_xml(s, order_status)
    #if http_code != 200:
        #print("unable to fetch orders", http_code, resp_text, '\n')
        #sys.exit()
    
    #print(resp_text)
    update_orders(s, parse_args(sys.argv[1]))
    print("tbd")
    
