import logging
import webapp2
import json

from google.appengine.api import memcache

import settings
import stripe
stripe.api_key = settings.stripe_secret_key


class ViewAccount(webapp2.RequestHandler):

  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      data = memcache.get('account')
      if data is None:
        account = stripe.Account.retrieve()
        data = {
          'business_logo': account.get('business_logo'),
          'business_name': account.get('business_name'),
          'business_primary_color': account.get('business_primary_color'),
          'business_url': account.get('business_url'),
          'default_currency': account.get('default_currency'),
          'support_email': account.get('support_email'),
          'support_phone': account.get('support_phone'),
          'support_url': account.get('support_url')
        }
        memcache.set('account', data)
      self.response.write(json.dumps(data))
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


class ListProducts(webapp2.RequestHandler):

  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      params = {
        "active": "true",
        "limit": 10,
        "starting_after": self.request.get('start', None)
      }
      key = 'products%s' % self.request.get('start', '')
      data = memcache.get(key)
      if data is None:
        data = stripe.Product.list(**params)
        memcache.set(key, data)
      self.response.write(data)
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


class ViewProduct(webapp2.RequestHandler):

  def get(self, product):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      data = memcache.get(product)
      if data is None:
        data = stripe.Product.retrieve(product)
        if (data['skus']['has_more']):
          all_skus = []
          skus = stripe.SKU.list(active=True, limit=100, product=data['id'])
          all_skus.extend(skus['data'])
          has_more = skus['has_more']
          while has_more:
            skus = stripe.SKU.list(active=True, limit=100, product=data['id'], starting_after=all_skus[-1]['id'])
            all_skus.extend(skus['data'])
            has_more = skus['has_more']
            #has_more = (len(skus['data']) > 0)
          data['skus']['data'] = all_skus
        memcache.set(product, data)
      self.response.write(data)
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


class CreateOrder(webapp2.RequestHandler):

  def post(self):
    self.response.headers['Content-Type'] = 'application/json'
    
    def get_items(items):
      new_items = []
      for item in items:
        if (item and (type(item) is dict)):
          if (item.get('type') == 'sku' and item.get('quantity') > 0):
            new_items.append({
              'type': item.get('type'),
              'parent': item.get('parent'),
              'quantity': item.get('quantity')
              })
      return new_items
    
    def get_shipping(shipping):
      new_shipping = {}
      name = shipping.get('name', '')
      phone = shipping.get('phone', '')
      country = shipping.get('address', {}).get('country', '')
      state = shipping.get('address', {}).get('state', '')
      city = shipping.get('address', {}).get('city', '')
      postal_code = shipping.get('address', {}).get('postal_code', '')
      line1 = shipping.get('address', {}).get('line1', '')
      line2 = shipping.get('address', {}).get('line2', '')
      if (name and phone and country and state and city and postal_code and line1):
        new_shipping = {
          'name': name,
          'phone': phone,
          'address': {
            'country': country,
            'state': state,
            'city': city,
            'postal_code': postal_code,
            'line1': line1,
            'line2': line2
          }
        }
      return new_shipping
    
    try:
      params = json.loads(self.request.body)
      if (params.get('id', '')):
        self.response.set_status(400)
        self.response.write(json.dumps({'error': 'existing_order'}))
        return
      order = {
        'currency': params.get('currency', ''),
        'email': params.get('email', ''),
        'items': get_items(params.get('items', [])),
        'shipping': get_shipping(params.get('shipping', {}))
      }
      if (params.get('coupon', '')):
        order['coupon'] = params.get('coupon')
      if (order['currency'] and order['email'] and order['items'] and order['shipping']):
        data = stripe.Order.create(**order)
        self.response.write(data)
      else:
        self.response.set_status(400)
        self.response.write(json.dumps({'error': 'invalid_order'}))
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


class UpdateOrder(webapp2.RequestHandler):

  def post(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      params = json.loads(self.request.body)
      if (params.get('id', '') != ''):
        order = stripe.Order.retrieve(params.get('id', None))
        if (order):
          if (params.get('selected_shipping_method', None)):
            order['selected_shipping_method'] = params.get('selected_shipping_method')
          if (params.get('coupon', '')):
            order['coupon'] = params.get('coupon')
          if ((order['status'] == 'created') and (params.get('status') == 'canceled')):
            order['status'] = params.get('status')
          data = order.save()
          self.response.write(data)
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


class PayOrder(webapp2.RequestHandler):

  def post(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      params = json.loads(self.request.body)
      if (params.get('id', None) and params.get('source', None)):
        order = stripe.Order.retrieve(params.get('id', None))
        if (order):
          data = order.pay(source=params.get('source'))
          memcache.flush_all()
          self.response.write(data)
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


class ViewOrder(webapp2.RequestHandler):

  def get(self, order):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      data = stripe.Order.retrieve(order)
      self.response.write(data)
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


class CreateSKUs(webapp2.RequestHandler):

  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      data = []
      sku = {}
      sku['product'] = 'prod_80HnnViSIO0LWc'
      sku['price'] = 100
      sku['currency'] = 'usd'
      sku['inventory'] = {'type': 'finite', 'quantity': '1'}
      sizes = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL']
      colors = ['Black', 'Beige', 'Pink', 'Orange', 'Silver', 'Purple', 'Gray', 'Burgundy']
      fabrics = ['Silk', 'Cotton', 'Polyester']
      attributes = {}
      for size in sizes:
        attributes['size'] = size
        for color in colors:
          attributes['color'] = color
          for fabric in fabrics:
            attributes['fabric'] = fabric
            sku['attributes'] = attributes
            data.append(stripe.SKU.create(**sku))
      self.response.write(data)
    except stripe.error.APIConnectionError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_connection_error'}))
    except stripe.error.APIError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'api_error'}))
    except stripe.error.AuthenticationError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'authentication_error'}))
    except stripe.error.CardError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': e.code}))
    except stripe.error.InvalidRequestError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'invalid_request_error'}))
    except stripe.error.RateLimitError, e:
      self.response.set_status(500)
      self.response.write(json.dumps({'error': 'rate_limit_error'}))
    except:
      self.response.set_status(500)


APP = webapp2.WSGIApplication([webapp2.Route(r'/account', handler=ViewAccount),
                              webapp2.Route(r'/products', handler=ListProducts),
                              webapp2.Route(r'/product/<product:(.*)>', handler=ViewProduct),
                              webapp2.Route(r'/order/create', handler=CreateOrder),
                              webapp2.Route(r'/order/update', handler=UpdateOrder),
                              webapp2.Route(r'/order/pay', handler=PayOrder),
                              webapp2.Route(r'/order/<order:(.*)>', handler=ViewOrder)],
                              debug=True)