from odoo import models , fields



class ResPartner(models.Model):
    _inherit = 'res.partner'

    ordertech_customer_id = fields.Char(readonly=True)
