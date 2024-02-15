    
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, tools, _
from odoo import models, api
import base64
import logging
_logger = logging.getLogger(__name__)
# from l10n_ar_account_reports.models import account_payment_group

class AccountPaymentGroupExport(models.TransientModel):
    _name = 'account.payment.group.export'
    _description = 'Export csv'

    text_export = fields.Text("¿Desea exportar la orden corriente?")
    account_payment_group_id = fields.Many2one("account.payment.group",'account payment')
    csv_content = fields.Text(string="Contenido")
    csv_name = fields.Char(string="File Name", readonly=True)
    csv_file = fields.Binary(string="Descargar Archivo",
                             readonly=True, attachment=False)
    
    format = fields.Selection([('csv', 'CSV')], default='csv', readonly=True)
    csv_export_ejecutado = fields.Boolean(default=False)
    wizard_text=fields.Char("¿Desea crear registro de e-cheques en archivo csv?", readonly=True, compute="_compute_text")

    # def _compute_text(self):
    #     self.wizard_text =  "¿Desea crear registro de e-cheques en archivo csv?"

    

    def csv_export(self):
        self.csv_export_ejecutado = True
        active_ids = self._context.get('active_id', False)
        for rec in self:
            
            group_payment=self.env['account.payment.group'].search([('id', '=',active_ids)])
            _logger.info("LOGGER RECORD: %s,%s",group_payment,active_ids)
            # records_line=[]
            records_line = group_payment.payment_ids.filtered(lambda x: x.payment_method_code == 'issue_check' and 'electronic' in x.checkbook_id.issue_check_subtype)
            _logger.info("LOGGER RECORD: %s",records_line)
            self.env
            rec.ensure_one()
            this = rec[0]
            res = []
            column=[
                 "CUIT del Beneficiario","Importe","Multi_Echeq","Cantidad","Fecha de pago","Caracter","Cruzado","Concepto","Descripcion del Echeq"
            ]
            res.append(','.join(column))
            for line in records_line:
                    
                    # Campo 1 -> Cuit del partner
                    if group_payment.partner_id.vat:
                        cuit= str(group_payment.partner_id.vat)
                    else:
                            cuit= "El benificiario no posee CUIT"
                    # # Campo 2 -> Importe del cheque  
                    amount = str(line.amount)
                    Multi_Echeq = "NO"
                    quantity = "1"
                    _logger.info("LOGGER DATE,%s",line.check_payment_date)
                    if line.check_payment_date != False:
                        date_from = line.check_payment_date.strftime("%d/%m/%Y") 
                    else:
                        date_from= "No posee fecha de pago"
                    Caracter = "A la orden"
                    Cruzado= "SI"
                    Concept="FAC"
                    description=  "Pago facturas varias"
                      
                    row = [
                        # Campo 1 -> Cuit del partner
                        cuit,
                        # Campo 2 -> Fecha Emisión cheque
                        amount,
                        Multi_Echeq,
                        quantity,
                        date_from,                    
                        Caracter,
                        Cruzado,
                        Concept,
                        description,


                    ]

                    res.append(','.join(row))
            
            _logger.info("LOGGER RECORD: %s",res)         
           

            # res.append('\r\n')
            
            csv_content = '\r\n'.join(res)
            
    
            extension = this.format
            name = "echeq%s.%s" % (group_payment.name, extension)
            binary_content = base64.encodebytes(csv_content.encode('UTF-8'))

            this.write({'csv_content': csv_content, 'csv_name': name, 'csv_file': binary_content})
            _logger.info("LOGGER RETURN: %s,%s",rec.csv_name,rec.id)
            return {
                    'name': 'Descargar CSV para Aplicativos',
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.payment.group.export',
                    'view_mode': 'form',
                    'res_id': this.id,
                    'views': [(False, 'form')],
                    'target': 'new',
                    'view_id': 'payment_csv_order_view_export_form',
                }














