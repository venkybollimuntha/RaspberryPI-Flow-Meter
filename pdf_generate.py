from fpdf import FPDF

data = [['ID', 'Flow Rate', 'Timestamp'],]
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
col_width = pdf.w / 4.5
row_height = pdf.font_size
for row in data:
	for item in row:
		pdf.cell(col_width, row_height*2,txt=item, border=1)
	pdf.ln(row_height*2)
pdf.output("simple_demo.pdf")