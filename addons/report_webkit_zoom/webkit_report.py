# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 CodUP (<http://codup.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import subprocess
import os
import tempfile
import time
from openerp.tools.translate import _
from openerp.osv.osv import except_osv
from openerp.addons.report_webkit.webkit_report import WebKitParser

import logging
_logger = logging.getLogger(__name__)

def generate_pdf(self, comm_path, report_xml, header, footer, html_list, webkit_header=False):
    """Call webkit in order to generate pdf"""
    if not webkit_header:
        webkit_header = report_xml.webkit_header
    tmp_dir = tempfile.gettempdir()
    out_filename = tempfile.mktemp(suffix=".pdf", prefix="webkit.tmp.")
    file_to_del = [out_filename]
    if comm_path:
        command = [comm_path]
    else:
        command = ['wkhtmltopdf']

    command.append('--quiet')
    # default to UTF-8 encoding.  Use <meta charset="latin-1"> to override.
    command.extend(['--encoding', 'utf-8'])
    if header :
        head_file = file( os.path.join(
                              tmp_dir,
                              str(time.time()) + '.head.html'
                             ),
                            'w'
                        )
        head_file.write(header)
        head_file.close()
        file_to_del.append(head_file.name)
        command.extend(['--header-html', head_file.name])
    if footer :
        foot_file = file(  os.path.join(
                              tmp_dir,
                              str(time.time()) + '.foot.html'
                             ),
                            'w'
                        )
        foot_file.write(footer)
        foot_file.close()
        file_to_del.append(foot_file.name)
        command.extend(['--footer-html', foot_file.name])

    if webkit_header.scale :
        command.extend(['--zoom', str(webkit_header.scale).replace(',', '.')])
    if webkit_header.margin_top :
        command.extend(['--margin-top', str(webkit_header.margin_top).replace(',', '.')])
    if webkit_header.margin_bottom :
        command.extend(['--margin-bottom', str(webkit_header.margin_bottom).replace(',', '.')])
    if webkit_header.margin_left :
        command.extend(['--margin-left', str(webkit_header.margin_left).replace(',', '.')])
    if webkit_header.margin_right :
        command.extend(['--margin-right', str(webkit_header.margin_right).replace(',', '.')])
    if webkit_header.orientation :
        command.extend(['--orientation', str(webkit_header.orientation).replace(',', '.')])
    if webkit_header.format :
        command.extend(['--page-size', str(webkit_header.format).replace(',', '.')])
    count = 0
    for html in html_list :
        html_file = file(os.path.join(tmp_dir, str(time.time()) + str(count) +'.body.html'), 'w')
        count += 1
        html_file.write(html)
        html_file.close()
        file_to_del.append(html_file.name)
        command.append(html_file.name)
    command.append(out_filename)
    stderr_fd, stderr_path = tempfile.mkstemp(text=True)
    file_to_del.append(stderr_path)
    try:
        status = subprocess.call(command, stderr=stderr_fd)
        os.close(stderr_fd) # ensure flush before reading
        stderr_fd = None # avoid closing again in finally block
        fobj = open(stderr_path, 'r')
        error_message = fobj.read()
        fobj.close()
        if not error_message:
            error_message = _('No diagnosis message was provided')
        else:
            error_message = _('The following diagnosis message was provided:\n') + error_message
        if status :
            raise except_osv(_('Webkit error' ),
                             _("The command 'wkhtmltopdf' failed with error code = %s. Message: %s") % (status, error_message))
        pdf_file = open(out_filename, 'rb')
        pdf = pdf_file.read()
        pdf_file.close()
    finally:
        if stderr_fd is not None:
            os.close(stderr_fd)
        for f_to_del in file_to_del:
            try:
                os.unlink(f_to_del)
            except (OSError, IOError), exc:
                _logger.error('cannot remove file %s: %s', f_to_del, exc)
    return pdf

WebKitParser.generate_pdf = generate_pdf

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: