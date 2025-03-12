from haystack.nodes import PDFToTextConverter

pdf_path = "docs\HDFC\HDFC-optima_secure\HDFC-optima_secure_policywordings.pdf" 
# Initialize PDF Converter
converter = PDFToTextConverter(remove_numeric_tables=True)

# Convert PDF to text
docs = converter.convert(file_path=pdf_path, meta=None)

# Print extracted text
print(docs[0]["content"])
# Save extracted text to a file
output_txt = "output.txt"

with open(output_txt, "w", encoding="utf-8") as f:
    for doc in docs:
        f.write(doc["content"] + "\n\n")

print(f"PDF text successfully extracted and saved to {output_txt}")




