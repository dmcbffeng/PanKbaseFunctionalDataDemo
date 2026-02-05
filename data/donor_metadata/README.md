# PankBase Human Donor Metadata

## Overview

This dataset contains comprehensive metadata for **3,739 human organ donors** who contributed pancreatic tissue and/or purified pancreatic islets for research. The data integrates information from multiple sources including HPAP (Human Pancreas Analysis Program), nPOD (Network for Pancreatic Organ donors with Diabetes), ADI (Alberta Diabetes Institute IsletCore), and IIDP (Integrated Islet Distribution Program).

This resource enables researchers to identify appropriate donor samples for studies, understand donor characteristics, correlate phenotypes with experimental outcomes, and perform meta-analyses across multiple pancreatic research cohorts.

## Dataset Information

- **Total Donors**: 3,739
- **Data Sources**: HPAP, nPOD, ADI, IIDP, Pancreatlas
- **Award**: U24DK138512-DK138515
- **Lab**: pankbase-consortium
- **Schema**: https://data.pankbase.org/profiles/human_donor/
- **Format**: Tab-separated values (TSV)
- **Standards Reference**: Based on Hart & Powers (Diabetologia 2018), Brissova et al. (Diabetes 2019, Diabetologia 2019)

## File Description

**Filename**: `pankbase-human-donor.tsv`

This file contains one row per donor with extensive metadata organized into the following categories:

## Field Categories

### Core Identifiers

- `Accession`: Unique PankBase identifier (PKBDO...)
- `Center Donor ID`: Original identifier from the source program (e.g., SAMN19842597)
- `RRID`: Research Resource Identifier for cross-referencing
- `Collections`: Source program (HPAP, nPOD, ADI, IIDP)

### Demographics (Tier 0 & 1 - Required)

- `Age (years)`: Donor age in years
- `Gender`: Reported biological sex (male/female)
- `BMI`: Body mass index (kg/m²)
- `Ethnicities`: Self-reported ethnicity
- `Predicted Genetic Ancestry`: Inferred ancestry from genetic analysis (with percentages)
- `Genetic Sex`: Genetic sex inferred from genomic data

### Diabetes Status (Tier 1 - Required)

- `Description of diabetes status`: Detailed diabetes classification
  - Allowed values: type 1 diabetes, type 2 diabetes, gestational diabetes, MODY, monogenic diabetes, neonatal diabetes, Wolfram syndrome, Alström syndrome, LADA, type 3c diabetes, steroid-induced diabetes, cystic fibrosis-related diabetes, control without diabetes, diabetes unspecified
- `Diabetes Status`: Ontology term (MONDO IDs)
- `Derived diabetes status`: Classification based on A1C value (Normal, Prediabetes, Diabetes)
- `T1D stage`: Type 1 diabetes staging
  - At-risk: Single or transient autoantibody, normal glucose
  - Stage 1: Two or more autoantibodies, normal glucose metabolism
  - Stage 2: Two or more autoantibodies, dysglycemia (HbA1c ≥ 5.7%)
  - Stage 3: One or more autoantibodies and diagnostic hyperglycemia or T1D diagnosis
  - Unknown: Insufficient information

### Diabetes-Related Clinical Data (Tier 2 & 3)

- `HbA1C (percentage)`: Hemoglobin A1C levels
- `C-Peptide (ng/ml)`: C-peptide concentration
- `Diabetes Duration (years)`: Years since diabetes diagnosis
- `Family History of Diabetes`: Boolean (TRUE/FALSE)
- `Family History of Diabetes Relationship`: Relationship to diabetic family members (e.g., "Paternal_grandmother, paternal_great_aunt")
- `Other Therapy`: Glucose-lowering therapy and medication regimen

### Autoantibody Testing (Tier 3)

Each autoantibody marker includes measurement fields:

**GADA (Glutamic Acid Decarboxylase Antibody)**
- `AAB GADA POSITIVE`: Boolean indicating presence above threshold
- `AAB GADA value (unit/ml)`: Numeric value

**IA2 (Insulinoma-Associated Antigen 2 Antibody)**
- `AAB IA2 POSITIVE`: Boolean indicating presence above threshold
- `AAB IA2 value (unit/ml)`: Numeric value

**IAA (Insulin Autoantibody)**
- `AAB IAA POSITIVE`: Boolean indicating presence above threshold
- `AAB IAA value (unit/ml)`: Numeric value

**ZNT8 (Zinc Transporter 8 Antibody)**
- `AAB ZNT8 POSITIVE`: Boolean indicating presence above threshold
- `AAB ZNT8 value (unit/ml)`: Numeric value

