from odoo import api, fields, models, _
import qrcode
import base64
import io
from odoo import http
from num2words import num2words
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    retention_account_id = fields.Many2one('account.account',
        string='Retention Account')
    advanced_account_id = fields.Many2one('account.account',
        string='Advanced Account')
