from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    use_caea = fields.Boolean(
        string='Allow contingency billing',
        related='company_id.use_caea'
    )

    afip_ws_caea_state = fields.Selection(
        [('inactive', 'Using WS'), ('active', 'In contingency mode'),
         ('syncro', 'In AFIP syncro')],
        string='AFIP enviroment method',
        config_parameter='afip.ws.caea.state',
        default='inactive'
    )
    afip_ws_caea_timeout = fields.Float(
        string='Contingency timeout',
        config_parameter='afip.ws.caea.timeout',
        default=2
    )

    def afip_red_button(self):
        self.env['l10n_ar.afipws.caea.log'].create([
            {'event': 'start_caea', 'user_id': self.env.user.id}
        ])
        self.env['ir.config_parameter'].set_param('afip.ws.caea.state', 'active')

    def afip_green_button(self):
        self.env['l10n_ar.afipws.caea.log'].create([
            {'event': 'end_caea', 'user_id': self.env.user.id}
        ])
        self.env['ir.config_parameter'].set_param('afip.ws.caea.state', 'inactive')
