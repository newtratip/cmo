# -*- coding: utf-8 -*-

from openerp import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
