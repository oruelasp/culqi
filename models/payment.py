# coding: utf-8

import json
import logging

import pprint
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_culqi.controllers.main import CulqiController
from odoo.tools.float_utils import float_compare


_logger = logging.getLogger(__name__)

CULQI = 'culqi'
CULQI_SELECTION = [
    (CULQI, 'Culqi')
]


class AcquirerCulqi(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=CULQI_SELECTION)
    brq_websitekey = fields.Char('WebsiteKey', required_if_provider=CULQI, groups='base.group_user')
    brq_secretkey = fields.Char('SecretKey', required_if_provider=CULQI, groups='base.group_user')

    culqi_email_account = fields.Char('culqi Email ID', required_if_provider=CULQI, groups='base.group_user')
    culqi_seller_account = fields.Char(
        'culqi Merchant ID', groups='base.group_user',
        help='The Merchant ID is used to ensure communications coming from culqi are valid and secured.')
    culqi_use_ipn = fields.Boolean('Use IPN', default=True, help='culqi Instant Payment Notification', groups='base.group_user')
    culqi_pdt_token = fields.Char(string='culqi PDT Token', required_if_provider=CULQI, help='Payment Data Transfer allows you to receive notification of successful payments as they are made.', groups='base.group_user')
    # Server 2 server
    culqi_api_enabled = fields.Boolean('Use Rest API', default=False)
    culqi_api_username = fields.Char('Rest API Username', groups='base.group_user')
    culqi_api_password = fields.Char('Rest API Password', groups='base.group_user')
    culqi_api_access_token = fields.Char('Access Token', groups='base.group_user')
    culqi_api_access_token_validity = fields.Datetime('Access Token Validity', groups='base.group_user')
    # Default culqi fees
    fees_dom_fixed = fields.Float(default=0.35)
    fees_dom_var = fields.Float(default=3.4)
    fees_int_fixed = fields.Float(default=0.35)
    fees_int_var = fields.Float(default=3.9)

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(AcquirerCulqi, self)._get_feature_support()
        res['fees'].append('culqi')
        return res

    def culqi_get_form_action_url(self):
        return '/payment/culqi/feedback'


class TxCulqi(models.Model):
    _inherit = 'payment.transaction'

    culqi_txn_type = fields.Char('Transaction type')
    culqi_txn_token = fields.Char('Token', readonly=True)
    acquirer_journal_id = fields.Many2one(related='acquirer_id.journal_id')

    @api.model
    def _culqi_form_get_tx_from_data(self, data):
        reference, amount, currency_name = data.get('reference'), data.get('amount'), data.get('currency_name')
        tx = self.search([('reference', '=', reference)])

        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _culqi_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))

        return invalid_parameters

    def _culqi_form_validate(self, data):
        _logger.info('Validated transfer payment for tx %s: set as pending' % (self.reference))
        return self.write({'state': 'pending'})

