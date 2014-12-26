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
import openerp
from openerp.modules.module import get_module_resource
from functools import partial
from openerp.tools.translate import _
from openerp.osv.osv import except_osv
from openerp.addons.report_webkit.webkit_report import WebKitParser, mako_template, _extender_functions
from openerp.addons.report_webkit.report_helper import WebKitHelper

import logging
_logger = logging.getLogger(__name__)

# override needed to keep the attachments storing procedure
def create_single_pdf(self, cursor, uid, ids, data, report_xml, context=None):
    """generate the PDF"""

    # just try to find an xml id for the report
    cr = cursor
    pool = openerp.registry(cr.dbname)
    found_xml_ids = pool["ir.model.data"].search(cr, uid, [["model", "=", "ir.actions.report.xml"], \
        ["res_id", "=", report_xml.id]], context=context)
    xml_id = None
    if found_xml_ids:
        xml_id = pool["ir.model.data"].read(cr, uid, found_xml_ids[0], ["module", "name"])
        xml_id = "%s.%s" % (xml_id["module"], xml_id["name"])

    if context is None:
        context={}
    htmls = []
    if report_xml.report_type != 'webkit':
        return super(WebKitParser,self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)

    parser_instance = self.parser(cursor,
                                  uid,
                                  self.name2,
                                  context=context)

    self.pool = pool
    objs = self.getObjects(cursor, uid, ids, context)
    parser_instance.set_context(objs, data, ids, report_xml.report_type)

    template =  False

    if report_xml.report_file :
        path = get_module_resource(*report_xml.report_file.split('/'))
        if path and os.path.exists(path) :
            template = unicode(file(path).read(),'UTF-8')
    if not template and report_xml.report_webkit_data :
        template =  report_xml.report_webkit_data
    if not template :
        raise except_osv(_('Error!'), _('Webkit report template not found!'))
    header = report_xml.webkit_header.html
    footer = report_xml.webkit_header.footer_html
    if not header and report_xml.use_global_header:
        raise except_osv(
              _('No header defined for this Webkit report!'),
              _('Please set a header in company settings.')
          )
    if not report_xml.use_global_header :
        header = ''
        default_head = get_module_resource('report_webkit', 'default_header.html')
        with open(default_head,'r') as f:
            header = f.read()
    css = report_xml.webkit_header.css
    if not css :
        css = ''

    translate_call = partial(self.translate_call, parser_instance)
    body_mako_tpl = mako_template(template)
    helper = WebKitHelper(cursor, uid, report_xml.id, context)
    parser_instance.localcontext['helper'] = helper
    parser_instance.localcontext['css'] = css
    parser_instance.localcontext['_'] = translate_call
    parser_instance.localcontext['context'] = context

    # apply extender functions
    additional = {}
    if xml_id in _extender_functions:
        for fct in _extender_functions[xml_id]:
            fct(pool, cr, uid, parser_instance.localcontext, context)

    if report_xml.precise_mode:
        ctx = dict(parser_instance.localcontext)
        for obj in parser_instance.localcontext['objects']:
            ctx['objects'] = [obj]
            try :
                html = body_mako_tpl.render(dict(ctx))
                htmls.append(html)
            except Exception, e:
                msg = u"%s" % e
                _logger.error(msg)
                raise except_osv(_('Webkit render!'), msg)
    else:
        try :
            html = body_mako_tpl.render(dict(parser_instance.localcontext))
            htmls.append(html)
        except Exception, e:
            msg = u"%s" % e
            _logger.error(msg)
            raise except_osv(_('Webkit render!'), msg)
    head_mako_tpl = mako_template(header)
    try :
        head = head_mako_tpl.render(dict(parser_instance.localcontext, _debug=False))
    except Exception, e:
        raise except_osv(_('Webkit render!'), u"%s" % e)
    foot = False
    if footer :
        foot_mako_tpl = mako_template(footer)
        try :
            foot = foot_mako_tpl.render(dict(parser_instance.localcontext))
        except Exception, e:
            msg = u"%s" % e
            _logger.error(msg)
            raise except_osv(_('Webkit render!'), msg)
    if report_xml.webkit_debug :
        try :
            deb = head_mako_tpl.render(dict(parser_instance.localcontext, _debug=tools.ustr("\n".join(htmls))))
        except Exception, e:
            msg = u"%s" % e
            _logger.error(msg)
            raise except_osv(_('Webkit render!'), msg)
        return (deb, 'html')
    bin = self.get_lib(cursor, uid)
    pdf = self.generate_pdf(bin, report_xml, head, foot, htmls)
    return (pdf, 'pdf')


def generate_pdf(self, comm_path, report_xml, header, footer, html_list, webkit_header=False):
    """Call webkit in order to generate pdf"""
    if not webkit_header:
        webkit_header = report_xml.webkit_header
    fd, out_filename = tempfile.mkstemp(suffix=".pdf",
                                        prefix="webkit.tmp.")
    file_to_del = [out_filename]
    if comm_path:
        command = [comm_path]
    else:
        command = ['wkhtmltopdf']

    command.append('--quiet')
    # default to UTF-8 encoding.  Use <meta charset="latin-1"> to override.
    command.extend(['--encoding', 'utf-8'])
    if header :
        with tempfile.NamedTemporaryFile(suffix=".head.html",
                                         delete=False) as head_file:
            head_file.write(self._sanitize_html(header.encode('utf-8')))
        file_to_del.append(head_file.name)
        command.extend(['--header-html', head_file.name])
    if footer :
        with tempfile.NamedTemporaryFile(suffix=".foot.html",
                                         delete=False) as foot_file:
            foot_file.write(self._sanitize_html(footer.encode('utf-8')))
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
        with tempfile.NamedTemporaryFile(suffix="%d.body.html" %count,
                                         delete=False) as html_file:
            count += 1
            html_file.write(self._sanitize_html(html.encode('utf-8')))
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
        with open(out_filename, 'rb') as pdf_file:
            pdf = pdf_file.read()
        os.close(fd)
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
WebKitParser.create_single_pdf = create_single_pdf

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: