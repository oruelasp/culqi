# -*- coding: utf-8 -*-
{
    'name': 'Culqi Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Culqi Implementation',
    'version': '1.0',
    'author': 'El impeishant',
    'description': """Culqi Payment Acquirer""",
    'depends': [
        'sale_payment',
        'website_sale'
    ],
    'data': [
        'views/payment_views.xml',
        'views/payment_culqi_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