### Autoantibody Summary Fields

These derived fields provide quick assessment of autoantibody profiles:

- `Number AAB`: Total count of positive autoantibodies (0-4)
  - Used to assess autoimmune burden in type 1 diabetes
  - Higher counts associated with more aggressive disease
  
- `Multi AAB`: Boolean indicating if multiple (≥2) autoantibodies are positive
  - TRUE: Two or more autoantibodies positive
  - FALSE: Zero or one autoantibody positive
  - Important for T1D staging (Stage 1+ requires ≥2 positive)
  
- `Only AAB GADA`: Boolean indicating GADA is the only positive autoantibody
  - TRUE: GADA positive, all others negative
  - FALSE: Multiple positives or GADA negative
  
- `Only AAB IA2`: Boolean indicating IA2 is the only positive autoantibody
  - TRUE: IA2 positive, all others negative
  - FALSE: Multiple positives or IA2 negative
  
- `Only AAB IAA`: Boolean indicating IAA is the only positive autoantibody
  - TRUE: IAA positive, all others negative
  - FALSE: Multiple positives or IAA negative
  
- `Only AAB ZNT8`: Boolean indicating ZNT8 is the only positive autoantibody
  - TRUE: ZNT8 positive, all others negative
  - FALSE: Multiple positives or ZNT8 negative

### Donation Information (Tier 2)

- `Cause of Death`: Primary medical condition leading to death
- `Donation Type`: Type of organ donation
  - Donation after Brain Death (DBD)
  - Donation after Circulatory Death (DCD)
  - Natural Death Donation
  - Medical Assistance in Dying (MAID)
- `Hospital Stay (hours)`: Total hours of hospitalization

## Data Interpretation Notes

### Missing Data
- `-` or `NA`: Data not available
- Empty fields: Data not collected or not applicable
- `0` or `FALSE`: Negative result (context-dependent)

### Autoantibody Results
- **POSITIVE = TRUE**: Autoantibody detected above threshold
- **POSITIVE = FALSE**: Autoantibody negative or below threshold
- Values provided in unit/ml when available

### Autoantibody Summary Interpretation

**Number AAB** ranges from 0 to 4:
- **0**: No autoantibodies detected (typical for controls)
- **1**: Single autoantibody (At-risk for T1D)
- **2+**: Multiple autoantibodies (T1D Stage 1 or higher)
- **3-4**: High autoantibody burden (often associated with rapid progression)

**Multi AAB** is critical for T1D classification:
- Donors with `Multi AAB = TRUE` meet autoimmune criteria for T1D Stage 1+
- Used in conjunction with glycemic status to determine precise staging

**Single-marker flags** (Only AAB X) help identify unique autoimmune profiles:
- Single GADA positivity is common in LADA (latent autoimmune diabetes in adults)
- Single IAA positivity may occur in very young children
- These fields facilitate stratification for mechanistic studies

### Predicted Genetic Ancestry
Provided as percentage breakdown:
```
{'ethnicity': 'European', 'percentage': 96},{'ethnicity': 'African', 'percentage': 3}
```

## Quality Control Recommendations

When using this dataset, consider:

1. **Check completeness**: Not all fields are available for all donors
2. **Verify RRIDs**: Use RRIDs to cross-reference with source databases
3. **Consider cohort effects**: Different programs may have different protocols
4. **Review autoantibody assays**: Different assays may have different thresholds
5. **Validate autoantibody summaries**: Cross-check `Number AAB` and `Multi AAB` with individual markers
6. **Review T1D staging**: Ensure autoantibody data supports the assigned T1D stage

## Linking to Other PankBase Data

This donor metadata can be linked to other PankBase datasets using:

- **Donor Accession** (PKBDO...): Primary key for linking
- **RRID**: For cross-referencing with external databases
- **Center Donor ID**: For linking back to source program data

## Common Use Cases

### Example 1: Identifying Multi-Autoantibody Positive Donors
```
Filter: Multi AAB = TRUE
Result: Donors with ≥2 positive autoantibodies (T1D Stage 1+)
```

### Example 2: Finding Single GADA-Positive Donors (LADA candidates)
```
Filter: Only AAB GADA = TRUE AND Age (years) > 30
Result: Adult donors with isolated GADA positivity
```

### Example 3: Stratifying by Autoantibody Burden
```
Group by: Number AAB (0, 1, 2, 3, 4)
Analysis: Compare disease characteristics across groups
```

### Example 4: T1D Stage 1 Identification
```
Filter: Multi AAB = TRUE AND Derived diabetes status = Normal
Result: Stage 1 T1D donors (pre-symptomatic)
```

## Citation

