# -*- coding: utf-8 -*-

{
'name': 'Saudi Employee Iqama & Documents Management',

'summary': 'Track employee Iqama, work permits, visas, expiry dates, renewals and automatic email alerts.',

'description': """
```

# Saudi Employee Iqama & Documents Management

A complete HR solution for managing employee Iqama and other important documents.

## Features

* Manage employee Iqama and document records.
* Support Iqama, Work Permit, Visa and Other Documents.
* Track issue date and expiry date.
* Calculate remaining days automatically.
* Automatic status update:

  * Valid
  * Expiring Soon
  * Expired
  * Renewed
* Automatic email notifications for expiring documents.
* Automatic email notifications for expired documents.
* Upload and manage document attachments.
* Keep document history and renewal records.
* Employee document overview inside employee form.
* Color-coded list view.
* Chatter tracking and activity log.
* Renewal workflow with renewal date tracking.
* Fully integrated with Odoo HR.

## Supported Documents

* Iqama Documents
* Work Permits
* Visit Visas
* Other Employee Documents

## Compatible With

* Odoo 18 Enterprise
  """,

  'author': 'Nooh Suliman',
  'website': 'https://www.linkedin.com/in/nooh-suliman',

  'category': 'Human Resources',
  'version': '18.0.1.0.0',
  'license': 'LGPL-3',

  'depends': [
  'hr',
  'mail',
  ],

  'data': [
  'security/ir.model.access.csv',
  'data/mail_templates.xml',
  'data/ir_cron.xml',
  'views/hr_employee_residence_views.xml',
  ],

  'images': [
  'static/description/banner.png',
  ],

  'price': 15.00,
  'currency': 'USD',

  'installable': True,
  'application': True,
  'auto_install': False,
  }
