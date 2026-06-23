# -*- coding: utf-8 -*-
{
    'name': 'Advance & Retention Amounts on Invoices',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Manage Advance Payments and Retention Amounts on Invoices',
    'description': """
        This module is designed for contracting companies and adds:
        - Advance Payment Amount field on invoices
        - Retention Amount field on invoices
        - Auto-creates corresponding journal lines for both
        - Updates totals (VAT, net, due balance) accordingly
        - Displays both fields in the invoice report template
        - Supports Saudi Arabia VAT (ZATCA) requirements
    """,
    'author': 'Nooh Suliman',
    'website': 'https://www.linkedin.com/in/nooh-suliman/',
    'depends': ['account'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/report_invoice.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
    'price': 10,
    'currency': 'USD',
}