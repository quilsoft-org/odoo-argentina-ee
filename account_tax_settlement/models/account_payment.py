from odoo import fields, models, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Description'

    payment_date = fields.Date(string="Fecha de pago",related='payment_group_id.payment_date')