from odoo import fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    caea_id = fields.Many2one(
        'afipws.caea',
        string='Caea',
        copy=False
    )

    def _post(self, soft=True):
        caea_state = self.env['ir.config_parameter'].sudo().get_param(
            'afip.ws.caea.state', 'inactive')
        if caea_state == 'active':
            for inv in self.filtered(lambda x:
                                     (x.journal_id.l10n_ar_afip_pos_system == 'CAEA' or
                                      x.journal_id.caea_journal_id)
                                     and not x.l10n_ar_afip_auth_code):
                if inv.journal_id.caea_journal_id:
                    inv.journal_id = inv.journal_id.caea_journal_id
                inv._l10n_ar_do_afip_ws_request_caea()

        super(AccountMove, inv)._post(soft)

    def _l10n_ar_do_afip_ws_request_caea(self):
        for inv in self:
            afip_caea = inv.company_id.get_active_caea()
            if inv.journal_id.l10n_ar_afip_pos_system == 'CAEA' and afip_caea:
                values = {'l10n_ar_afip_auth_mode': 'CAEA',
                          'l10n_ar_afip_auth_code': afip_caea['name'],
                          'l10n_ar_afip_auth_code_due': self.invoice_date,
                          'l10n_ar_afip_result': '',
                          'caea_id': afip_caea.id,
                          #'l10n_ar_afip_verification_type': 'required'
                          }
                inv.sudo().write(values)
            else:
                inv.message_post(body='<p><b>' + _('AFIP Messages') +
                                 '</b></p><p><i>%s</i></p>' % _('The journal not has CAEA journal'))

 
