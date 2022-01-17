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
                                     x.journal_id.l10n_ar_afip_ws
                                     and not x.l10n_ar_afip_auth_code):
                if inv.journal_id.caea_journal_id:
                    inv.journal_id = inv.journal_id.caea_journal_id
        super(AccountMove, inv)._post()

    def _l10n_ar_do_afip_ws_request_cae(self, client, auth, transport):
        caea_state = self.env['ir.config_parameter'].sudo().get_param(
            'afip.ws.caea.state', 'inactive')
        if caea_state == 'active':
            for inv in self.filtered(lambda x:
                                     x.journal_id.l10n_ar_afip_ws
                                     and not x.l10n_ar_afip_auth_code):
                afip_caea = inv.company_id.get_active_caea()
                if inv.journal_id.use_for_caea and afip_caea:
                    values = {'l10n_ar_afip_auth_mode': 'CAEA',
                              'l10n_ar_afip_auth_code': afip_caea['name'],
                              'l10n_ar_afip_auth_code_due': self.invoice_date,
                              'l10n_ar_afip_result': '',
                              'caea_id': afip_caea.id
                              }
                    inv.sudo().write(values)
                else:
                    inv.message_post(body='<p><b>' + _('AFIP Messages') +
                                     '</b></p><p><i>%s</i></p>' % _('The journal not has CAEA journal'))
        else:
            super()._l10n_ar_do_afip_ws_request_cae(client, auth, transport)

    def get_pyafipws_last_invoice(self, document_type):
        if self.journal_id.use_for_caea:
            return self._l10n_ar_get_document_number_parts(self.l10n_latam_document_number,
                                                           self.l10n_latam_document_type_id.code)['invoice_number']
        else:
            return super().get_pyafipws_last_invoice(document_type)

    def _is_argentina_electronic_invoice(self):
        return bool(self.journal_id.l10n_latam_use_documents and
                    self.env.company.country_id.code == "AR" and
                    self.journal_id.l10n_ar_afip_ws and not self.journal_id.use_for_caea 
                    )
