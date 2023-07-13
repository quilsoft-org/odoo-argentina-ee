from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_caea = fields.Boolean(
        string='Allow contingency billing',
    )

    def get_active_caea(self):
        self.ensure_one()
        today = fields.Date.today()
        return self.env['l10n_ar.afipws.caea'].search([
            ('company_id', '=', self.id),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
            ('state', '=', 'active')
        ], limit=1)

    def _l10n_ar_get_connection(self, afip_ws):
        caea_state = self.env['ir.config_parameter'].sudo().get_param(
            'afip.ws.caea.state', 'inactive')        
        if caea_state == 'active' and 'ignore_active_caea' not in self.env.context:
            return self.get_active_caea()

        return super()._l10n_ar_get_connection(afip_ws)

    def get_caea_afip_ws(self):
        return 'wsfe'
