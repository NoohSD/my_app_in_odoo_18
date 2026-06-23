# -*- coding: utf-8 -*-
{
    'name': 'Product Running Cost & Move Type Tracker',
    'version': '18.0.1.0.0',
    'author': 'Nooh Suliman',
    'website': 'https://www.linkedin.com/in/nooh-suliman/',
    'category': 'Inventory/Inventory',
    'summary': 'Capture product cost at validation time and classify stock movements automatically',

    'description': """
Stock Cost Snapshot & Move Type Tracker
======================================

This module enhances stock move lines by recording critical information
at the exact moment a transfer is validated.

Key Features:
-------------
- Capture real product cost at validation time 
- Automatically detect move type (Purchase, Sale, Internal, Adjustment, Scrap)
- Smart handling of multi-step routes
- Accurate audit trail for inventory valuation

Perfect for:
------------
- Inventory control
- Cost auditing
- Financial tracking
- Warehouse operations

Technical Highlights:
---------------------
- Values stored permanently (no recomputation)
- Written once during validation (_action_done)
- Multi-company support
- Clean and optimized logic

Dependencies:
-------------
- stock
- stock_account
- hide_sale_stock_cost_margin
    """,

    'depends': [
        'stock',
        'stock_account',
    ],

    'data': [
        'views/stock_move_line_views.xml',
    ],
    'images': ['static/description/banner.png',],
    'icon': 'static/description/icon.png',

    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',

    'price': 0,
    'currency': 'USD',

    'application': False,
}