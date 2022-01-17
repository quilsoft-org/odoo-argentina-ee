# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, RedirectWarning
import logging
_logger = logging.getLogger(__name__)


class L10nArAfipwsCaea(models.Model):
    _name = 'l10n_ar.afipws.caea'
    _description = 'Caea registry'
    _order = "date_from desc"
    _sql_constraints = [
        ('unique_caea', 'unique (company_id,name)', 'CAEA already exists!'),
        ('unique_caea', 'unique (company_id,period, order)',
         'CAEA request already exists!')
    ]

    name = fields.Char(
        string='CAEA',
        default='/'
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    period = fields.Char(
        string='Period',
        size=6,
        required=True,
    )
    year = fields.Integer(
        string='Year',
        required=True,
    )
    month = fields.Selection(
        [
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            ('04', 'April'),
            ('05', 'May'),
            ('06', 'June'),
            ('07', 'July'),
            ('08', 'August'),
            ('09', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
        ],
        string='Month',
        required=True,
    )
    order = fields.Selection(
        [('1', 'first Fortnight'), ('2', 'second Fortnight')],
        string='Fortnight',
        required=True,
    )

    afip_observations = fields.Text(
        string='Observations',
    )
    afip_errors = fields.Text(
        string='Errors',
    )
    date_from = fields.Date(
        string='from',
        compute="_compute_date",
        store=True,
    )
    date_to = fields.Date(
        string='to',
        compute="_compute_date",
        store=True,
    )
    move_ids = fields.One2many(
        'account.move',
        'caea_id',
        string='Moves',
    )

    @api.onchange('month', 'year')
    def _onchange_month_year(self):
        if self.year and self.month:
            self.period = str(self.year) + self.month

    @api.depends('month', 'year')
    def _compute_date(self):
        for caea in self:
            if caea.year and caea.month:
                if caea.order == '1':
                    caea.date_from = fields.Date.from_string(
                        "%s-%s-01" % (caea.year, caea.month))
                    caea.date_to = fields.Date.from_string(
                        "%s-%s-15" % (caea.year, caea.month))
                else:
                    caea.date_from = fields.Date.from_string(
                        "%s-%s-16" % (caea.year, caea.month))
                    caea.date_to = fields.Date.from_string(
                        "%s-%s-1" % (caea.year, caea.month)) + relativedelta(months=1) - relativedelta(days=1)

    def action_request_caea(self):
        self.ensure_one()
        client, auth, transport = self.company_id._l10n_ar_get_connection(
            'wsfe')._get_client(return_transport=True)
        caea = self._l10n_ar_do_afip_ws_request_caea(client, auth, transport)
        self.name = caea['CAEA']
        self.afip_observations = caea['Observaciones']

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['period'] = str(vals['year']) + vals['month']

        res = super().create(vals_list)

        for afipws_caea in res:
            afipws_caea.action_request_caea()
        return res

    def write(self, vals):
        if 'year' in vals or 'month' in vals:
            year = vals.get('year', self.year)
            month = vals.get('month', self.month)
            vals['period'] = str(year) + month
        super().write(vals)

    def _l10n_ar_do_afip_ws_request_caea(self, client, auth, transport, ws_method='FECAEASolicitar'):
        self.ensure_one()
        try:
            client.create_message(client.service, ws_method,
                                  auth, Orden=self.order, Periodo=self.period)
        except Exception as error:
            raise UserError(repr(error))
        response = client.service[ws_method](
            auth, Orden=self.order, Periodo=self.period)
        if response['Errors']:
            if response['Errors']['Err'][0]['Code'] == 15008:
                response = self._l10n_ar_do_afip_ws_request_caea(
                    client, auth, transport, 'FECAEAConsultar')
                return response
            else:
                raise UserError(repr(response['Errors']))
        if response['Events']:
            raise UserError(repr(response['Events']))

        return response['ResultGet']

    def _get_client(self, return_transport=False):
        if return_transport:
            return False, False, False
        return False, False


    # informar caea
    # FECAEARegInformativo

    """def send_caea_invoices(self):
        self.env['ir.config_parameter'].set_param(
            'afip.ws.caea.state', 'inactive')

        move_ids = self.env['account.move'].search([
            ('afip_auth_mode', '=', 'CAEA'),
            ('afip_auth_code', '=', self.afip_caea)
        ], order='name asc')
        out_invoice = move_ids.filtered(lambda i: i.type in ['out_invoice'])
        out_refund = move_ids.filtered(lambda i: i.type in ['out_refund'])
        for inv in out_invoice:
            inv.do_pyafipws_request_cae()
        for inv in out_refund:
            inv.do_pyafipws_request_cae()

    def cron_request_caea(self):
        request_date = fields.Date.today() + relativedelta(days=7)
        period = request_date.strftime('%Y%m')
        order = '1' if request_date.day < 16 else '2'

        company_ids = self.env['res.company'].search([('use_caea', '=', True)])
        for company_id in company_ids:
            caea = self.search([
                ('name', '=', period),
                ('order', '=', order),
                ('company_id', '=', company_id.id),
            ])

            if not len(caea):
                self.create({
                    'name': period,
                    'order': order,
                    'company_id': company_id.id
                })

    def cron_caea_timeout(self):
        state = self.env['ir.config_parameter'].get_param(
            'afip.ws.caea.state', 'inactive')
        if state == 'active':
            timeout = int(self.env['ir.config_parameter'].get_param(
                'afip.ws.caea.timeout', 2))
            threshold = fields.Datetime.from_string(
                fields.Datetime.now()) - relativedelta(minutes=int(timeout * 60))
            log = self.env['afipws.caea.log'].search_count([
                ('event', '=', 'start_caea'),
                ('event_datetime', '>', threshold)
            ], order='event_datetime DESC')
            if log < 1:
                self.env['ir.config_parameter'].set_param(
                    'afip.ws.caea.state', 'inactive')
                self.env['afipws.caea.log'].create([
                    {'event': 'end_caea', 'user_id': self.env.user.id}
                ])

    def cron_send_caea_invoices(self):

        self.env['ir.config_parameter'].set_param(
            'afip.ws.caea.state', 'inactive')
        caea_ids = self.search([
            ('date_from', '<=',  fields.Date.today() + relativedelta(days=1)),
            ('date_to', '>=',  fields.Date.today() + relativedelta(days=1))
        ])
        caea_ids.send_caea_invoices()"""


class L10nArAfipwsCaeaLog(models.Model):

    _name = 'l10n_ar.afipws.caea.log'
    _description = 'afipws caea log'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user.id
    )
    event_datetime = fields.Datetime(
        string='Datetime',
        default=lambda self: fields.Datetime.now()
    )
    event = fields.Selection(
        [('request', 'request'),
         ('start_caea', 'start caea mode'),
         ('end_caea', 'end caea mode')
         ],
        string='Event',
    )
