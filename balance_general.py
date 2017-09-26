# -*- coding: utf-8 -*-

#from openerp import addons
from openerp import models, fields, api, _
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta
from datetime import date
import math

####### TRABAJAR CON LOS EXCEL
import base64
import xlsxwriter
import tempfile
from xlsxwriter.utility import xl_rowcol_to_cell


##### SOLUCIONA CUALQUIER ERROR DE ENCODING (CARACTERES ESPECIALES)
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class account_monthly_balance(models.Model):
	_inherit = 'account.monthly_balance'

####################################
#  CAMPOS PARA GENERAR EL ARCHIVO  #
####################################
	datas_fname = fields.Char('File Name',size=256)
	file = fields.Binary('Link de descarga')
	download_file = fields.Boolean('Descargar Archivo', default=False)
	cadena_decoding = fields.Text('Binario sin encoding')


###################################
#  METODOS PARA EXPORTAR A EXCEL  #  '2017-09-25 14:05:47'
###################################
	@api.multi
	def get_report_data(self,account_codes_lst):
		print 'CREATE_DATE: ', self.create_date, 'PERIOD_NAME: ', self.period_name
		print 'ACCOUNTS: ', account_codes_lst
		self = self.env['account.monthly_balance'].search([('period_name', '=', self.period_name),\
			('create_date', '>=', self.create_date),\
			('account_code', 'in', account_codes_lst)])

		return self

	@api.multi
	def get_report_lines_bg(self, account_codes_lst):
		self = self.get_report_data(account_codes_lst)
		values=[]
		cuenta_valor = []
		if self:
			for item in self:
				cuenta_valor = (item.account_code,int(round(item.ending_balance)))
				values.append(cuenta_valor)
			return values
		
	@api.multi
	def get_report_lines_er(self, account_codes_lst):
		self = self.get_report_data(account_codes_lst)
		values=[]
		cuenta_valor = []
		if self:
			for item in self:
				cuenta_valor = (item.account_code,item.account_name,int(round(item.balance)),int(round(item.ending_balance)))
				values.append(cuenta_valor)
			return values

	@api.multi
	def balance_general(self):
		"""METODO LLAMADO DEL BOTON BALANCE GENERAL"""
		#SE OBTIENE LA INFO DEL FURMULARIO
		period_name = self.period_name
		company_name = self.account_id.company_id.name

		#SE OBTIENEN LAS LINEAS DEL REPORTE
		codes_list = [\
		#CUENTAS DEL ACTIVO CIRCULANTE
		'01H-1-01-01','01H-1-01-02','01H-1-01-03','01H-1-01-04','01H-1-01-05','01H-1-01-06','01H-1-01-08','01H-1-01-09','01H-1-01-10','01H-1-01-11','01H-1-01-12',\
		#CUENTAS DEL PASIVO CIRCULANTE
		'01H-2-01-01','01H-2-01-02','01H-2-01-03','01H-2-01-04','01H-2-01-05','01H-2-01-06',\
		#CUENTAS DEL ACTIVO FIJO
		'01H-1-02-01-01','01H-1-02-01-02','01H-1-02-01-03','01H-1-02-01-04','01H-1-02-01-05','01H-1-02-01-06','01H-1-02-01-07','01H-1-02-02',\
		#CUENTAS DEL PASIVO DIFERIDO
		'01H-2-03-01',\
		#CUENTAS DEL ACTIVO DIFERIDO
		'01H-1-02-03','01H-1-02-04','01H-1-03',\
		#CUENTAS DEL CAPTAL CONTABLE
		'01H-3-01','01H-3-02','01H-3-03','01H-3-04','01H-3-05','01H-6','01H-7']
		
		xlines = self.get_report_lines_bg(codes_list)


		#SE PREPARAN LOS VALORES DEL REPORTE
		vals = {
			'period_name' : period_name,
			'company_name' : company_name,
			'report_line_ids': [],
		}

		if not xlines:
			raise ValidationError(_('Error al generar el reporte, la consulta no ha arrojado datos \n Por el momento este reporte solo se encuentra disponible para el Consolidado'))
		else:
			for element in xlines:
				vals['report_line_ids'].append(element)

		return self.export_xlsx_balance_general(xlines, period_name, company_name)
		
	@api.multi
	def export_xlsx_balance_general(self, xlines, period_name, company_name):
		print 'export_xlsx_file_bal_gen'
		fname=tempfile.NamedTemporaryFile(suffix='.xlsx',delete=False)

		workbook = xlsxwriter.Workbook(fname)
		worksheet = workbook.add_worksheet('Balance General')

		# Widen the first column to make the text clearer.
		worksheet.set_column('A:A', 40)
		worksheet.set_column('B:B', 15)
		worksheet.set_column('C:C', 5)
		worksheet.set_column('D:D', 40)
		worksheet.set_column('E:E', 15)


		bold = workbook.add_format({'bold': True})

		#FORMATOS DE CELDA AZUL###########
		blue_bg =  workbook.add_format()
		blue_bg.set_font_color('white')
		blue_bg.set_bold()
		blue_bg.set_bg_color('blue')

		#FORMATOS DE CELDA GRIS###########
		light_gray = workbook.add_format()
		light_gray.set_font_color('black')
		light_gray.set_bold()
		light_gray.set_bg_color('#C0C0C0')

		#CELDAS NUMEROS
		number = workbook.add_format({'num_format': '#,##0'})
		number.set_font_color('black')
		
		#CELDAS NUMEROS FONDO GRIS
		light_gray_number = workbook.add_format({'num_format': '#,##0'})
		light_gray_number.set_font_color('black')
		light_gray_number.set_bold()
		light_gray_number.set_bg_color('#C0C0C0')

		#CELDAS NUMEROS FONDO AZUL
		blue_bg_number =  workbook.add_format({'num_format': '#,##0'})
		blue_bg_number.set_font_color('white')
		blue_bg_number.set_bold()
		blue_bg_number.set_bg_color('blue')


		report_title_style = workbook.add_format({'bold': True})
		report_title_style.set_font_size(12)


		report_title = 'Reporte de Balance General del periodo ' + period_name

		date = datetime.now().strftime('%d-%m-%Y')
		datas_fname = report_title+'_'+str(date)+".xlsx" # Nombre del Archivo

		#ENCABEZADO DEL REPORTE
		####################################################
		worksheet.write('A1', company_name.upper(),report_title_style)
		worksheet.write('A2', report_title,report_title_style)
		worksheet.write('A3', 'Fecha de impresion: ' + date,bold)
		##################################################################

		#ENCABEZADOS DE COLUMNAS
		worksheet.write(4, 0, 'CUENTA', blue_bg)
		worksheet.write(4, 1, 'IMPORTE', blue_bg)
		worksheet.write(4, 2, '', blue_bg)
		worksheet.write(4, 3, 'CUENTA', blue_bg)
		worksheet.write(4, 4, 'IMPORTE', blue_bg)
		
		#ACTIVO CIRCULANTE
		worksheet.write(6, 0, 'ACTIVO CIRCULANTE', light_gray)
		worksheet.write(8, 0, 'FONDO FIJO DE CAJA', '')
		worksheet.write(8, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-01'].pop()][1], number)
		worksheet.write(9, 0, 'BANCOS E INVERSIONES', '')
		worksheet.write(9, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-02'].pop()][1]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-03'].pop()][1], number)
		worksheet.write(10, 0, 'CUENTAS POR COBRAR A CLIENTES', '')
		worksheet.write(10, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-04'].pop()][1], number)
		worksheet.write(11, 0, 'PRESTACIONES LABORALES', '')
		worksheet.write(11, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-05'].pop()][1], number)
		worksheet.write(12, 0, 'DEUDORES DIVERSOS', '')
		worksheet.write(12, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-06'].pop()][1], number)
		worksheet.write(13, 0, 'IVA ACREDITABLE Y A FAVOR', '')
		worksheet.write(13, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-08'].pop()][1]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-09'].pop()][1], number)
		worksheet.write(14, 0, 'INVENTARIOS', '')
		worksheet.write(14, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-11'].pop()][1], number)
		worksheet.write(15, 0, 'ANTICIPOS A IMPUESTOS', '')
		worksheet.write(15, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-10'].pop()][1], number)
		worksheet.write(16, 0, 'ANTICIPOS A PROVEEDORES', '')
		worksheet.write(16, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-01-12'].pop()][1], number)

		#PASIVO CIRCULANTE
		worksheet.write(6, 3, 'PASIVO CIRCULANTE', light_gray)
		worksheet.write(8, 3, 'PROVEEDORES', '')
		worksheet.write(8, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-2-01-01'].pop()][1], number)
		worksheet.write(9, 3, 'ACREEDORES DIVERSOS', '')
		worksheet.write(9, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-2-01-02'].pop()][1], number)
		worksheet.write(10, 3, 'CREDITOS BANCARIOS POR PAGAR', '')
		worksheet.write(10, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-2-01-03'].pop()][1], number)
		worksheet.write(11, 3, 'IMPUESTOS Y APORTACIONES POR PAGAR', '')
		worksheet.write(11, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-2-01-04'].pop()][1], number)
		worksheet.write(12, 3, 'IVA TRASLADADO', '')
		worksheet.write(12, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-2-01-05'].pop()][1], number)
		worksheet.write(13, 3, 'ANTICIPOS DE CLIENTES', '')
		worksheet.write(13, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-2-01-06'].pop()][1], number)
		
		#TOTALES
		worksheet.write(18, 0, 'TOTAL ACTIVO CIRCULANTE', light_gray)
		worksheet.write_formula('B19', '=SUM(B9:B17)', light_gray_number)
		worksheet.write(18, 3, 'TOTAL PASIVO CIRCULANTE', light_gray)
		worksheet.write_formula('E19', '=SUM(E9:E14)', light_gray_number)
		
		#ACTIVO FIJO
		worksheet.write(20, 0, 'ACITO FIJO', light_gray)
		worksheet.write(22, 0, 'TERRENOS Y EDIFICIOS', '')
		worksheet.write(22, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-01-01'].pop()][1]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-01-02'].pop()][1], number)
		worksheet.write(23, 0, 'EQUIPO DE OFICINA Y COMPUTO', '')
		worksheet.write(23, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-01-03'].pop()][1]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-01-04'].pop()][1], number)
		worksheet.write(24, 0, 'EQUIPO DE TRANSPORTE Y AUTOMOVILES', '')
		worksheet.write(24, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-01-05'].pop()][1], number)
		worksheet.write(25, 0, 'GRUAS Y EQUIPOS DE CARGA', '')
		worksheet.write(25, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-01-06'].pop()][1], number)
		worksheet.write(26, 0, 'MAQUINARIA Y EQUIPOS', '')
		worksheet.write(26, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-01-07'].pop()][1], number)
		worksheet.write(27, 0, 'OBRAS EN PROCESO', '')
		worksheet.write(27, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-02'].pop()][1], number)

		#PASIVO DIFERIDO
		worksheet.write(20, 3, 'PASIVO DIFERIDO', light_gray)
		worksheet.write(22, 3, 'PASIVOS LABORALES', '')
		worksheet.write(22, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-2-03-01'].pop()][1], number)
		worksheet.write(24, 3, 'TOTAL PASIVO DIFERIDO', light_gray)
		worksheet.write_formula('E25', '=SUM(E23:E24)', light_gray_number)

		#TOTALES
		worksheet.write(29, 0, 'TOTAL ACTIVO FIJO', light_gray)
		worksheet.write_formula('B30', '=SUM(B23:B28)', light_gray_number)
		worksheet.write(29, 3, 'SUMA EL PASIVO', light_gray)
		worksheet.write_formula('E30', '=SUM(E19,E25)', light_gray_number)

		#ACTIVO DIFERIDO
		worksheet.write(31, 0, 'ACTIVO DIFERIDO', light_gray)
		worksheet.write(33, 0, 'IMPUESTOS A FAVOR', '')
		worksheet.write(33, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-03'].pop()][1], number)
		worksheet.write(34, 0, 'SEGUROS POR AMORTIZAR', '')
		worksheet.write(34, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-03'].pop()][1], number)
		worksheet.write(35, 0, 'DEPOSITOS EN GARANTIA', '')
		worksheet.write(35, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-1-02-04'].pop()][1], number)
		
		#CAPITAL CONTABLE
		worksheet.write(31, 3, 'CAPITAL CONTABLE', light_gray)
		worksheet.write(33, 3, 'CAPITAL SOCIAL POR APORTACION', '')
		worksheet.write(33, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-3-01'].pop()][1], number)
		worksheet.write(34, 3, 'ACTUALIZACION DE CAPITAL POR APORTACION', '')
		worksheet.write(34, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-3-02'].pop()][1], number)
		worksheet.write(35, 3, 'RESULTADOS DE EJERCICIOS ANTERIORES', '')
		worksheet.write(35, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-3-03'].pop()][1], number)
		worksheet.write(36, 3, 'RESULTADOS POR ACTUALIZACION', '')
		worksheet.write(36, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-3-05'].pop()][1], number)
		worksheet.write(37, 3, 'RESERVA LEGAL', '')
		worksheet.write(37, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-3-04'].pop()][1], number)
		worksheet.write(38, 3, 'UTILIDAD (PERDIDA) DEL EJERCICIO', '')
		worksheet.write(38, 4, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6'].pop()][1]-xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7'].pop()][1], number)

		#TOTALES
		worksheet.write(40, 0, 'TOTAL ACTIVO DIFERIDO', light_gray)
		worksheet.write_formula('B41', '=SUM(B34:B36)', light_gray_number)
		worksheet.write(40, 3, 'SUMA EL CAPITAL CONTABLE', light_gray)
		worksheet.write_formula('E41', '=SUM(E34:E39)', light_gray_number)

		#TOTALES GLOBALES
		worksheet.write(42, 0, 'SUMA EL ACTIVO', blue_bg)
		worksheet.write_formula('B43', '=SUM(B19,B30,B41)', blue_bg_number)
		worksheet.write(42, 3, 'SUMA PASIVO Y CAPITAL', blue_bg)
		worksheet.write_formula('E43', '=SUM(E30,E41)', blue_bg_number)


		workbook.close()
		f = open(fname.name, "r")
		data = f.read()
		f.close()

		
		self.write({'cadena_decoding':"",
			'datas_fname':datas_fname,
			'file':base64.encodestring(data),
			'download_file': True})
		print 'datas_fname: ',datas_fname
		# return {
		# 	'type': 'ir.actions.act_window',
		# 	'res_model': 'account.monthly_balance',
		# 	'view_mode': 'form',
		# 	'view_type': 'form',
		# 	'res_id': self.id,
		# 	'views': [(False, 'form')],
		# 	'target': 'new',
		# 	}

	@api.multi
	def estado_resultados(self):
		"""METODO LLAMADO DEL BOTON ESTADO DE RESULTADOS"""
		#SE OBTIENE LA INFO DEL FURMULARIO
		period_name = self.period_name
		company_name = self.account_id.company_id.name

		#SE OBTIENEN LAS LINEAS DEL REPORTE
		codes_list = [\
		#MARGEN DE CONTRIBUCION(INGRESOS)/
		#(COSTOS) 01B-6-03-01  
		'01H-6-01-01','01H-6-01-02','01H-6-03-01','01H-6-03-02','01H-6-02-01',\
		'01H-7-01-01-01','01H-7-01-02-01','01H-7-03-01-01','01H-7-03-02-01','01H-7-02-01-01',\
		#COSTOS FIJOS
		'01H-7-01-01','01H-7-01-01-01','01H-7-01-04','01H-7-01-02','01H-7-01-02-01','01H-7-01-03','01H-7-03','01H-7-02','01H-7-02-01-01',\
		#GASTOS DE OPERACION
		'01H-7-01-63','01H-7-01-64','01H-7-01-65','01H-7-01-66','01H-7-01-67','01H-7-01-68','01H-7-01-69',\
		#OTROS COSTOS FINANCIEROS
		'01H-6-01-04','01H-6-01-05','01H-6-02-02','01H-6-02-03','01H-6-03-04','01H-6-03-05','01H-6-01-06','01H-6-02-04',\
		'01H-7-01-60','01H-7-01-70','01H-7-01-70-05']

		xlines = self.get_report_lines_er(codes_list)


		#SE PREPARAN LOS VALORES DEL REPORTE
		vals = {
			'period_name' : period_name,
			'company_name' : company_name,
			'report_line_ids': [],
		}

		if not xlines:
			raise ValidationError(_('Error al generar el reporte, la consulta no ha arrojado datos \n Por el momento este reporte solo se encuentra disponible para el Consolidado'))
		else:
			for element in xlines:
				vals['report_line_ids'].append(element)

		return self.export_xlsx_estado_resultados(xlines, period_name, company_name)


	@api.multi
	def export_xlsx_estado_resultados(self, xlines, period_name, company_name):
		print 'export_xlsx_file_est_res'
		fname=tempfile.NamedTemporaryFile(suffix='.xlsx',delete=False)

		workbook = xlsxwriter.Workbook(fname)
		worksheet = workbook.add_worksheet('Estado de Resultados')

		# Widen the first column to make the text clearer.
		worksheet.set_column('A:A', 45)
		worksheet.set_column('B:D', 15)
		worksheet.set_column('E:E', 8)
		worksheet.set_column('F:H', 15)
		worksheet.set_column('I:I', 8)

		#FORMATOS DE CELDA AZUL###########
		bold = workbook.add_format({'bold': True})
		blue_bg =  workbook.add_format()
		blue_bg.set_font_color('white')
		blue_bg.set_bold()
		blue_bg.set_bg_color('blue')
		blue_bg.set_text_wrap()
		blue_bg.set_align('center')
		blue_bg.set_align('vcenter')

		#FORMATOS DE CELDA GRIS###########
		light_gray = workbook.add_format()
		light_gray.set_font_color('black')
		light_gray.set_bold()
		light_gray.set_bg_color('#C0C0C0')

		#FORMATOS DE CELDA BORDERS########
		border = workbook.add_format()
		border.set_border(1)
		border.set_bold()
		border.set_font_color('black')

		#FORMATO DE CELDA NEGRITAS#######
		bold = workbook.add_format()
		bold.set_bold()

		#CELDAS NUMEROS
		number = workbook.add_format({'num_format': '$#,##0'})
		number.set_font_color('black')

		#CELDAS NUMEROS PORCIENTO
		percentage = workbook.add_format({'num_format': '#0.00%'})
		percentage.set_font_color('black')
		
		#CELDAS NUMEROS NEGRITAS SIN BORDE
		number_bold_nb = workbook.add_format({'num_format': '$#,##0'})
		number_bold_nb.set_font_color('black')
		number_bold_nb.set_bold()

		#CELDAS NUMEROS NEGRITAS
		number_bold = workbook.add_format({'num_format': '$#,##0'})
		number_bold.set_font_color('black')
		number_bold.set_bold()
		number_bold.set_border(1)

		#FORMATO DE CELDA INVISIBLE#######
		invisible = workbook.add_format()
		invisible.set_font_color('white')

		report_title_style = workbook.add_format({'bold': True})
		report_title_style.set_font_size(12)


		report_title = 'Reporte de Estado de Resultados al periodo ' + period_name

		date = datetime.now().strftime('%d-%m-%Y')
		datas_fname = report_title+'_'+str(date)+".xlsx" # Nombre del Archivo

		#ENCABEZADO DEL REPORTE
		####################################################
		worksheet.write('A1', company_name.upper(),report_title_style)
		worksheet.write('A2', report_title,report_title_style)
		worksheet.write('A3', 'Fecha de impresion: ' + date,bold)
		#worksheet.write('B3', date,bold)
		##################################################################

		#ENCABEZADOS DE COLUMNAS
		worksheet.write(4, 0, 'CONCEPTO', blue_bg)
		worksheet.write(4, 1, 'DEL PERIODO INGRESOS', blue_bg)
		worksheet.write(4, 2, 'DEL PERIODO COSTOS', blue_bg)
		worksheet.write(4, 3, 'RESULTADO DEL PERIODO', blue_bg)
		worksheet.write(4, 4, '%', blue_bg)
		worksheet.write(4, 5, 'ACUMULADO INGRESOS', blue_bg)
		worksheet.write(4, 6, 'ACUMULADO COSTOS', blue_bg)
		worksheet.write(4, 7, 'RESULTADO ACUMULADO', blue_bg)
		worksheet.write(4, 8, '%', blue_bg)
		
		#----------MARGEN DE CONTRIBUCION----------

		worksheet.write(6, 0, 'INGRESOS PLANTA 1', '')
		worksheet.write(6, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-01'].pop()][2], number)
		worksheet.write(6, 2, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-01-01'].pop()][2], number)
		worksheet.write_formula('D7', '=B7-C7', number)
		worksheet.write_formula('E7', '=D7/B7', percentage)
		worksheet.write(6, 5, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-01'].pop()][3], number)
		worksheet.write(6, 6, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-01-01'].pop()][3], number)
		worksheet.write_formula('H7', '=F7-G7', number)
		worksheet.write_formula('I7', '=H7/F7', percentage)

		worksheet.write(7, 0, 'INGRESOS PLANTA 2', '')
		worksheet.write(7, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-02'].pop()][2], number)
		worksheet.write(7, 2, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-02-01'].pop()][2], number)		
		worksheet.write_formula('D8', '=B8-C8', number)
		worksheet.write_formula('E8', '=D8/B8', percentage)
		worksheet.write(7, 5, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-02'].pop()][3], number)
		worksheet.write(7, 6, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-02-01'].pop()][3], number)		
		worksheet.write_formula('H8', '=F8-G8', number)
		worksheet.write_formula('I8', '=H8/F8', percentage)

		worksheet.write(8, 0, 'INGRESOS PLANTA OBREGON', '')
		worksheet.write(8, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-01'].pop()][2]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-02'].pop()][2], number)
		worksheet.write(8, 2, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-03-01-01'].pop()][2]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-03-02-01'].pop()][2], number)		
		worksheet.write_formula('D9', '=B9-C9', number)
		worksheet.write_formula('E9', '=D9/B9', percentage)
		worksheet.write(8, 5, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-01'].pop()][3]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-02'].pop()][3], number)
		worksheet.write(8, 6, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-03-01-01'].pop()][3]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-03-02-01'].pop()][3], number)		
		worksheet.write_formula('H9', '=F9-G9', number)
		worksheet.write_formula('I9', '=H9/F9', percentage)

		worksheet.write(9, 0, 'INGRESOS MERIDA', '')
		worksheet.write(9, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-02-01'].pop()][2], number)# 01B-6-03-01
		worksheet.write(9, 2, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-02-01-01'].pop()][2], number)		
		worksheet.write_formula('D10', '=B10-C10', number)
		worksheet.write_formula('E10', '=D10/B10', percentage)
		worksheet.write(9, 5, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-02-01'].pop()][3], number)# 01B-6-03-01
		worksheet.write(9, 6, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-02-01-01'].pop()][3], number)		
		worksheet.write_formula('H10', '=F10-G10', number)
		worksheet.write_formula('I10', '=H10/F10', percentage)

		#TOTALES
		worksheet.write(11, 0, 'ACTIVIDAD PREPONDERANTE/ MARGEN DE CONTRIBUCION', border)
		worksheet.write_formula('B12', '=SUM(B7:B10)', number_bold)
		worksheet.write_formula('C12', '=SUM(C7:C10)', number_bold)
		worksheet.write_formula('D12', '=SUM(D7:D10)', number_bold)
		worksheet.write_formula('E12', '=D12/B12', percentage)
		worksheet.write_formula('F12', '=SUM(F7:F10)', number_bold)
		worksheet.write_formula('G12', '=SUM(G7:G10)', number_bold)
		worksheet.write_formula('H12', '=SUM(H7:H10)', number_bold)
		worksheet.write_formula('I12', '=H12/F12', percentage)

		#----------GASTOS FIJOS DE PRODUCION----------

		worksheet.write(13, 0, 'GASTOS FIJOS DE PRODUCCION', light_gray)
		
		worksheet.write(15, 0, 'GASTOS FIJOS DE PLANTA 1', '')
		worksheet.write(15, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-01'].pop()][2]-xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-01-01'].pop()][2]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-04'].pop()][2], number)
		worksheet.write(15, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-01'].pop()][3]-xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-01-01'].pop()][3]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-04'].pop()][3], number)

		worksheet.write(16, 0, 'GASTOS FIJOS DE PLANTA 2', '')
		worksheet.write(16, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-02'].pop()][2]-xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-02-01'].pop()][2]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-03'].pop()][2], number)
		worksheet.write(16, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-02'].pop()][3]-xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-02-01'].pop()][3]+xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-03'].pop()][3], number)

		worksheet.write(17, 0, 'GASTOS FIJOS PLANTA OBREGON', '')
		worksheet.write(17, 2, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-03'].pop()][2], invisible)
		worksheet.write_formula('D18', '=C18-C9', number)
		worksheet.write(17, 6, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-03'].pop()][3], invisible)
		worksheet.write_formula('H18', '=G18-G9', number)

		worksheet.write(18, 0, 'GASTOS FIJOS MERIDA', '')
		worksheet.write(18, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-02'].pop()][2]-xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-02-01-01'].pop()][2], number)
		worksheet.write(18, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-02'].pop()][3]-xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-02-01-01'].pop()][3], number)


		#TOTALES
		worksheet.write(20, 0, 'TOTAL COSTOS FIJOS', border)
		worksheet.write_formula('D21', '=SUM(D16:D19)', number_bold)
		worksheet.write_formula('E21', '=SUM(E16:E19)', percentage)
		worksheet.write_formula('H21', '=SUM(H16:H19)', number_bold)
		worksheet.write_formula('I21', '=SUM(I16:I19)', percentage)

		#PORCENTAJES
		worksheet.write_formula('E16', '=D16/(C12+D21)', percentage)
		worksheet.write_formula('E17', '=D17/(C12+D21)', percentage)
		worksheet.write_formula('E18', '=D18/(C12+D21)', percentage)
		worksheet.write_formula('E19', '=D19/(C12+D21)', percentage)
		worksheet.write_formula('I16', '=H16/(G12+H21)', percentage)
		worksheet.write_formula('I17', '=H17/(G12+H21)', percentage)
		worksheet.write_formula('I18', '=H18/(G12+H21)', percentage)
		worksheet.write_formula('I19', '=H19/(G12+H21)', percentage)

		#UTILIDAD BRUTA
		worksheet.write(22, 0, 'UTILIDAD BRUTA', border)
		worksheet.write_formula('D23', '=D12-D21', number_bold)
		worksheet.write_formula('E23', '=D23/B12', percentage)
		worksheet.write_formula('H23', '=H12-H21', number_bold)
		worksheet.write_formula('I23', '=H23/F12', percentage)

		#----------GASTOS DE OPERACION----------

		worksheet.write(24, 0, 'MANTENIMIENTO INDUSTRIAL', '')
		worksheet.write(24, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-63'].pop()][2], number)
		worksheet.write(24, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-63'].pop()][3], number)

		worksheet.write(25, 0, 'TALLER INDUSTRIAL', '')
		worksheet.write(25, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-64'].pop()][2], number)
		worksheet.write(25, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-64'].pop()][3], number)

		worksheet.write(26, 0, 'TALLER MECANICO', '')
		worksheet.write(26, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-65'].pop()][2], number)
		worksheet.write(26, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-65'].pop()][3], number)

		worksheet.write(27, 0, 'SERVICIOS Y EQUIPO MOVIL', '')
		worksheet.write(27, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-66'].pop()][2], number)
		worksheet.write(27, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-66'].pop()][3], number)

		worksheet.write(28, 0, 'GASTOS DE VENTA', '')
		worksheet.write(28, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-67'].pop()][2], number)
		worksheet.write(28, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-67'].pop()][3], number)

		worksheet.write(29, 0, 'GASTOS DE ADMINISTRACION', '')
		worksheet.write(29, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-68'].pop()][2], number)
		worksheet.write(29, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-68'].pop()][3], number)

		worksheet.write(30, 0, 'GASTOS DE CORPORATIVOS', '')
		worksheet.write(30, 3, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-69'].pop()][2], number)
		worksheet.write(30, 7, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-69'].pop()][3], number)
	

		#TOTALES
		worksheet.write(32, 0, 'TOTAL GASTOS DE OPERACION', border)
		worksheet.write_formula('D33', '=SUM(D25:D31)', number_bold)
		worksheet.write_formula('E33', '=SUM(E25+E31)', percentage)
		worksheet.write_formula('H33', '=SUM(H25:H31)', number_bold)
		worksheet.write_formula('I33', '=SUM(I25+I31)', percentage)

		#PORCENTAJES
		worksheet.write_formula('E25', '=D25/B12', percentage)
		worksheet.write_formula('E26', '=D26/B12', percentage)
		worksheet.write_formula('E27', '=D27/B12', percentage)
		worksheet.write_formula('E28', '=D28/B12', percentage)
		worksheet.write_formula('E29', '=D29/B12', percentage)
		worksheet.write_formula('E30', '=D30/B12', percentage)
		worksheet.write_formula('E31', '=D31/B12', percentage)
		worksheet.write_formula('I25', '=H25/F12', percentage)
		worksheet.write_formula('I26', '=H26/F12', percentage)
		worksheet.write_formula('I27', '=H27/F12', percentage)
		worksheet.write_formula('I28', '=H28/F12', percentage)
		worksheet.write_formula('I29', '=H29/F12', percentage)
		worksheet.write_formula('I30', '=H30/F12', percentage)
		worksheet.write_formula('I31', '=H31/F12', percentage)

		#UTILIDAD (PERDIDA) DE OPERACION
		worksheet.write(34, 0, 'UTILIDAD (PERDIDA) DE OPERACION', border)
		worksheet.write_formula('D35', '=D23-D33', number_bold)
		worksheet.write_formula('E35', '=D35/B12', percentage)
		worksheet.write_formula('H35', '=H23-H33', number_bold)
		worksheet.write_formula('I35', '=H35/F12', percentage)

		#----------OTROS COSTOS FINANCIEROS----------

		worksheet.write(36, 0, 'OTROS INGRESOS Y OTROS COSTOS', '')
		worksheet.write(36, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-04'].pop()][2]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-05'].pop()][2]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-02-03'].pop()][2]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-04'].pop()][2]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-05'].pop()][2], number)
		worksheet.write(36, 2, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-60'].pop()][2], number)
		worksheet.write_formula('D37', '=B37-C37', number)
		worksheet.write(36, 5, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-04'].pop()][3]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-05'].pop()][3]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-02-02'].pop()][3]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-02-03'].pop()][3]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-04'].pop()][3]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-03-05'].pop()][3], number)
		worksheet.write(36, 6, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-60'].pop()][3], number)
		worksheet.write_formula('H37', '=F37-G37', number)


		worksheet.write(37, 0, 'OTROS PRODUCTOS Y GASTOS FINANCIEROS', '')
		worksheet.write(37, 1, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-06'].pop()][2]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-02-04'].pop()][2], number)
		worksheet.write(37, 2, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-70'].pop()][2], number)
		worksheet.write_formula('D38', '=B38-C38', number)
		worksheet.write(37, 5, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-01-06'].pop()][3]+\
			xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-6-02-04'].pop()][3], number)
		worksheet.write(37, 6, xlines[[i for i, v in enumerate(xlines) if v[0] == '01H-7-01-70-05'].pop()][3], number)
		worksheet.write_formula('H38', '=F38-G38', number)
		 

		worksheet.write(38, 0, 'RESULTADO DE OTROS COSTOS Y FINANCIEROS', bold)
		worksheet.write_formula('B39', '=B37+B38', number_bold_nb)
		worksheet.write_formula('C39', '=C37+C38', number_bold_nb)
		worksheet.write_formula('D39', '=D37+D38', number_bold_nb)
		worksheet.write_formula('E39', '=D39/B12', percentage)
		worksheet.write_formula('F39', '=F37+F38', number_bold_nb)
		worksheet.write_formula('G39', '=G37+G38', number_bold_nb)
		worksheet.write_formula('H39', '=H37+H38', number_bold_nb)
		worksheet.write_formula('I39', '=H39/F12', percentage)

		#UTILIDAD NETA ANTES DE ISR Y PTU
		worksheet.write(41, 0, 'UTILIDAD NETA ANTES DE ISR Y PTU', border)
		worksheet.write_formula('D42', '=D35+D39', number_bold)
		worksheet.write_formula('E42', '=D42/(B12+B39)', percentage)
		worksheet.write_formula('H42', '=H35+H39', number_bold)
		worksheet.write_formula('I42', '=H42/(F12+F39)', percentage)

		workbook.close()
		f = open(fname.name, "r")
		data = f.read()
		f.close()

		
		self.write({'cadena_decoding':"",
			'datas_fname':datas_fname,
			'file':base64.encodestring(data),
			'download_file': True})
		print 'datas_fname: ',datas_fname
		# return {
		# 	'type': 'ir.actions.act_window',
		# 	'res_model': 'account.monthly_balance',
		# 	'view_mode': 'form',
		# 	'view_type': 'form',
		# 	'res_id': self.id,
		# 	'views': [(False, 'form')],
		# 	'target': 'new',
		# 	}