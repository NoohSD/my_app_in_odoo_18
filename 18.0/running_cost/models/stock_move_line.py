# -*- coding: utf-8 -*-
from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    cost_at_move_date = fields.Float(
        string='Running Cost',
        digits='Product Price',
        copy=False,
        readonly=True,
        help=(
            "The product's unit cost at the exact moment this stock move "
            "was validated. Frozen forever after that point."
        ),
    )

    move_type_label = fields.Selection(
        selection=[
            ('purchase',      'Purchase'),
            ('sale',          'Sale'),
            ('internal',      'Internal'),
            ('inventory',     'Adjustment'),
            ('scrap_merge',   'Damaged Scrap'),
            ('scrap_expired', 'Expired Scrap'),
        ],
        string='Move Type',
        copy=False,
        readonly=True,
        help="نوع الحركة المخزنية المسجّل وقت التنفيذ.",
    )

    def _get_current_product_cost(self):
        self.ensure_one()
        if not self.product_id:
            return 0.0
        return self.product_id.with_company(
            self.company_id or self.env.company
        ).standard_price

    def _get_move_type_label(self):
        self.ensure_one()
        move = self.move_id

        if move and move.scrapped:
            dest_name = (self.location_dest_id.complete_name or '').strip()
            if 'Damaged' in dest_name:
                return 'scrap_merge'
            if 'Expired' in dest_name:
                return 'scrap_expired'
            # سكراب من نوع غير معروف → نعامله كـ Damaged
            return 'scrap_merge'

        if self.is_inventory:
            return 'inventory'

        code = (
            self.picking_id.picking_type_id.code
            if self.picking_id
            else (move.picking_type_id.code if move else None)
        )
        if code == 'incoming':
            return 'purchase'
        if code == 'outgoing':
            return 'sale'
        if code == 'internal':
            return 'internal'

        return 'internal'

    def _action_done(self):
        lines_to_stamp = self.filtered(lambda l: l.state != 'done')

        cost_map = {line.id: line._get_current_product_cost() for line in lines_to_stamp}
        type_map = {line.id: line._get_move_type_label() for line in lines_to_stamp}

        res = super()._action_done()

        for line in lines_to_stamp:
            vals = {}
            cost = cost_map.get(line.id, 0.0)
            if cost:
                vals['cost_at_move_date'] = cost
            move_type = type_map.get(line.id)
            if move_type:
                vals['move_type_label'] = move_type
            if vals:
                line.sudo().write(vals)

        return res