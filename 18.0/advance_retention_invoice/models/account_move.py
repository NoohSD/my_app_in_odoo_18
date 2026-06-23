# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    """Extend account.move.line to support advance/retention line types."""
    _inherit = 'account.move.line'

    display_type = fields.Selection(
        selection_add=[
            ('others', 'Others'),
        ],
        ondelete={'others': 'cascade'},
    )

    line_type = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('advance_payment', 'Advance Payment'),
            ('retention', 'Retention'),
        ],
        default='default',
        copy=True,
        string='Line Type',
    )


class AccountMove(models.Model):
    """
    Extend account.move with:
      - advance_amt  : amount to deduct as advance payment already collected
      - retention_amt: amount to hold back (retention)

    Both fields trigger:
      1. Recomputation of net_amt_before_tax, vat_15, net_including_vat, due_balance
      2. Creation / refresh of dedicated journal lines (display_type='others')
      3. Adjustment of the receivable and tax lines so the move stays balanced
    """
    _inherit = 'account.move'

    # ── New fields ────────────────────────────────────────────────────────────

    advance_amt = fields.Float(
        string='Advanced Amount',
        default=0.0,
        help='Amount already collected as an advance payment. '
             'A dedicated debit journal line is created automatically.',
    )
    retention_amt = fields.Float(
        string='Retention Amount',
        default=0.0,
        help='Amount withheld as retention. '
             'A dedicated debit journal line is created automatically.',
    )

    # ── Computed summary fields ───────────────────────────────────────────────

    total_disc = fields.Float(
        string='Discount',
        compute='_compute_advance_retention_totals',
        store=True,
    )
    net_amt_before_tax = fields.Float(
        string='Net Amount Before VAT',
        compute='_compute_advance_retention_totals',
        store=True,
    )
    vat_15 = fields.Float(
        string='VAT (15%)',
        compute='_compute_advance_retention_totals',
        store=True,
    )
    net_including_vat = fields.Float(
        string='Net Total Including VAT',
        compute='_compute_advance_retention_totals',
        store=True,
    )
    due_balance = fields.Float(
        string='Due Balance',
        compute='_compute_advance_retention_totals',
        store=True,
    )

    # ── Compute ───────────────────────────────────────────────────────────────

    @api.depends(
        'invoice_line_ids',
        'invoice_line_ids.discount',
        'invoice_line_ids.price_unit',
        'invoice_line_ids.quantity',
        'invoice_line_ids.price_total',
        'amount_untaxed',
        'amount_tax',
        'advance_amt',
        'retention_amt',
    )
    def _compute_advance_retention_totals(self):
        for move in self:
            # Total discount across all invoice lines
            total_disc = 0.0
            for line in move.invoice_line_ids:
                disc_unit = line.price_unit * (line.discount / 100.0)
                total_disc += line.quantity * disc_unit

            # Net amount before VAT = untaxed − advance − discount
            before_tax = move.amount_untaxed - move.advance_amt - total_disc

            # VAT: recalculate at 15 % when advance is present, else keep Odoo's figure
            if move.advance_amt and move.amount_tax:
                vat_15 = round(before_tax * 15.0 / 100.0, 2)
            else:
                vat_15 = move.amount_tax

            net_with_tax = before_tax + vat_15
            due_balance = net_with_tax - move.retention_amt

            move.total_disc = total_disc
            move.net_amt_before_tax = before_tax
            move.vat_15 = vat_15
            move.net_including_vat = net_with_tax
            move.due_balance = due_balance

    # ── Helpers: create journal lines ─────────────────────────────────────────

    def _get_advance_account(self):
        """Return the advance account from the partner; raise if missing."""
        account = self.partner_id.advanced_account_id
        if not account:
            raise ValidationError(_(
                'Please set the Advance Account on the partner "%s" '
                'before saving this invoice.',
                self.partner_id.display_name,
            ))
        return account

    def _get_retention_account(self):
        """Return the retention account from the partner; raise if missing."""
        account = self.partner_id.retention_account_id
        if not account:
            raise ValidationError(_(
                'Please set the Retention Account on the partner "%s" '
                'before saving this invoice.',
                self.partner_id.display_name,
            ))
        return account

    def _build_special_line_vals(self, name, account_id, line_type, amount):
        """
        Build the value dict for an advance/retention journal line.
        The debit/credit sides are set in _update_lines() after the line exists.
        """
        return {
            'name': name,
            'quantity': 1.0,
            'date_maturity': fields.Date.context_today(self),
            'move_id': self.id,
            'account_id': account_id,
            'partner_id': self.commercial_partner_id.id,
            'line_type': line_type,
            'currency_id': self.currency_id.id,
            'display_type': 'others',
            'company_id': self.company_id.id,
        }

    # ── Core update routine ───────────────────────────────────────────────────

    def _update_lines(self):
        """
        1. Remove stale advance/retention lines.
        2. Re-create them if the respective amounts are set.
        3. Fix the receivable and tax lines so the move stays in balance.
        """
        ctx_no_check = {
            'check_move_validity': False,
            'skip_update': True,
            'force_delete': True,
        }

        for move in self:
            # ── Step 1: drop old special lines ────────────────────────────────
            old_lines = move.line_ids.filtered(
                lambda l: l.line_type in ('advance_payment', 'retention')
            )
            if old_lines:
                old_lines.with_context(**ctx_no_check).unlink()

            # Shortcut references used repeatedly below
            is_sale_like = move.move_type in ('out_invoice', 'in_refund')
            is_refund = move.move_type == 'out_refund'

            def _receivable():
                lines = move.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable'
                )
                return lines[:1]

            def _tax_line():
                lines = move.line_ids.filtered(lambda l: l.tax_line_id)
                return lines[:1]

            balance = move.due_balance + move.total_disc

            # ── Step 2a: Advance Payment line ─────────────────────────────────
            if move.advance_amt:
                account_id = move._get_advance_account().id
                vals = move._build_special_line_vals(
                    name='Advance Payment ' + str(move.advance_amt),
                    account_id=account_id,
                    line_type='advance_payment',
                    amount=move.advance_amt,
                )
                if is_sale_like and move.amount_untaxed:
                    vals.update({
                        'debit': move.advance_amt,
                        'credit': 0.0,
                        'amount_currency': move.advance_amt,
                    })
                elif is_refund and move.amount_untaxed:
                    vals.update({
                        'debit': 0.0,
                        'credit': move.advance_amt,
                        'amount_currency': -move.advance_amt,
                    })
                self.env['account.move.line'].with_context(**ctx_no_check).create(vals)

            # ── Step 2b: Retention line ────────────────────────────────────────
            if move.retention_amt:
                account_id = move._get_retention_account().id
                vals = move._build_special_line_vals(
                    name='Retention ' + str(move.retention_amt),
                    account_id=account_id,
                    line_type='retention',
                    amount=move.retention_amt,
                )
                if is_sale_like and move.amount_untaxed:
                    vals.update({
                        'debit': move.retention_amt,
                        'credit': 0.0,
                        'amount_currency': move.retention_amt,
                    })
                elif is_refund and move.amount_untaxed:
                    vals.update({
                        'debit': 0.0,
                        'credit': move.retention_amt,
                        'amount_currency': -move.retention_amt,
                    })
                self.env['account.move.line'].with_context(**ctx_no_check).create(vals)

            # ── Step 3: re-balance receivable and tax lines ───────────────────
            rec_line = _receivable()
            tax_line = _tax_line()

            if is_sale_like and move.amount_untaxed:
                if tax_line:
                    tax_line.with_context(**ctx_no_check).write(
                        {'credit': move.vat_15}
                    )
                if rec_line:
                    rec_line.with_context(**ctx_no_check).write(
                        {'debit': balance}
                    )
            elif move.move_type != 'entry':
                if tax_line:
                    tax_line.with_context(**ctx_no_check).write(
                        {'debit': move.vat_15}
                    )
                if rec_line:
                    rec_line.with_context(**ctx_no_check).write(
                        {'credit': balance}
                    )

            move._cr.commit()

    # ── ORM overrides ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        # Strip out any pre-created Retention lines coming from the UI
        # (they will be re-created properly by _update_lines)
        for vals in vals_list:
            if 'line_ids' in vals:
                vals['line_ids'] = [
                    cmd for cmd in vals['line_ids']
                    if not (
                        isinstance(cmd, (list, tuple))
                        and len(cmd) >= 3
                        and isinstance(cmd[2], dict)
                        and 'Retention' in (cmd[2].get('name') or '')
                    )
                ]

        moves = super(AccountMove, self.with_context(check_move_validity=False)).create(
            vals_list
        )
        for move in moves:
            move._update_lines()
        return moves

    def write(self, vals):
        res = super(AccountMove, self.with_context(check_move_validity=False)).write(vals)
        # Re-sync lines only when the relevant amounts change
        if 'advance_amt' in vals or 'retention_amt' in vals:
            self._update_lines()
        return res

    def action_post(self):
        for move in self:
            move._update_lines()
        return super(AccountMove, self.with_context(check_move_validity=False)).action_post()
