pdf_path = "docs\HDFC\HDFC-optima_secure\HDFC-optima_secure_policywordings.pdf" 

import pdfplumber
import pandas as pd

def extract_page_content(page, page_num):
    """Extract text and tables in the correct order from a page."""
    elements = []

    # Extract text word by word with positions
    words = page.extract_words()
    if words:
        text = page.extract_text()
        if text:
            elements.append((min(w["top"] for w in words), text.strip()))

    # Extract tables with positions
    for table_num, table in enumerate(page.extract_tables(), start=1):
        df = pd.DataFrame(table)
        md_table = df.to_markdown(index=False)
        bbox_top = page.find_tables()[table_num - 1].bbox[1]  # Get table's Y-position
        elements.append((bbox_top, f"\n### Table {page_num}.{table_num}\n{md_table}\n"))

    # Sort elements by Y-coordinate to maintain order
    elements.sort(key=lambda x: x[0])

    # Return ordered content
    return "\n\n".join(e[1] for e in elements)

def extract_pdf_content(pdf_path):
    """Extract text and tables in order for the entire PDF."""
    content = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            content.append(extract_page_content(page, page_num))

    return "\n\n".join(content)

def save_to_markdown(pdf_path, md_output_path):
    """Convert PDF to Markdown while maintaining content order."""
    md_content = extract_pdf_content(pdf_path)

    with open(md_output_path, "w", encoding="utf-8") as md_file:
        md_file.write(md_content)

if __name__ == "__main__":
    pdf_file = pdf_path  # Change this to your PDF file
    md_file = "output.md"

    save_to_markdown(pdf_file, md_file)
    print(f"Markdown file saved as {md_file}")
