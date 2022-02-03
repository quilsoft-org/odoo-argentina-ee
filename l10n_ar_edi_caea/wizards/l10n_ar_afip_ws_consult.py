from odoo import models, fields


class L10nArAfipWsConsult(models.TransientModel):

    _inherit = 'l10n_ar_afip.ws.consult'
    journal_id = fields.Many2one('account.journal', domain="[('l10n_ar_afip_pos_system', 'in', ['CAEA', 'RAW_MAW', 'BFEWS', 'FEEWS'])]", required=True)
