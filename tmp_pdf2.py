"""Throwaway: dump the exact pages needed from the HFSS scripting guide."""

from pypdf import PdfReader

PDF = r"C:\Program Files\AnsysEM\v221\Win64\Help\HFSS\HFSSScriptingGuide.pdf"

reader = PdfReader(PDF)

for index in (1029, 1030, 1031):
    print("\n" + "=" * 70)
    print("PAGE", index + 1)
    print("=" * 70)
    print(reader.pages[index].extract_text())

# also find GetFaceIDs
for index, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    if "GetFaceIDs" in text and "GetFaceIDsOfSheet" in text:
        print("\n" + "=" * 70)
        print("PAGE", index + 1)
        print("=" * 70)
        print(text[:5000])
        break
