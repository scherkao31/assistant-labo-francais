# Laboratory Datasets Description

This document describes the Belgian laboratory analysis datasets scraped from various hospital websites. These datasets are designed for use in RAG (Retrieval-Augmented Generation) systems to provide comprehensive information about medical laboratory tests.

## 📊 Dataset Overview

| Laboratory | Analyses Count | File Size | Detail Level | Status |
|------------|---------------|-----------|--------------|--------|
| **LHUB-ULB** | 1,513 | 308KB | Basic + Detailed | ✅ Complete |
| **UZA** | 2,852 | 718KB | Detailed | ✅ Complete |
| **Citadelle** | 800+ | 217KB | Detailed | ✅ Complete |
| **CHU ULG** | 4,685 | 1.4MB | Basic | ✅ Complete |
| **Total** | **~9,850** | **~2.6MB** | Mixed | ✅ Complete |

## 🏥 Individual Laboratory Descriptions

### 1. LHUB-ULB (Laboratoire Hospitalier Universitaire de Bruxelles)
**Files:** `examen_lhub.json`, `examen_lhub_detailed.json`
**Source:** https://lhub-ulb.manuelprelevement.be/

**Description:**
- University hospital laboratory in Brussels
- Comprehensive collection of routine and specialized analyses
- Covers multiple medical specialties

**Data Structure:**
```json
{
  "titre": "Analysis name",
  "code": "Laboratory code",
  "id": "Internal ID",
  "lien": "Detail page URL"
}
```

**Detailed version includes:**
- `description`: Full analysis description
- `indication`: Clinical indications
- `prelevement`: Sample collection instructions
- `technique`: Analytical method
- `interpretation`: Result interpretation
- `reference`: Reference values

**Use Case:** General medical laboratory queries, routine blood tests, biochemistry

---

### 2. UZA (Universitair Ziekenhuis Antwerpen)
**File:** `examen_uza_detailed.json`
**Source:** https://www.uza.be/

**Description:**
- University hospital in Antwerp
- Largest dataset with detailed information
- Strong focus on specialized and advanced diagnostics
- Includes emergency/urgent analysis indicators

**Data Structure:**
```json
{
  "titre": "Analysis name",
  "code": "UZA code",
  "lien": "Detail page URL",
  "description": "Detailed description",
  "indication": "Clinical use",
  "prelevement": "Sample requirements",
  "technique": "Methodology",
  "interpretation": "Result interpretation",
  "reference": "Normal values",
  "urgence": "Emergency availability"
}
```

**Special Features:**
- Emergency analysis indicators
- Comprehensive sample collection details
- Detailed methodology descriptions
- Clinical interpretation guidelines

**Use Case:** Advanced diagnostics, emergency medicine, specialized testing

---

### 3. Citadelle (CHR Citadelle)
**File:** `examen_citadelle_detailed.json`
**Source:** https://www.chrcitadelle.be/

**Description:**
- Regional hospital center in Liège
- Focus on routine and specialized analyses
- Good coverage of common laboratory tests
- Includes sample type specifications

**Data Structure:**
```json
{
  "titre": "Analysis name",
  "code": "Citadelle code",
  "lien": "Detail page URL",
  "description": "Analysis description",
  "indication": "Clinical indications",
  "prelevement": "Sample collection",
  "technique": "Analytical method",
  "interpretation": "Result interpretation",
  "reference": "Reference ranges"
}
```

**Use Case:** Regional hospital diagnostics, routine laboratory medicine

---

### 4. CHU ULG (Centre Hospitalier Universitaire de Liège)
**File:** `examen_chu_ulg.json`
**Source:** https://www.chu.ulg.ac.be/

**Description:**
- University hospital of Liège
- Largest collection with 4,685 analyses
- Comprehensive coverage including genetics, oncology, hematology
- Strong in specialized and molecular diagnostics

**Data Structure:**
```json
{
  "code": "Laboratory code",
  "titre": "Analysis name",
  "lien": "Detail page URL",
  "types_echantillons": "Sample types (pipe-separated)",
  "methode": "Analytical method"
}
```

**Special Features:**
- Extensive genetics and molecular biology coverage
- Detailed sample type specifications
- Comprehensive oncology and hematology panels
- Advanced diagnostic techniques (FISH, CGH, etc.)

**Use Case:** Specialized diagnostics, genetics, oncology, research-level testing

## 🎯 RAG System Integration Guidelines

### For LLM Processing:

1. **Data Normalization:**
   - All datasets contain French language content
   - Common fields: `titre`, `code`, `lien`
   - Variable detail levels across datasets

2. **Search Strategies:**
   - Use `titre` for analysis name matching
   - Use `code` for exact laboratory code lookup
   - Use `description` for detailed content search
   - Use `indication` for clinical use cases

3. **Query Types Supported:**
   - **Analysis lookup:** "What is glucose test?"
   - **Clinical indication:** "Tests for diabetes"
   - **Sample requirements:** "Blood tests for anemia"
   - **Methodology:** "How is PCR performed?"
   - **Reference values:** "Normal range for cholesterol"

4. **Multi-Laboratory Coverage:**
   - Cross-reference similar tests across hospitals
   - Compare methodologies between institutions
   - Identify specialized tests available at specific centers

### Recommended RAG Architecture:

```
User Query → 
  Embedding → 
    Vector Search (across all datasets) → 
      Retrieve relevant analyses → 
        Context enrichment → 
          LLM Response with hospital-specific info
```

### Key Considerations:

1. **Language:** All content is in French
2. **Medical Terminology:** Uses standard Belgian medical terminology
3. **Completeness:** Some datasets have more detail than others
4. **Updates:** Data reflects snapshot from scraping date
5. **Accuracy:** Information sourced directly from hospital websites

## 📋 Sample Queries for Testing:

1. **Basic Analysis Lookup:**
   - "Qu'est-ce que l'analyse de glucose?"
   - "Comment se fait un test de cholestérol?"

2. **Clinical Indications:**
   - "Quels tests pour diagnostiquer le diabète?"
   - "Analyses pour l'anémie"

3. **Sample Requirements:**
   - "Prélèvement sanguin à jeun"
   - "Tests sur urine"

4. **Hospital-Specific:**
   - "Tests génétiques au CHU ULG"
   - "Analyses d'urgence à l'UZA"

## 🔄 Data Maintenance:

- **Scrapers Available:** All datasets have corresponding scraper scripts
- **Update Frequency:** Run scrapers periodically to refresh data
- **Quality Assurance:** Validate data structure and completeness
- **Backup:** Keep historical versions for comparison

This comprehensive dataset provides extensive coverage of Belgian laboratory medicine, suitable for building robust RAG systems for medical laboratory information retrieval. 