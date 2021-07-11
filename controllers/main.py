# -*- coding: utf-8 -*-

import logging
import culqipy
import json

import pprint
import werkzeug

from odoo.addons.website_sale.controllers.main import WebsiteSale as WS

from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)


class WebsiteSale(WS):

    @http.route(['/shop/culqi/'], type='json', auth="public", website=True)
    def payment_transaction_culqi(self, **post):
        order = request.website.sale_get_order()
        transaction = request.env['payment.transaction'].sudo().search([('sale_order_id', '=', order.id)])
        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'culqi')], limit=1)
        if not transaction:
            tx = request.website.sale_get_transaction() or request.env['payment.transaction'].sudo()
            transaction = tx._check_or_create_sale_tx(order, acquirer, payment_token=False, tx_type='form')

        if order and transaction and post.get('culqi_token'):
            order.sudo().with_context(send_email=True).action_confirm()
            culqipy.public_key = acquirer.brq_websitekey
            culqipy.secret_key = acquirer.brq_secretkey
            dir_charge = {
                'amount': post.get('amount_total', 0),
                'country_code': 'PE',
                'currency_code': 'PEN',
                'description': post.get('description', ''),
                'email': post.get('email', ''),
                'source_id': post.get('culqi_token', ''),
                'metadata': {
                    'Pedido de venta': order.name
                },
            }
            res = culqipy.Charge.create(dir_charge)
            print ('res: {}'.format(res))
            transaction.sudo().write({
                'culqi_txn_token': res.get('id', ''),
                'state': 'done'
            })


class CulqiController(http.Controller):

    _accept_url = '/payment/culqi/feedback'

    @http.route(['/payment/culqi/feedback', ], type='http', auth='none', csrf=False)
    def transfer_form_feedback(self, **post):
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        # request.env['payment.transaction'].sudo().form_feedback(post, 'culqi')
        return werkzeug.utils.redirect(post.pop('return_url', '/'))

    @http.route('/payment/culqi/keys', type='json', auth="public", methods=['POST', 'GET'], csrf=False)
    def culqi_keys(self, **kw):
        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'culqi')], limit=1)
        return {
            'brq_websitekey': acquirer.brq_websitekey,
            'acquirer_id': acquirer.id
        }
