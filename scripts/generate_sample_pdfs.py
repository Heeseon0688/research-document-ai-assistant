"""Create three clearly synthetic, multi-page research PDFs for demos."""
from pathlib import Path
import fitz

OUT = Path(__file__).resolve().parents[1] / "sample_data"
DOCS = {
    "fermentation_process_report.pdf": [
        ("Fermentation Process Report", "This fictional report evaluates three bench-scale fermentation runs. SYNTHETIC SAMPLE DATA FOR RAG DEMO\nAll measurements are invented for software demonstration and are not real research."),
        ("Run design", "Runs F-01, F-02, and F-03 used a fictional yeast strain in 2 L vessels. Temperature was held at 30 C. Samples were taken at 12, 24, and 36 hours."),
        ("Results", "F-01 produced 41 g/L at 36 hours. F-02 produced 48 g/L at 36 hours and had the highest reported production. F-03 produced 44 g/L. These values are synthetic."),
        ("Interpretation", "The demonstration dataset suggests that the F-02 feed schedule is associated with higher titer. A real study would require replicates, controls, statistical analysis, and validated assays."),
    ],
    "protein_expression_report.pdf": [
        ("Protein Expression Report", "This fictional report compares expression conditions. SYNTHETIC SAMPLE DATA FOR RAG DEMO\nAll measurements are invented for software demonstration and are not real research."),
        ("Constructs", "Construct P-01 uses promoter A, P-02 uses promoter B, and P-03 uses promoter C. Cultures were induced for 16 hours in a fictional host."),
        ("Purification results", "P-01 yielded 18 mg/L at 82% purity. P-02 yielded 27 mg/L at 91% purity. P-03 yielded 22 mg/L at 87% purity. The synthetic P-02 result is the highest yield and purity."),
        ("Limitations", "The values are illustrative only. Confirmation would require independent cultures, assay calibration, identity testing, and review of raw instrument files."),
    ],
    "manufacturing_quality_report.pdf": [
        ("Manufacturing Quality Report", "This fictional report summarizes three manufacturing lots. SYNTHETIC SAMPLE DATA FOR RAG DEMO\nAll measurements are invented for software demonstration and are not real research."),
        ("Release checks", "Lots Q-01, Q-02, and Q-03 were inspected for fill volume, appearance, and a fictional potency assay. Acceptance criteria were defined for this demonstration."),
        ("Observations", "Q-01 passed all checks. Q-02 passed appearance and volume but required a repeat potency measurement. Q-03 was placed on hold because its initial potency reading was below the fictional acceptance range."),
        ("Disposition", "The synthetic record recommends investigating Q-03, preserving samples, and documenting a quality decision before release. No real manufacturing decision should be made from this demo."),
    ],
}

def main():
    OUT.mkdir(exist_ok=True)
    for filename, pages in DOCS.items():
        doc = fitz.open()
        for heading, body in pages:
            page = doc.new_page()
            page.insert_text((54, 72), heading, fontsize=20, color=(0.12, 0.3, 0.2))
            page.insert_textbox((54, 110, 540, 760), body, fontsize=12, lineheight=1.5)
        doc.save(OUT / filename)
        doc.close()
        print(OUT / filename)

if __name__ == "__main__":
    main()
