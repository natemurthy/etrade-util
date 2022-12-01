"""Print orders"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import pickle
import pyetrade
import sys
from tabulate import tabulate

config = configparser.ConfigParser()
config.read('config.ini')

ACCT = {
    "accountId": config["DEFAULT"]["account_id"],
    "accountIdKey": config["DEFAULT"]["account_id_key"]
}

# this should be of the form key1=value,key2=value2
query_filter = None
if len(sys.argv) > 1:
    query_filter = sys.argv[1]

def parse_args(s):
    result = {}
    if s is not None:
        terms = [kwargs.split("=") for kwargs in s.split(",")]
        for kv in terms:
            result[kv[0]] = kv[1]
    return result


def load_oauth_session():
    """Load oauth session from pickle file"""
    with open('session.pickle', 'rb') as f:
        sess = pickle.load(f)
        #print('access_token', sess.access_token)
        #print('access_token_secret', sess.access_token_secret)
        return sess


def get_open_orders(sess):
    """
    List all open orders using pyetrade client

    :param sess: request session container with access tokens
    """
    order_client = pyetrade.ETradeOrder(
        config['DEFAULT']['consumer_key'],
        config['DEFAULT']['consumer_secret'],
        sess.access_token,
        sess.access_token_secret,
        dev=False
    )

    filter_kws = parse_args(query_filter)
    query_params = {}
    if 'security_type' in filter_kws:
        query_params['securityType'] = filter_kws['security_type']
    if 'symbol' in filter_kws:
        query_params['symbol'] = filter_kws['symbol']

    res = order_client.list_orders(
        account_id=config["DEFAULT"]["account_id_key"],
        resp_format="json",
        status="OPEN",
        **query_params
    )

    return res


def print_orders(response):
    """
    Displays a list of orders in table format

    :param response: response object of a list of orders
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

    if response is not None and "OrdersResponse" in response and "Order" in response["OrdersResponse"]:
        for order in response["OrdersResponse"]["Order"]:
            if order is not None and "OrderDetail" in order:
                order_row = []
                if order is not None and 'orderId' in order:
                    # col 0
                    order_row.append(order["orderId"])

                # should be guaranteed to exist based on schema definition
                # https://apisb.etrade.com/docs/api/order/api-order-v1.html#/definitions/OrdersResponse
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

                    if 'status' in detail:
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
                            order_row.append("{} {}".format(leg_0, leg_1))
                        else:
                            order_row.append("{} {}".format(instrument['orderAction'], instrument['symbolDescription']))

                    if 'orderTerm' in detail:
                        # col 7
                        order_row.append(detail["orderTerm"])

                    if 'priceType' in detail:
                        # col 8
                        order_row.append(detail["priceType"])

                orders_arr.append(order_row)

    filtered_orders = [table_header] + orders_arr
    print(tabulate(filtered_orders, headers='firstrow'), '\n')


if __name__ == "__main__":
    s = load_oauth_session()

    res = get_open_orders(s)
    
    print_orders(res)
    
