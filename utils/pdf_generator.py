from fpdf import FPDF

def create_pdf(text_file, pdf_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    with open(text_file, 'r', encoding='utf-8') as file:
        for line in file:
            pdf.multi_cell(0, 10, txt=line.strip(), align='L')
    
    pdf.output(pdf_file)

# Create PDFs
create_pdf('documents/medium_risk_rental.pdf', 'documents/medium_risk_rental.pdf') 