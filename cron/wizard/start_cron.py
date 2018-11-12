# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2014-2018 CodUP (<http://codup.com>).
#
##############################################################################

from odoo.service.server import ThreadedServer
from odoo import api, fields, models


class cron_start_cron(models.TransientModel):
    _name = 'cron.start.cron'
    _description = 'Start cron'

    def start_cron(self):
        ThreadedServer(None).cron_spawn()
        return {'type': 'ir.actions.act_window_close',}
