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
    
    use_for_caea = fields.Boolean(
        string='Use for caea',
    )


