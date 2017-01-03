import logging
import os
import webapp2
import json

import stripe
stripe.api_key = "sk_test_m4QQ4tXt50ceGcWl9MsiA21B"


class ViewAccount(webapp2.RequestHandler):

  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
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
      self.response.write(json.dumps(data))
    except:
      self.response.write('')


class ListProducts(webapp2.RequestHandler):

  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      params = {
        "active": "true",
        "limit": 10,
        "starting_after": self.request.get('start', None)
      }
      data = stripe.Product.list(**params)
      self.response.write(data)
    except:
      self.response.write('')


class ViewProduct(webapp2.RequestHandler):

  def get(self, product):
    self.response.headers['Content-Type'] = 'application/json'
    try:
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
      self.response.write(data)
    except:
      self.response.write('')


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
    
    def order_is_valid(order):
      if (order['currency'] is None or \
          order['email'] is None or \
          len(order['items']) == 0 or \
          order['shipping']['name'] is None or \
          order['shipping']['phone'] is None or \
          order['shipping']['address']['country'] is None or \
          order['shipping']['address']['state'] is None or \
          order['shipping']['address']['city'] is None or \
          order['shipping']['address']['postal_code'] is None or \
          order['shipping']['address']['line1'] is None):
        return False
      else:
        return True
    
    try:
      params = json.loads(self.request.body)
      if (params.get('id', None)):
        self.response.write('')
        return
      order = {
        'currency': params.get('currency', None),
        'email': params.get('email', None),
        'items': get_items(params.get('items', [])),
        'shipping': {
          'name': params.get('shipping', {}).get('name', None),
          'phone': params.get('shipping', {}).get('phone', None),
          'address': {
            'country': params.get('shipping', {}).get('address', {}).get('country', None),
            'state': params.get('shipping', {}).get('address', {}).get('state', None),
            'city': params.get('shipping', {}).get('address', {}).get('city', None),
            'postal_code': params.get('shipping', {}).get('address', {}).get('postal_code', None),
            'line1': params.get('shipping', {}).get('address', {}).get('line1', None),
            'line2': params.get('shipping', {}).get('address', {}).get('line2', None)
          }
        }
      }
      if (params.get('coupon', None)):
        order['coupon'] = params.get('coupon')
      if (order_is_valid(order)):
        data = stripe.Order.create(**order)
        self.response.write(data)
    except:
      self.response.write('')


class UpdateOrder(webapp2.RequestHandler):

  def post(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      params = json.loads(self.request.body)
      if (params.get('id', None)):
        order = stripe.Order.retrieve(params.get('id', None))
        if (order):
          if (params.get('selected_shipping_method', None)):
            order['selected_shipping_method'] = params.get('selected_shipping_method')
          if (params.get('coupon', None)):
            order['coupon'] = params.get('coupon')
          if (params.get('status') == 'canceled'):
            order['status'] = params.get('status')
          data = order.save()
          self.response.write(data)
    except:
      self.response.write('')


class PayOrder(webapp2.RequestHandler):

  def post(self):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      params = json.loads(self.request.body)
      if (params.get('id', None) and params.get('source', None)):
        order = stripe.Order.retrieve(params.get('id', None))
        if (order):
          data = order.pay(source=params.get('source'))
          self.response.write(data)
    except:
      self.response.write('')


class ViewOrder(webapp2.RequestHandler):

  def get(self, order):
    self.response.headers['Content-Type'] = 'application/json'
    try:
      data = stripe.Order.retrieve(order)
      self.response.write(data)
    except:
      self.response.write('')


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
    except:
      self.response.write('')


APP = webapp2.WSGIApplication([webapp2.Route(r'/account', handler=ViewAccount),
                              webapp2.Route(r'/products', handler=ListProducts),
                              webapp2.Route(r'/product/<product:(.*)>', handler=ViewProduct),
                              webapp2.Route(r'/order/create', handler=CreateOrder),
                              webapp2.Route(r'/order/update', handler=UpdateOrder),
                              webapp2.Route(r'/order/pay', handler=PayOrder),
                              webapp2.Route(r'/order/<order:(.*)>', handler=ViewOrder)],
                              debug=True)