import pdfplumber
import pandas as pd
import os

pdf_path = "docs/HDFC/HDFC-optima_secure/HDFC-optima_secure_policywordings.pdf"
output_dir = "md_output"  # Directory to store MD files

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

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

def save_pages_as_markdown(pdf_path, output_dir):
    """Save each page of the PDF as a separate Markdown file."""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            md_content = extract_page_content(page, page_num)
            md_filename = os.path.join(output_dir, f"page_{page_num}.md")

            with open(md_filename, "w", encoding="utf-8") as md_file:
                md_file.write(md_content)

            print(f"Saved: {md_filename}")

if __name__ == "__main__":
    save_pages_as_markdown(pdf_path, output_dir)
