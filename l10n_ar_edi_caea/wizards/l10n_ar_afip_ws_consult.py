from odoo import models, fields, _
from odoo.exceptions import UserError

import zeep
import logging

_logger = logging.getLogger(__name__)


class L10nArAfipWsConsult(models.TransientModel):

    _inherit = "l10n_ar_afip.ws.consult"
    journal_id = fields.Many2one(
        "account.journal",
        domain="[('l10n_ar_afip_pos_system', 'in', ['CAEA', 'RAW_MAW', 'BFEWS', 'FEEWS'])]",
        required=True,
    )

    def button_confirm(self):
        """Recover infomation of an invoice that has already been authorized by AFIP.

        For auditing and troubleshooting purposes you can get the detailed information of an invoice number that has
        been previously sent to AFIP. You can also get the last number used in AFIP for a specific Document Type and
        POS Number as support for any possible issues on the sequence synchronization between Odoo and AFIP"""
        self.ensure_one()
        pos_number = self.journal_id.l10n_ar_afip_pos_number
        if self.journal_id.l10n_ar_afip_pos_system == "CAEA":
            afip_ws = self.journal_id.company_id.get_caea_afip_ws()
        else:
            afip_ws = self.journal_id.l10n_ar_afip_ws

        if not afip_ws:
            raise UserError(
                _("No AFIP WS selected on point of sale %s") % (self.journal_id.name)
            )
        if not self.number:
            raise UserError(_("Please set the number you want to consult"))

        connection = self.journal_id.company_id._l10n_ar_get_connection(afip_ws)
        client, auth = connection._get_client()

        res = error = False
        # We need to call a different method for every webservice type and assemble the returned errors if they exist
        if afip_ws == "wsfe":
            response = client.service.FECompConsultar(
                auth,
                {
                    "CbteTipo": self.document_type_id.code,
                    "CbteNro": self.number,
                    "PtoVta": pos_number,
                },
            )
            res = response.ResultGet
            error = response.Errors
        elif afip_ws == "wsfex":
            response = client.service.FEXGetCMP(
                auth,
                {
                    "Cbte_tipo": self.document_type_id.code,
                    "Punto_vta": pos_number,
                    "Cbte_nro": self.number,
                },
            )
            res = response.FEXResultGet
            if response.FEXErr.ErrCode != 0 or response.FEXErr.ErrMsg != "OK":
                error = response.FEXErr
        elif afip_ws == "wsbfe":
            response = client.service.BFEGetCMP(
                auth,
                {
                    "Tipo_cbte": self.document_type_id.code,
                    "Punto_vta": pos_number,
                    "Cbte_nro": self.number,
                },
            )
            res = response.BFEResultGet
            if response.BFEErr.ErrCode != 0 or response.BFEErr.ErrMsg != "OK":
                error = "\n* Code %s: %s" % (
                    response.BFEErr.ErrCode,
                    response.BFEErr.ErrMsg,
                )
            if response.BFEEvents.EventCode != 0 or response.BFEEvents.EventMsg:
                error += repr(response.BFEEvents)
        else:
            raise UserError(_("AFIP WS %s not implemented", afip_ws))

        title = _("Invoice number %s\n", self.number)
        if error:
            _logger.warning("%s\n%s" % (title, error))
            raise UserError(_("AFIP Errors") + " %s" % error)

        msg = ""
        data = zeep.helpers.serialize_object(res, dict)
        for key, value in data.items():
            msg += " * %s: %s\n" % (key, value or "")
        raise UserError(title + msg)
