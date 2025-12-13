from odoo import models,fields,api
from odoo.exceptions import UserError


class PosCategory(models.Model):
    _inherit = 'pos.category'

    company_id = fields.Many2one('res.company',default=lambda self:self.env.company.id)

    def sync_data_to_ordertech(self):
        pass