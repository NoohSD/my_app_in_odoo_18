# -*- coding: utf-8 -*-
# from odoo import http


# class PosExtended(http.Controller):
#     @http.route('/pos_extended/pos_extended', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_extended/pos_extended/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_extended.listing', {
#             'root': '/pos_extended/pos_extended',
#             'objects': http.request.env['pos_extended.pos_extended'].search([]),
#         })

#     @http.route('/pos_extended/pos_extended/objects/<model("pos_extended.pos_extended"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_extended.object', {
#             'object': obj
#         })

