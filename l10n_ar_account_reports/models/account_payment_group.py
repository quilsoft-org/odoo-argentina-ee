    
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, tools, _
from odoo import models, api
import base64
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentGroup(models.Model):
    _inherit = 'account.payment.group'
    _description = 'Export csv'

    def export_csv(self): 
            return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment.group.export',
            'target': 'new',
            'context': {'active_id': self.id}
            }












