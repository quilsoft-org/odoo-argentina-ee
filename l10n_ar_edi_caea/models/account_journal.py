from odoo import fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    caea_journal_id = fields.Many2one(
        "account.journal",
        string="Caea journal",
    )

    def _get_l10n_ar_afip_pos_types_selection(self):
        """Add more options to the selection field AFIP POS System, re order options by common use"""
        res = super()._get_l10n_ar_afip_pos_types_selection()
        res.append(
            (
                "CAEA",
                _("Electronic Invoice CAEA - Advance electronic authorization code"),
            )
        )
        return res

    def _get_journal_codes(self):
        self.ensure_one()
        usual_codes = ["1", "2", "3", "6", "7", "8", "11", "12", "13"]
        mipyme_codes = ["201", "202", "203", "206", "207", "208", "211", "212", "213"]
        invoice_m_code = ["51", "52", "53"]
        receipt_m_code = ["54"]
        receipt_codes = ["4", "9", "15"]
        if self.l10n_ar_afip_pos_system in ["CAEA"]:
            # electronic/online invoice
            return (
                usual_codes
                + receipt_codes
                + invoice_m_code
                + receipt_m_code
                + mipyme_codes
            )
        return super()._get_journal_codes()