If you use this dataset in your research, please cite:

### HPAP (Human Pancreas Analysis Program)

RRID:SCR_016202; PMID: 31127054; PMID: 36206763. HPAP is part of a Human Islet Research Network (RRID:SCR_014393) consortium (UC4-DK112217, U01-DK123594, UC4-DK112232, and U01-DK123716).

### nPOD (Network for Pancreatic Organ donors with Diabetes)

The Network for Pancreatic Organ donors with Diabetes (nPOD; RRID:SCR_014641) is a collaborative type 1 diabetes research project supported by grants from Breakthrough T1D/The Leona M. & Harry B. Helmsley Charitable Trust (3-SRA-2023-1417-S-B) and the Helmsley Charitable Trust (2018PG-T1D053, G-2108-04793). Results and interpretation of analyses that include nPOD data are the responsibility of the authors and do not necessarily reflect the official view of nPOD. Organ Procurement Organizations (OPO) partnering with nPOD to provide research resources are listed at https://npod.org/for-partners/npod-partners/.

Additional information about how to identify nPOD samples in your work and other relevant guidelines can be found at the nPOD website (https://npod.org/publications/policies/).

### ADI (Alberta Diabetes Institute IsletCore)

Human islets for research were provided by the Alberta Diabetes Institute IsletCore at the University of Alberta in Edmonton (http://www.bcell.org/adi-isletcore.html) with the assistance of the Human Organ Procurement and Exchange (HOPE) program, Trillium Gift of Life Network (TGLN), and other Canadian organ procurement organizations. Islet isolation was approved by the Human Research Ethics Board at the University of Alberta (Pro00013094). All donors' families gave informed consent for the use of pancreatic tissue in research.

This work includes data and/or analyses from HumanIslets.com funded by the Canadian Institutes of Health Research, JDRF Canada, and Diabetes Canada (5-SRA-2021-1149-S-B/TG 179092).

**ADI HumanIslets.com web tool:**
- Ewald et al. (2024) HumanIslets.com: Improving accessibility, integration, and usability of human research islet data. Cell Metab. 2025 Jan 7;37(1):7-11. doi: 10.1016/j.cmet.2024.09.001. PMID: 39357523.

### IIDP (Integrated Islet Distribution Program)

Some experimental results were derived from human pancreatic islets and/or other resources provided by the NIDDK-funded Integrated Islet Distribution Program (IIDP) (RRID:SCR_014387) at City of Hope, NIH Grant # 2UC4DK098085.

### Pancreatlas

Saunders, D. C. et al. Pancreatlas: Applying an Adaptable Framework to Map the Human Pancreas in Health and Disease. Patterns 1(8), 100120 (2020). DOI: 10.1016/j.patter.2020.100120. RRID:SCR_018567

### Metadata Standards

- Hart N & Powers A. Use of human islets to understand islet biology and diabetes: progress, challenges and suggestions. Diabetologia 2018.
- Brissova M et al. Assessment of human pancreatic islet architecture and composition by laser scanning confocal microscopy. J Histochem Cytochem 2005.
- Brissova M et al. α Cell Function and Gene Expression Are Compromised in Type 1 Diabetes. Cell Rep 2018.

## Contact & Support

For questions, issues, or additional information:
- **Website**: [PankBase Portal](https://pankbase.org)
- **Data Model**: https://data.pankbase.org/profiles/human_donor/
- **Award**: U24DK138512-DK138515
- **Email**: help@pankbase.org

## Data Use Guidelines

### IMPORTANT: Source-Specific Requirements

When using data from specific sources, researchers must:

1. **Check source-specific policies**: Each program (HPAP, nPOD, ADI, IIDP) may have specific data use requirements
2. **Use appropriate RRIDs**: Always cite RRIDs in publications for reproducibility
3. **Review publication policies**: Some programs require manuscript review before publication
4. **Acknowledge donor families**: Respect the contribution of organ donors and their families

### Recommended Practices

- Report the `Accession` and `RRID` in publications for reproducibility
- Describe donor selection criteria clearly in methods
- Report any exclusions or filters applied
- Consider batch effects when combining data from multiple sources
- Acknowledge incomplete data and potential biases

## License

Please refer to PankBase data use policies for licensing and terms of use. Individual data sources (HPAP, nPOD, ADI, IIDP) may have specific requirements for data usage and publication. Please review the citation requirements above and consult the respective program websites for detailed policies.

---

**Dataset**: pankbase-human-donor.tsv  
**Total Donors**: 3,739  
**Last Updated**: November 20th, 2025  
**Format**: Tab-separated values (TSV)  
**Schema Version**: 18