from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_repr
import re

import logging
_logger = logging.getLogger(__name__)

WS_DATE_FORMAT = {'wsfe': '%Y%m%d', 'wsfex': '%Y%m%d', 'wsbfe': '%Y%m%d'}


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_ar_afip_pos_system = fields.Char(
        string='AFIP POS System',
        compute='_compute_l10n_ar_afip_pos_system'
    )

    l10n_ar_afip_result = fields.Selection(
        selection_add=[('R', 'Rejected')],
        ondelete={'R': 'set null'}
    )

    caea_id = fields.Many2one(
        'l10n_ar.afipws.caea',
        string='Caea',
        copy=False
    )
    caea_post_datetime = fields.Datetime(
        string='CAEA post datetime',
    )
    l10n_ar_afip_caea_reported = fields.Boolean(
        string='Caea Reported',
    )

    @api.depends('journal_id')
    def _compute_l10n_ar_afip_pos_system(self):
        for move in self:
            move.l10n_ar_afip_pos_system = move.journal_id.l10n_ar_afip_pos_system

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

        super(AccountMove, self)._post(soft)

    def _l10n_ar_do_afip_ws_request_caea(self):
        for inv in self:
            afip_caea = inv.company_id.get_active_caea()
            if not len(afip_caea):
                raise UserError(_('Dont have CAEA Active'))
            if inv.journal_id.l10n_ar_afip_pos_system == 'CAEA' and afip_caea:
                values = {'l10n_ar_afip_auth_mode': 'CAEA',
                          'l10n_ar_afip_auth_code': afip_caea['name'],
                          'l10n_ar_afip_auth_code_due': self.invoice_date,
                          'l10n_ar_afip_result': '',
                          'caea_id': afip_caea.id,
                          'caea_post_datetime': fields.Datetime.now()
                          #'l10n_ar_afip_verification_type': 'required'
                          }
                inv.sudo().write(values)
            else:
                inv.message_post(body='<p><b>' + _('AFIP Messages') +
                                 '</b></p><p><i>%s</i></p>' % _('The inovice has not CAEA journal'))


    # Prepare Request Data for webservices
    @api.model
    def wsfe_get_caea_request(self, caea, client=None):

        self.ensure_one()
        partner_id_code = self._get_partner_code_id(self.commercial_partner_id)
        invoice_number = self._l10n_ar_get_document_number_parts(self.l10n_latam_document_number, self.l10n_latam_document_type_id.code)['invoice_number']
        amounts = self._l10n_ar_get_amounts()
        due_payment_date = self._due_payment_date()
        service_start, service_end = self._service_dates()

        related_invoices = self._get_related_invoice_data()
        vat_items = self._get_vat()
        for item in vat_items:
            if 'BaseImp' in item and 'Importe' in item:
                item['BaseImp'] = float_repr(item['BaseImp'], precision_digits=2)
                item['Importe'] = float_repr(item['Importe'], precision_digits=2)
        vat = partner_id_code and self.commercial_partner_id.vat and re.sub(r'\D+', '', self.commercial_partner_id.vat)

        tributes = self._get_tributes()
        optionals = self._get_optionals_data()

        ArrayOfAlicIva = client.get_type('ns0:ArrayOfAlicIva')
        ArrayOfTributo = client.get_type('ns0:ArrayOfTributo')
        ArrayOfCbteAsoc = client.get_type('ns0:ArrayOfCbteAsoc')
        ArrayOfOpcional = client.get_type('ns0:ArrayOfOpcional')

        res = {'FeCabReq': {
                   'CantReg': 1, 'PtoVta': self.journal_id.l10n_ar_afip_pos_number, 'CbteTipo': self.l10n_latam_document_type_id.code},
               'FeDetReq': [{'FECAEADetRequest': {
                   'Concepto': int(self.l10n_ar_afip_concept),
                   'DocTipo': partner_id_code or 0,
                   'DocNro': vat and int(vat) or 0,
                   'CbteDesde': invoice_number,
                   'CbteHasta': invoice_number,
                   'CbteFch': self.invoice_date.strftime(WS_DATE_FORMAT['wsfe']),

                   'ImpTotal': float_repr(self.amount_total, precision_digits=2),
                   'ImpTotConc': float_repr(amounts['vat_untaxed_base_amount'], precision_digits=2),  # Not Taxed VAT
                   'ImpNeto': float_repr(amounts['vat_taxable_amount'], precision_digits=2),
                   'ImpOpEx': float_repr(amounts['vat_exempt_base_amount'], precision_digits=2),
                   'ImpTrib': float_repr(amounts['not_vat_taxes_amount'], precision_digits=2),
                   'ImpIVA': float_repr(amounts['vat_amount'], precision_digits=2),

                   # Service dates are only informed when AFIP Concept is (2,3)
                   'FchServDesde': service_start.strftime(WS_DATE_FORMAT['wsfe']) if service_start else False,
                   'FchServHasta': service_end.strftime(WS_DATE_FORMAT['wsfe']) if service_end else False,
                   'FchVtoPago': due_payment_date.strftime(WS_DATE_FORMAT['wsfe']) if due_payment_date else False,
                   'MonId': self.currency_id.l10n_ar_afip_code,
                   'MonCotiz':  float_repr(self.l10n_ar_currency_rate, precision_digits=6),
                   'CbtesAsoc': ArrayOfCbteAsoc([related_invoices]) if related_invoices else None,
                   'Iva': ArrayOfAlicIva(vat_items) if vat_items else None,
                   'Tributos': ArrayOfTributo(tributes) if tributes else None,
                   'Opcionales': ArrayOfOpcional(optionals) if optionals else None,
                   'Compradores': None,
                   'CAEA': caea,
                   'CbteFchHsGen': self.caea_post_datetime.strftime('%Y%m%d%H%M%S'),


                   }}]}
        return res
    """
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


    def _is_argentina_electronic_invoice(self):
        return bool(self.journal_id.l10n_latam_use_documents and
                    self.env.company.country_id.code == "AR" and
                    self.journal_id.l10n_ar_afip_ws and not self.journal_id.use_for_caea
                    )
    """

    def _get_related_invoice_data(self):
        """ Applies on wsfe and wsfex web services """
        self.ensure_one()
        _logger.info('journal_id.l10n_ar_afip_ws = %s', self.journal_id.l10n_ar_afip_ws)

        if self.journal_id.l10n_ar_afip_ws != False:
            return super()._get_related_invoice_data()
        res = {}
        related_inv = self._found_related_invoice()
        afip_ws = 'wsfe'

        if not related_inv:
            return res

        # WSBFE_1035 We should only send CbtesAsoc if the invoice to validate has any of the next doc type codes
        if int(self.l10n_latam_document_type_id.code) not in [2, 3, 7, 8, 91, 202, 203, 207, 208]:
            return res

        wskey = {'wsfe': {'type': 'Tipo', 'pos_number': 'PtoVta', 'number': 'Nro', 'cuit': 'Cuit', 'date': 'CbteFch'},
                 'wsbfe': {'type': 'Tipo_cbte', 'pos_number': 'Punto_vta', 'number': 'Cbte_nro', 'cuit': 'Cuit', 'date': 'Fecha_cbte'},
                 'wsfex': {'type': 'Cbte_tipo', 'pos_number': 'Cbte_punto_vta', 'number': 'Cbte_nro', 'cuit': 'Cbte_cuit'}}

        res.update({wskey[afip_ws]['type']: related_inv.l10n_latam_document_type_id.code,
                    wskey[afip_ws]['pos_number']: related_inv.journal_id.l10n_ar_afip_pos_number,
                    wskey[afip_ws]['number']: self._l10n_ar_get_document_number_parts(
                        related_inv.l10n_latam_document_number, related_inv.l10n_latam_document_type_id.code)['invoice_number']})

        # WSFE_10151 send cuit of the issuer if type mipyme refund
        if self._is_mipyme_fce_refund() or afip_ws == 'wsfex':
            res.update({wskey[afip_ws]['cuit']: related_inv.company_id.partner_id._get_id_number_sanitize()})

        # WSFE_10158 send orignal invoice date on an mipyme document
        if afip_ws == 'wsfe' and (self._is_mipyme_fce() or self._is_mipyme_fce_refund()):
            res.update({wskey[afip_ws]['date']: related_inv.invoice_date.strftime(WS_DATE_FORMAT[afip_ws])})

        return res
