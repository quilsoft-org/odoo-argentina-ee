# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError

_logger = logging.getLogger(__name__)

# Pagina 118
# https://www.afip.gob.ar/fe/ayuda//documentos/Manual-desarrollador-V.2.21.pdf


class L10nArAfipwsCaea(models.Model):
    _name = "l10n_ar.afipws.caea"
    _description = "Caea registry"
    _order = "date_from desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    _sql_constraints = [
        ("unique_caea", "unique (company_id,name)", "CAEA already exists!"),
        (
            "unique_caea",
            "unique (company_id,period, order)",
            "CAEA request already exists!",
        ),
    ]

    state = fields.Selection(
        [("draft", "draft"), ("active", "active"), ("reported", "reported")],
        string="State",
        default="draft",
    )
    name = fields.Char(string="CAEA", default="/")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    period = fields.Char(
        string="Period",
        size=6,
        required=True,
    )
    year = fields.Integer(
        string="Year",
        required=True,
    )
    month = fields.Selection(
        [
            ("01", "January"),
            ("02", "February"),
            ("03", "March"),
            ("04", "April"),
            ("05", "May"),
            ("06", "June"),
            ("07", "July"),
            ("08", "August"),
            ("09", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month",
        required=True,
    )
    order = fields.Selection(
        [("1", "first Fortnight"), ("2", "second Fortnight")],
        string="Fortnight",
        required=True,
    )

    afip_observations = fields.Text(
        string="Observations",
    )
    afip_errors = fields.Text(
        string="Errors",
    )
    date_from = fields.Date(
        string="from",
        compute="_compute_date",
        store=True,
    )
    date_to = fields.Date(
        string="to",
        compute="_compute_date",
        store=True,
    )
    process_deadline = fields.Date(string="process deadline")

    move_ids = fields.One2many(
        "account.move",
        "caea_id",
        string="Moves",
    )
    journal_ids = fields.Many2many(
        "account.journal",
        string="Autorized CAEA journals",
    )

    def get_afip_ws(self):
        return "wsfe"

    @api.onchange("month", "year")
    def _onchange_month_year(self):
        if self.year and self.month:
            self.period = str(self.year) + self.month

    @api.depends("month", "year", "order")
    def _compute_date(self):
        for caea in self:
            if caea.year and caea.month:
                if caea.order == "1":
                    caea.date_from = fields.Date.from_string(
                        "%s-%s-01" % (caea.year, caea.month)
                    )
                    caea.date_to = fields.Date.from_string(
                        "%s-%s-15" % (caea.year, caea.month)
                    )
                elif caea.order == "2":
                    caea.date_from = fields.Date.from_string(
                        "%s-%s-16" % (caea.year, caea.month)
                    )
                    caea.date_to = (
                        fields.Date.from_string("%s-%s-1" % (caea.year, caea.month))
                        + relativedelta(months=1)
                        - relativedelta(days=1)
                    )

    def action_request_caea(self):
        self.ensure_one()
        afip_ws = self.get_afip_ws()

        client, auth, transport = self.company_id._l10n_ar_get_connection(
            afip_ws
        )._get_client(return_transport=True)
        result = self._l10n_ar_do_afip_ws_request_caea(client, auth, transport)
        self.name = result["CAEA"]
        self.process_deadline = datetime.strptime(result["FchTopeInf"], "%Y%m%d")
        if result.Observaciones:
            return_info = "".join(
                [
                    "\n* Code %s: %s" % (ob.Code, ob.Msg)
                    for ob in result.Observaciones.Obs
                ]
            )
            self.message_post(
                body="<p><b>"
                + _("AFIP Messages")
                + "</b></p><p><i>%s</i></p>" % (return_info)
            )
        self.state = "active"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["period"] = str(vals["year"]) + vals["month"]

        res = super().create(vals_list)

        for afipws_caea in res:
            afipws_caea.action_request_caea()
            afipws_caea.action_get_caea_pos()
        return res

    def write(self, vals):
        if "year" in vals or "month" in vals:
            year = vals.get("year", self.year)
            month = vals.get("month", self.month)
            vals["period"] = str(year) + month
        super().write(vals)

    def _l10n_ar_do_afip_ws_request_caea(
        self, client, auth, transport, ws_method="FECAEASolicitar"
    ):
        self.ensure_one()
        try:
            client.create_message(
                client.service, ws_method, auth, Orden=self.order, Periodo=self.period
            )
        except Exception as error:
            raise UserError(repr(error))
        response = client.service[ws_method](
            auth, Orden=self.order, Periodo=self.period
        )
        if response["Errors"]:
            if response["Errors"]["Err"][0]["Code"] == 15008:
                response = self._l10n_ar_do_afip_ws_request_caea(
                    client, auth, transport, "FECAEAConsultar"
                )
                return response
            else:
                raise UserError(repr(response["Errors"]))

        return response["ResultGet"]

    def report_no_invoices(self):
        self.ensure_one()
        afip_ws = self.get_afip_ws()
        connection = self.company_id._l10n_ar_get_connection(afip_ws)
        client, auth = connection._get_client()
        if afip_ws == "wsfe":
            # Update actives Journals
            self.action_get_caea_pos()
            journal_ids = (
                self.env["account.move"]
                .search(
                    [
                        ("journal_id", "in", self.journal_ids.ids),
                        ("caea_post_datetime", ">=", self.date_from),
                        ("caea_post_datetime", "<=", self.date_to),
                    ]
                )
                .mapped("journal_id")
            )

            no_invoices_journal_ids = self.journal_ids - journal_ids
            ws_method = "FECAEASinMovimientoInformar"

            return_info = ""
            for report_journal in no_invoices_journal_ids:
                request_data = {
                    "PtoVta": report_journal.l10n_ar_afip_pos_number,
                    "CAEA": self.name,
                }
                try:
                    client.create_message(client.service, ws_method, auth, request_data)
                except Exception as error:
                    raise UserError(repr(error))

                response = client.service[ws_method](
                    auth, PtoVta=report_journal.l10n_ar_afip_pos_number, CAEA=self.name
                )
                if response.Resultado == "A":
                    return_info += "<p><strong>POS %s</strong> %s</p>" % (
                        report_journal.l10n_ar_afip_pos_number,
                        _("Reported with no invoices successful"),
                    )
                else:
                    return_info += "<p><strong>POS %s</strong> %s</p>" % (
                        report_journal.l10n_ar_afip_pos_number,
                        _("Error cant reported with no invoices"),
                    )
                if response.Errors:
                    return_info += "".join(
                        [
                            "\n* Code %s: %s" % (err.Code, err.Msg)
                            for err in response.Errors.Err
                        ]
                    )

                if response.Events:
                    return_info += "".join(
                        [
                            "\n* Code %s: %s" % (evt.Code, evt.Msg)
                            for evt in response.Events.Evt
                        ]
                    )

            self.message_post(
                body="<p><b>"
                + _("AFIP Messages")
                + "</b></p><p><i>%s</i></p>" % (return_info)
            )
            self.state = "reported"

        else:
            raise UserError(
                _(
                    '"Check Available AFIP PoS" is not implemented for webservice %s',
                    self.l10n_ar_afip_ws,
                )
            )

    def action_get_caea_pos(self):
        self.ensure_one()
        afip_ws = self.get_afip_ws()
        connection = self.company_id._l10n_ar_get_connection(afip_ws)
        client, auth = connection._get_client()
        if afip_ws == "wsfe":
            response = client.service.FEParamGetPtosVenta(auth)
            pos_numbers = []
            if response.ResultGet:
                journal_ids = False
                for pdv in response.ResultGet.PtoVenta:
                    if pdv.EmisionTipo.startswith("CAEA") and pdv.Bloqueado == "N":
                        pos_numbers.append(int(pdv["Nro"]))
                if len(pos_numbers):
                    journal_ids = self.env["account.journal"].search(
                        [("l10n_ar_afip_pos_number", "in", pos_numbers)]
                    )
                if len(journal_ids):
                    self.journal_ids = [(6, 0, journal_ids.ids)]
        else:
            raise UserError(
                _(
                    '"Check Available AFIP PoS" is not implemented for webservice %s',
                    self.l10n_ar_afip_ws,
                )
            )

    def _get_client(self, return_transport=False):
        if return_transport:
            return False, False, False
        return False, False

    def _ws_verify_request_data(self, client, auth, ws_method, request_data):
        """Validate that all the request data sent is ok"""
        try:
            client.create_message(client.service, ws_method, auth, request_data)
        except Exception as error:
            raise UserError(repr(error))

    def _l10n_ar_do_afip_ws_report_invoice(self, move_ids, client, auth, transport):
        self.ensure_one()
        afip_ws = self.get_afip_ws()
        for inv in move_ids:
            if afip_ws == "wsfe":
                ws_method = "FECAEARegInformativo"
                return_codes = []
                errors = ""
                events = ""
                obs = ""
                request_data = inv.wsfe_get_caea_request(self.name, client)
                self._ws_verify_request_data(client, auth, ws_method, request_data)
                response = client.service[ws_method](auth, request_data)
                if response.FeDetResp:
                    result = response.FeDetResp.FECAEADetResponse[0]
                    if result.Observaciones:
                        obs = "".join(
                            [
                                "\n* Code %s: %s" % (ob.Code, ob.Msg)
                                for ob in result.Observaciones.Obs
                            ]
                        )
                        return_codes += [
                            str(ob.Code) for ob in result.Observaciones.Obs
                        ]
                    if result.Resultado == "A":
                        values = {
                            "l10n_ar_afip_auth_mode": "CAEA",
                            "l10n_ar_afip_caea_reported": True,
                            "l10n_ar_afip_auth_code": result.CAEA
                            and str(result.CAEA)
                            or "",
                            "l10n_ar_afip_result": result.Resultado,
                        }

                    if result.Resultado == "R":
                        values = {"l10n_ar_afip_result": result.Resultado}
                if response.Errors:
                    errors = "".join(
                        [
                            "\n* Code %s: %s" % (err.Code, err.Msg)
                            for err in response.Errors.Err
                        ]
                    )
                    return_codes += [str(err.Code) for err in response.Errors.Err]
                if response.Events:
                    events = "".join(
                        [
                            "\n* Code %s: %s" % (evt.Code, evt.Msg)
                            for evt in response.Events.Evt
                        ]
                    )
                    return_codes += [str(evt.Code) for evt in response.Events.Evt]

            return_info = inv._prepare_return_msg(
                afip_ws, errors, obs, events, return_codes
            )
            afip_result = values.get("l10n_ar_afip_result")
            xml_response, xml_request = transport.xml_response, transport.xml_request

            if afip_result not in ["A", "O"]:
                if not self.env.context.get("l10n_ar_invoice_skip_commit"):
                    self.env.cr.rollback()
                    # levantamos una excepcion para que no siga informando facturas
                    # porque ya sabemos que todas van a dar error al faltar esta no van
                    # a coincidir los números
                    raise UserError(_("Afip devuelve error al validar factura."))

                if inv.exists():
                    # Only save the xml_request/xml_response fields if the invoice exists.
                    # It is possible that the invoice will rollback as well e.g. when it is automatically created when:
                    #   * creating credit note with full reconcile option
                    #   * creating/validating an invoice from subscription/sales
                    inv.sudo().write(
                        {
                            "l10n_ar_afip_xml_request": xml_request,
                            "l10n_ar_afip_xml_response": xml_response,
                        }
                    )
                    if not self.env.context.get("l10n_ar_invoice_skip_commit"):
                        self.env.cr.commit()
                    if return_info:
                        inv.message_post(
                            body="<p><b>"
                            + _("AFIP Messages")
                            + "</b></p><p><i>%s</i></p>" % (return_info)
                        )

                return return_info
            values.update(
                l10n_ar_afip_xml_request=xml_request,
                l10n_ar_afip_xml_response=xml_response,
            )
            inv.sudo().write(values)
            # salvamos a BD una a una las facturas validadas para que si falla alguna
            # y me hace rollback tendremos en odoo lo mismo que en afip.
            self.env.cr.commit()

            if return_info:
                inv.message_post(
                    body="<p><b>"
                    + _("AFIP Messages")
                    + "</b></p><p><i>%s</i></p>" % (return_info)
                )
            return return_info

    def action_send_invoices(self):
        self.env["ir.config_parameter"].set_param("afip.ws.caea.state", "inactive")

        move_ids = self.move_ids.filtered(
            lambda m: m.l10n_ar_afip_caea_reported is False
        )

        afip_ws = self.get_afip_ws()
        return_info_all = []
        for inv in move_ids.sorted(key=lambda r: r.caea_post_datetime):
            client, auth, transport = inv.company_id._l10n_ar_get_connection(
                afip_ws
            )._get_client(return_transport=True)
            return_info = self._l10n_ar_do_afip_ws_report_invoice(
                inv, client, auth, transport
            )
            if return_info and len(return_info):

                return_info_all.append(
                    "<strong>%s</strong> %s" % (inv.name, return_info)
                )
        if len(return_info_all):
            self.message_post(
                body="<p><b>"
                + _("AFIP Messages")
                + "</b></p><p><ul><li>%s</li></ul></p>"
                % ("</li><li>".join(return_info_all))
            )

    def cron_request_caea(self):
        """ Llammado desde cron verifica si se requiere pedir a la afip un nuevo
        certificado para CAEA lo hace si estamos 7 dias antes de la quincena y si
        no esta otorgado esto es para cada compañia """

        request_date = fields.Date.today() + relativedelta(days=7)
        period = request_date.strftime("%Y%m")
        year = request_date.strftime("%Y")
        month = request_date.strftime("%m")
        order = "1" if request_date.day < 16 else "2"

        company_ids = self.env["res.company"].search([("use_caea", "=", True)])
        for company_id in company_ids:
            caea = self.search(
                [
                    ("name", "=", period),
                    ("order", "=", order),
                    ("company_id", "=", company_id.id),
                ]
            )

            if not len(caea):
                self.create(
                    {
                        "name": period,
                        "order": order,
                        "company_id": company_id.id,
                        "year": int(year),
                        "month": month,
                    }
                )

    def cron_caea_timeout(self):
        """ Llamado desde cron vigila que el estado de contingencia no dure mas de
        dos horas """

        state = self.env["ir.config_parameter"].get_param(
            "afip.ws.caea.state", "inactive"
        )
        if state == "active":
            timeout = float(
                self.env["ir.config_parameter"].get_param("afip.ws.caea.timeout", 2)
            )
            threshold = fields.Datetime.now() - relativedelta(minutes=int(timeout * 60))
            log = self.env["l10n_ar.afipws.caea.log"].search_count(
                [("event", "=", "start_caea"), ("event_datetime", ">", threshold)],
            )
            if log < 1:
                self.env["ir.config_parameter"].set_param(
                    "afip.ws.caea.state", "inactive"
                )
                self.env["l10n_ar.afipws.caea.log"].create(
                    [{"event": "end_caea", "user_id": self.env.user.id}]
                )

    def cron_send_caea_invoices(self):
        """ Llamado desde cron informa las facturas que se hicieron en modo de
            contingencia, esto debe correrse a la noche """

        caea_ids = self.search(
            [
                ("date_from", "<=", fields.Date.today() + relativedelta(days=1)),
                ("date_to", ">=", fields.Date.today() + relativedelta(days=1)),
                ("state", "=", "active"),
            ]
        )
        for caea_id in caea_ids:
            caea_id.action_send_invoices()

    def cron_close_caea(self):
        """ Llamado desde cron cierra los certificados CAEA al finalizar el periodo se
            hace esto por cada compañia"""

        raise NotImplemented('todavia no esta implementado')

        company_ids = self.env["res.company"].search([("use_caea", "=", True)])
        for company_id in company_ids:
            caea = self.search(
                [
                    ("name", "=", period),
                    ("state", "=", 'active'),
                    ("company_id", "=", company_id.id),
                ]
            )


class L10nArAfipwsCaeaLog(models.Model):

    _name = "l10n_ar.afipws.caea.log"
    _description = "afipws caea log"

    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user.id
    )
    event_datetime = fields.Datetime(
        string="Datetime", default=lambda self: fields.Datetime.now()
    )
    event = fields.Selection(
        [
            ("request", "request"),
            ("start_caea", "start caea mode"),
            ("end_caea", "end caea mode"),
        ],
        string="Event",
    )
