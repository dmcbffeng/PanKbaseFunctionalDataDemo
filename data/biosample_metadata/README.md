# **PankBase Biosample Metadata**

This dataset contains curated metadata for **human pancreatic biosamples**, integrating information from HPAP, nPOD, ADI, IIDP, Prodo, and other sources. Each row represents a unique biosample with detailed annotations on donor characteristics, isolation parameters, processing conditions, islet quality, and experimental context.

## **File Format**

* **Type:** TSV (tab-separated)
* **Each row:** One biosample record
* **Primary Identifier:** `Accession` (e.g., PKBSMxxxxxx)

---

# **Field Descriptions**

## **1. Identifiers & Core Metadata**

* **Accession** — Unique PankBase identifier for the biosample
* **Donors** — Donor accession linked to this biosample
* **Classifications** — Category (e.g., primary islet, primary cell, cell line)
* **Sample_terms** — Controlled ontology term describing the biosample
* **Description** — Free-text summary of sample specifics

---

## **2. Biosample Source & Derivation**

* **Biosample_type** — Type of biosample (islet, exocrine, ductal, etc.)
* **Biosample derived from** — Parent biosample if derived
* **Biosample origin of** — Samples produced from this biosample
* **Organ Source** — Donor organ type/source program (HPAP, nPOD, etc.)

---

## **3. Isolation & Processing**

* **Isolation_center** — Center where the islets were isolated
* **Treatments** — Any in vitro treatments (cytokines, drugs, etc.)
* **Preservation Method** — Freezer, cryoprotectant, fresh shipment, etc.
* **Cold Ischaemia Time (hours)** — Time pancreas was kept on ice before processing
* **Warm Ischaemia Duration / Down Time (hours)** — Time without blood supply at body temperature
* **Digest Time (hours)** — Duration of enzymatic digestion
* **Date Obtained** — Date biosample was received or isolated
* **Pre-Shipment Culture Time (hours)** — How long islets were cultured before shipping

---

## **4. Islet Quantity & Quality Metrics**

* **IEQ/Pancreas Weight (grams)** — Islet equivalents per gram of pancreas
* **Islet Yield (IEQ)** — Total yield of islet equivalents
* **Prep Viability (percentage)** — Viability before shipment
* **Purity (Percentage)** — Percentage of islet tissue vs exocrine contamination
* **Percentage Trapped (percentage)** — Fraction of trapped/non-functional islets
* **Islet Function Available** — Whether GSIS or other assays exist
* **Islet Histology** — Whether histology slides/data are available
* **Islet Morphology** — Morphology assessment availability

---

## **5. Sample Composition & Phenotype**

* **Sample_terms** — Ontology for tissue/cell type
* **External Resources** — URLs, RRIDs, vendor links, reference datasets

---

## **6. Shipment & Handling**

* **Preservation Method** — Shipping/cryopreservation technique
* **Pre-Shipment Culture Time (hours)** — Culture before packaging
* **Warm Ischaemia Duration** — Affects islet quality
* **Cold Ischaemia Time** — Key determinant of viability

---

## **7. Optional Metadata (if available)**

* **IEQ/Pancreas Weight (grams)**
* **Islet Function Available**
* **Islet Histology**
* **Islet Morphology**
* **Islet Yield (IEQ)**
* **Percentage Trapped (percentage)**
* **Prep Viability (percentage)**
* **Purity (Percentage)**

---

# **Usage Notes**

### **Best Practices**

* Always reference `Accession` and linked `Donors` for reproducibility.
* Interpret islet quality using **viability**, **purity**, **IEQ**, and **ischemia times**.
* Use **Treatments** and **Preservation Method** fields to understand experimental context.
* When comparing across cohorts (HPAP, IIDP, ADI, nPOD), check **Isolation_center** and **Organ Source**.

### **Missing Data Indicators**

* `NA` or empty = not provided
* `unknown` = explicitly marked as unknown
* `-999` = used for unavailable quantitative values

---

# **Citation**

Please cite the corresponding islet program (HPAP, nPOD, ADI, IIDP) and related publications when using these metadata in research.

