from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, txt="• Bullet point with smart quotes ‘ ’ “ ” and em-dash —")
with open("test.pdf", "wb") as f:
    f.write(pdf.output(dest='S').encode('latin-1'))
