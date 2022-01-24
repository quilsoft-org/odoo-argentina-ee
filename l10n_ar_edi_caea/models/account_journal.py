from odoo import fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    caea_journal_id = fields.Many2one(
        'account.journal',
        string='Caea journal',
    )
    
    def _get_l10n_ar_afip_pos_types_selection(self):
        """ Add more options to the selection field AFIP POS System, re order options by common use """
        res = super()._get_l10n_ar_afip_pos_types_selection()
        res.append(('CAEA', _('Electronic Invoice CAEA - Advance electronic authorization code')))
        return res
