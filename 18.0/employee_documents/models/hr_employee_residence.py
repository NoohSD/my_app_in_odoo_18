# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta
from datetime import date


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    residence_ids = fields.One2many(
        'hr.employee.residence',
        'employee_id',
        string='Residence Documents'
    )

    residence_status = fields.Selection([
        ('valid', 'Valid'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('no_data', 'No Data'),
    ], string='Documents Status', compute='_compute_residence_status', store=True)

    @api.depends('residence_ids.state')
    def _compute_residence_status(self):
        for emp in self:
            active = emp.residence_ids.filtered(lambda r: r.residence_type == 'iqama')

            if not active:
                emp.residence_status = 'no_data'
            elif any(r.state == 'expired' for r in active):
                emp.residence_status = 'expired'
            elif any(r.state == 'expiring_soon' for r in active):
                emp.residence_status = 'expiring_soon'
            else:
                emp.residence_status = 'valid'


class HrEmployeeResidence(models.Model):
    _name = 'hr.employee.residence'
    _description = 'Employee Residence Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc'
    _rec_name = 'display_name'


    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    residence_type = fields.Selection([
        ('iqama', 'Iqama Document'),
        ('work_permit', 'Work Documents'),
        ('visit_visa', 'Visa Documents'),
        ('other', 'Other Documents'),
        
    ], string='Type', required=True, default='iqama', tracking=True)

    iqama_number = fields.Char(string='Document Number', tracking=True)
    issue_date = fields.Date(string='Issue Date', required=True, tracking=True)
    expiry_date = fields.Date(string='Expiry Date', required=True, tracking=True)

    # الحالة عادية وليست compute
    # تغيير الحالة يتم فقط من Cron
    state = fields.Selection([
        ('valid', 'Valid'),
        ('expiring_soon', 'Expiring Soon (30 days)'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
    ], string='Status', default='valid', tracking=True)

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments'
    )
    renewal_date = fields.Date(
        string='Renewal Date',
        readonly=True,
        copy=False,
        tracking=True
    )


    notes = fields.Text(string='Notes', tracking=True)

    # لمنع تكرار إرسال إيميل قريب الانتهاء
    expiring_email_sent = fields.Boolean(
        string='Expiring Soon Email Sent',
        default=False,
        copy=False
    )

    # لمنع تكرار إرسال إيميل الانتهاء
    expired_email_sent = fields.Boolean(
        string='Expired Email Sent',
        default=False,
        copy=False
    )
    remaining_days = fields.Integer(
        string='Remaining Days',
        compute='_compute_remaining_days',
        store=True
    )
    is_renewed = fields.Boolean(
        string='Renewed',
        default=False,
        copy=False
    )


    def _send_notification_email(self, template_xmlid):
        self.ensure_one()

        if not self.employee_id.work_email:
            return False

        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            return False

        template.send_mail(self.id, force_send=True)
        return True

    @api.constrains('issue_date', 'expiry_date')
    def _check_dates(self):
        for rec in self:
            if rec.issue_date and rec.expiry_date and rec.issue_date > rec.expiry_date:
                raise ValidationError(_("Issue Date cannot be after Expiry Date."))
    @api.model
    def cron_update_residence_states(self):
        today = date.today()
        soon = today + timedelta(days=30)

        records = self.search([])

        for rec in records:
            # تجاهل المستندات التي تم تجديدها
            if rec.state == 'renewed':
                continue

            old_state = rec.state

            if not rec.expiry_date:
                new_state = 'valid'
            elif rec.expiry_date < today:
                new_state = 'expired'
            elif rec.expiry_date <= soon:
                new_state = 'expiring_soon'
            else:
                new_state = 'valid'

            if old_state != new_state:
                rec.write({'state': new_state})

            if new_state == 'expiring_soon' and not rec.expiring_email_sent:
                sent = rec._send_notification_email(
                    'employee_documents.email_template_residence_expiring_soon'
                )
                if sent:
                    rec.write({'expiring_email_sent': True})

            if new_state == 'expired' and not rec.expired_email_sent:
                sent = rec._send_notification_email(
                    'employee_documents.email_template_residence_expired'
                )
                if sent:
                    rec.write({'expired_email_sent': True})
    @api.depends('employee_id', 'residence_type', 'iqama_number')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s - %s" % (
                rec.employee_id.name or '',
                dict(rec._fields['residence_type'].selection).get(rec.residence_type, '')
        )
    @api.depends('expiry_date')
    def _compute_remaining_days(self):
        today = date.today()
        for rec in self:
            if rec.expiry_date:
                rec.remaining_days = (rec.expiry_date - today).days
            else:
                rec.remaining_days = 0

    def action_renew(self):
        self.ensure_one()

        if self.state not in ['expired', 'expiring_soon']:
            return True

        # تحديث السجل الحالي
        self.write({
            'state': 'renewed',
            'is_renewed': True,
            'renewal_date': fields.Date.context_today(self),
        })

        # إنشاء سجل جديد
        new_document = self.create({
            'employee_id': self.employee_id.id,
            'residence_type': self.residence_type,
            'issue_date': fields.Date.context_today(self),
            'expiry_date': fields.Date.context_today(self),
            'iqama_number': self.iqama_number,
            'state': 'valid',
        })

        # فتح السجل الجديد
        return {
            'type': 'ir.actions.act_window',
            'name': _('Renewed Document'),
            'res_model': 'hr.employee.residence',
            'view_mode': 'form',
            'res_id': new_document.id,
            'target': 'current',
        }