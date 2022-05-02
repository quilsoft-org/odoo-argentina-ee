# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class L10nArAfipwsDummy(models.TransientModel):
    _name = 'l10n_ar.afipws.dummy'
    _description = 'AFIP dummy'

    def _default_afip_ws_caea_state(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'afip.ws.caea.state', 'inactive')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company.id
    )

    use_caea = fields.Boolean(
        string='Allow contingency billing',
        related="company_id.use_caea"
    )    

    afip_ws = fields.Char(
        string='AFIP WS',
        default=lambda self: self.get_afip_ws()
    )

    afip_ws_caea_state = fields.Selection(
        [('inactive', 'Using WS'), ('active', 'In contingency mode')],
        string='AFIP enviroment type',
        compute='_compute_afip_ws_caea_state',
        default=lambda self: self._default_afip_ws_caea_state()
    )

    app_server_status = fields.Boolean(
        string='App Server Status',
        # readonly=True,
    )
    db_server_status = fields.Boolean(
        string='DB Server Status',
        # readonly=True,
    )
    auth_server_status = fields.Boolean(
        string='auth Server Status',
        # readonly=True,
    )
    status = fields.Boolean(
        string='AFIP status',
    )

    def get_afip_ws(self):
        return 'wsfe'

    @api.onchange('app_server_status', 'db_server_status', 'auth_server_status')
    def _onchange_status(self):
        self.status = self.app_server_status and self.db_server_status and self.auth_server_status

    @api.onchange('afip_ws')
    def _onchange_afip_ws(self):
        ws_method = 'FEDummy'

        try:
            client, auth, transport = self.company_id.with_context(ignore_active_caea=True)._l10n_ar_get_connection(
                self.afip_ws)._get_client(return_transport=True)
            client.create_message(client.service, ws_method)
            response = client.service[ws_method]()
            self.write({'app_server_status': True if response.AppServer == 'OK' else False,
                        'db_server_status': True if response.DbServer == 'OK' else False,
                        'auth_server_status': True if response.AuthServer == 'OK' else False,
                        })
        except Exception as e:
            _logger.error(e)
            self.write({'app_server_status': False,
                        'db_server_status': False,
                        'auth_server_status': False,
                        'status': False
                        })

    def _compute_afip_ws_caea_state(self):
        self.afip_ws_caea_state = self.env['ir.config_parameter'].sudo().get_param(
            'afip.ws.caea.state', 'inactive')

    def afip_green_button(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'afip.ws.caea.state', 'inactive')
        self.env['l10n_ar.afipws.caea.log'].sudo().create([
            {'event': 'end_caea', 'user_id': self.env.user.id}
        ])

    def afip_red_button(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'afip.ws.caea.state', 'active')
        self.env['l10n_ar.afipws.caea.log'].sudo().create([
            {'event': 'start_caea', 'user_id': self.env.user.id}
        ])
