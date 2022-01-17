# -*- coding: utf-8 -*-
# from odoo import http


# class L10nArEdiCaea(http.Controller):
#     @http.route('/l10n_ar_edi_caea/l10n_ar_edi_caea/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ar_edi_caea/l10n_ar_edi_caea/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ar_edi_caea.listing', {
#             'root': '/l10n_ar_edi_caea/l10n_ar_edi_caea',
#             'objects': http.request.env['l10n_ar_edi_caea.l10n_ar_edi_caea'].search([]),
#         })

#     @http.route('/l10n_ar_edi_caea/l10n_ar_edi_caea/objects/<model("l10n_ar_edi_caea.l10n_ar_edi_caea"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ar_edi_caea.object', {
#             'object': obj
#         })
