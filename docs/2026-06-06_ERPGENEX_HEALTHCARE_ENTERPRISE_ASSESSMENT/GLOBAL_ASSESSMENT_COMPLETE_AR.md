# ERPGenEx Healthcare — وصف كامل · مقارنة عالمية · تقييم استشاري مستقل

**التاريخ:** 2026-06-10  
**التطبيق:** `omnexa_healthcare` (ErpGenEx — Healthcare)  
**منهجية:** تدقيق حي للكود + لقطة `LIVE_AUDIT_SNAPSHOT.json` + تقييم استشاري مستقل (17 مرحلة)  
**ملاحظة مهمة:** التقييم الآلي الداخلي (`enterprise_assessment`) يقيس **وجود المكوّنات** (DocType/Page/API). هذا المستند يقيس **الجاهزية التشغيلية العالمية** (عمق سير العمل، UX، تكامل إنتاجي، شهادات، AI حقيقي).

---

## 1. الملخص التنفيذي

| المؤشر | التقييم الآلي (هيكلي) | التقييم الاستشاري (تشغيلي) |
|--------|------------------------|------------------------------|
| **الجاهزية العالمية** | 5.00 / 5.00 | **71 / 100** |
| **نضج EMR/EHR** | 100% | **76 / 100** |
| **تجربة المريض الرقمية** | — | **68 / 100** |
| **الطب عن بُعد** | موجود جزئياً | **45 / 100** |
| **الرعاية المنزلية** | غير مكتمل | **30 / 100** |
| **السياحة العلاجية** | غير مكتمل | **15 / 100** |
| **التشغيل البيني (Interop)** | APIs موجودة | **72 / 100** |
| **الأمن والامتثال** | MFA + PHI log | **76 / 100** |
| **الذكاء الاصطناعي السريري** | مسارات AI | **58 / 100** |
| **الترتيب العالمي التقريبي** | #1 (داخلي) | **~18–25** عالمياً (HIS واسع) |
| **بعد خارطة 24 شهر** | — | **~8–12** (مع تنفيذ كامل) |

### ما يميّز المنصة اليوم

- **84 DocType** + **19 صفحة** + **48 تقرير** + **23 ملف اختبار** — تغطية HIS واسعة نادراً ما تُرى في امتداد ERP مفتوح.
- **محرك تخصصات JSON** (15+ تخصص) + **مركز تميز أسنان** (FDI، خطط متعددة الزيارات، زراعة).
- **ADT/IPD** (قبول، نقل، خروج، أسرة، ICU board، مرافق، رعاية حرجة).
- **LIS/RIS** (عينات، QC، باركود، HL7 ORU، ASTM، DICOM viewer، WADO-RS).
- **RCM** (NPHIES، مطالبات، تفويض مسبق، أهلية، DRG، أقساط، باقات علاج).
- **Interop** (FHIR R4، IPS، HL7، X12).
- **موقع مستشفى عام** (`/hospital`) + بوابة موحدة حسب نشاط الشركة (`omnexa_experience`).
- **سجل PHI**، موافقات، MFA لأدوار PHI، WCAG helpers.

### أهم الفجوات نحو «عالمي فعلاً»

1. **الطب عن بُعد:** نوع موعد Telehealth دون منصة فيديو/WebRTC مدمجة (Teladoc-class).
2. **الرعاية المنزلية والسياحة العلاجية:** لا وحدة عمل كاملة (زيارات منزلية، تنسيق سفر، باقات دولية).
3. **تطبيقات مريض/طبيب native:** صفحات ويب متجاوبة وليست تطبيقات iOS/Android بإشعارات push كاملة.
4. **AI إنتاجي:** مسار LLM يولّد ملاحظات من قوالب؛ ليس نموذج سريري مُدقَّق بمستوى Epic/Cerner.
5. **PACS إنتاجي:** تكامل DICOMweb scaffold؛ يحتاج ربط PACS enterprise واختبار تيرابايت.
6. **شهادات:** خرائط HIPAA/GDPR موجودة؛ لا شهادة HIMSS EMRAM Stage 7 أو JCI digital formal.
7. **UX المريض:** تحسّن كبير بموقع المستشفى؛ لا يزال خلف Mayo/Cleveland في رحلة موحّدة end-to-end.

---

## 2. وصف المنصة (Product Description)

### 2.1 الرؤية والنطاق

ERPGenEx Healthcare منصة **معلومات صحية مؤسسية** مبنية على Frappe/ERPNext، مدمجة مع **ERPGenEx Core** (شركات متعددة، فروع، محاسبة، مخزون). تستهدف:

- مستشفيات وعيادات متعددة الفروع
- مراكز تخصصية (أسنان، قلب، عيون، …)
- سلاسل عيادات + RCM تأمين (بما في ذلك NPHIES في السعودية)
- تجربة مريض رقمية + موقع عام للمستشفى

### 2.2 الطبقات المعمارية

| الطبقة | المكوّنات |
|--------|-----------|
| **عرض (Presentation)** | Workspace 150+ رابط، 19 Page، موقع `/hospital`, بوابات `omnexa_experience` |
| **تطبيق (Application)** | 84 DocType، سير عمل ADT/OPD/ER/OT/LIS/RIS/Pharmacy |
| **تكامل (Integration)** | FHIR REST، HL7، X12، NPHIES، DICOMweb، webhooks إشعارات |
| **أمان** | Branch-scoped permissions، PHI Access Log، MFA، Patient Consent |
| **تحليلات** | Executive dashboard، 48 تقرير، population health cohorts |
| **AI** | CDS rules، AI insights، ambient session، voice dictation، AI scheduling، LLM pipeline |

### 2.3 الوحدات الوظيفية الرئيسية

| الوحدة | القدرات المنجزة |
|--------|-----------------|
| **MPI / المريض** | FHIR HumanName، معرّفات، دمج مرضى، موافقات |
| **OPD** | مواعيد، طابور، حجز ويب، تقويم، تخصصات |
| **EMR** | Encounter، SOAP، conditions، allergies، immunizations، observations |
| **IPD/ADT** | قبول، نقل سرير، خروج، census، companion stay |
| **ER** | لوحة طوارئ، ESI، disposition |
| **ICU/NICU** | لوحة حرجة، monitoring، تنبيهات |
| **OT** | حالات جراحية، checklist، OR، anesthesia |
| **LIS** | عينات، باركود، QC، reference range، HL7/ASTM inbound |
| **RIS/PACS** | worklist، تقارير، DICOM viewer، WADO-RS، MPPS |
| **Pharmacy** | صرف، تفاعلات دوائية، eMAR |
| **RCM** | مطالبات، remittance، eligibility، DRG، أقساط |
| **Dental COE** | مخطط FDI، خطط علاج، تقويم، زراعة |
| **Specialty Engine** | 15+ module JSON-driven |
| **Patient engagement** | portal APIs، journey wizard، SMS/WhatsApp hooks |
| **Public web** | hospital site، أطباء، حجز 5 خطوات، متجر |

---

## 3. مقارنة عالمية (Competitive Benchmark)

### 3.1 مصفوفة المقارنة (تقييم استشاري 1–5)

| المنصة | EHR/EMR | IPD | LIS/RIS | RCM | Patient UX | Telehealth | AI | Interop | SME تكلفة | **متوسط** |
|--------|---------|-----|---------|-----|------------|------------|-----|---------|-----------|-----------|
| **Epic** | 5.0 | 5.0 | 4.8 | 4.9 | 4.7 | 4.5 | 4.6 | 4.9 | 2.0 | **4.82** |
| **Oracle Health (Cerner)** | 4.8 | 4.9 | 4.7 | 4.8 | 4.4 | 4.3 | 4.2 | 4.8 | 2.5 | **4.75** |
| **MEDITECH** | 4.5 | 4.7 | 4.4 | 4.5 | 4.0 | 3.8 | 3.5 | 4.3 | 3.0 | **4.55** |
| **eClinicalWorks** | 4.4 | 4.2 | 4.0 | 4.5 | 4.3 | 4.5 | 4.0 | 4.0 | 3.5 | **4.45** |
| **Athenahealth** | 4.3 | 3.8 | 3.5 | 4.7 | 4.5 | 4.2 | 3.8 | 3.9 | 3.8 | **4.50** |
| **InterSystems TrakCare** | 4.6 | 4.7 | 4.5 | 4.4 | 4.2 | 4.0 | 3.9 | 4.6 | 3.0 | **4.55** |
| **NextGen** | 4.2 | 4.0 | 4.0 | 4.3 | 4.1 | 4.0 | 3.7 | 4.0 | 3.5 | **4.40** |
| **Teladoc (تجربة مريض)** | — | — | — | — | 4.8 | 5.0 | 4.0 | 3.5 | — | **4.6** (niche) |
| **ERPGenEx Healthcare** | **4.0** | **4.2** | **3.8** | **4.3** | **3.6** | **2.5** | **2.9** | **3.8** | **4.8** | **3.72** |
| **ERPGenEx (عمق بعد 24 شهر)** | 4.5 | 4.6 | 4.3 | 4.6 | 4.5 | 4.2 | 4.0 | 4.5 | 4.8 | **4.45** |

### 3.2 نقاط القوة مقابل العمالقة

| البُعد | ERPGenEx | Epic/Cerner |
|--------|----------|-------------|
| **التكلفة والنشر** | مفتوح/مرن، SME ومتوسط | تكلفة عالية، مشاريع طويلة |
| **تعدد الأنشطة** | ERP + صحة + تجارة + تمويل في منصة واحدة | تركيز صحي primarily |
| **السعودية/NPHIES** | NPHIES bundles أصلية | يتطلب شركاء/تخصيص |
| **التخصصات والأسنان** | محرك JSON + COE أسنان عميق | قوي لكن تخصيص مكلف |
| **سرعة التخصيص** | Frappe low-code | تخصيص Epic costly |
| **الفروع المتعددة** | Company/Branch native | قوي لكن معقد |

### 3.3 نقاط الضعف مقابل العمالقة

| البُعد | الفجوة |
|--------|--------|
| **تجربة مريض consumer-grade** | Mayo/Cleveland/Teladoc أعلى بكثير |
| **Telehealth فيديو** | غير مدمج |
| **AI سريري مُنتج** | Epic/Cerner لديهم مسارات FDA-aware |
| **Scale 500+ سرير** | يحتاج اختبار أداء وread replicas |
| **شهادات** | HIMSS/JCI formal غير مُنجزة |
| **Marketplace تكاملات** | App Orchard / Cerner CODE أوسع |

---

## 4. تقييم HIMSS / JCI / معايير دولية

| المعيار | الوضع الحالي | الهدف |
|---------|-------------|--------|
| **HIMSS EMRAM** | ~Stage 4–5 (سجلات سريرية، LIS/RIS، بوابة جزئية) | Stage 6–7 |
| **JCI Digital** | خرائط عمليات؛ لا audit pack كامل | توثيق JCI + KPIs |
| **NHS Digital** | FHIR/IPS جزئي | UK CIIS alignment |
| **HIPAA** | mapped + PHI log + MFA | BAA + penetration test |
| **GDPR** | mapped | DPIA formal |
| **ISO 27001** | partial | certification path |

---

## 5. الترتيب العالمي والجاهزية

| السيناريو | الترتيب التقريبي | الجاهزية |
|-----------|------------------|----------|
| **اليوم — HIS عالمي شامل** | 18–25 | 71% |
| **اليوم — ERP+Healthcare SME** | 3–5 | 85% |
| **اليوم — شرق أوسط + NPHIES** | 5–8 | 80% |
| **بعد 12 شهر (خارطة كاملة)** | 10–15 | 85% |
| **بعد 24 شهر** | 8–12 | 90%+ |

**احتمال الوصول لـ «أفضل عالمياً»:** يتطلب تنفيذ كامل للفجوات الحرجة (telehealth، UX، AI إنتاجي، شهادات، scale) — **واقعي خلال 18–24 شهر** مع استثمار منتج مستمر.

---

## 6. الروابط والوثائق المرتبطة

| المستند | المحتوى |
|---------|---------|
| [GAP_ANALYSIS_17_PHASES_AR.md](./GAP_ANALYSIS_17_PHASES_AR.md) | تدقيق 17 مرحلة مفصّل |
| [DEVELOPMENT_ROADMAP_2026_AR.md](./DEVELOPMENT_ROADMAP_2026_AR.md) | خارطة 30/90/6/12/24 شهر |
| [MASTER_CHECKLIST_v2026.json](./MASTER_CHECKLIST_v2026.json) | تشيكليست صريح (موجود/ناقص) |
| [LIVE_AUDIT_SNAPSHOT.json](./LIVE_AUDIT_SNAPSHOT.json) | لقطة آلية محدّثة |
| [ENTERPRISE_AUDIT_AR.md](./ENTERPRISE_AUDIT_AR.md) | تدقيق مؤسسي تفصيلي |

---

## 7. أوامر التحقق

```bash
bench --site SITE migrate
bench build --app omnexa_healthcare
bench --site SITE execute omnexa_healthcare.enterprise_assessment.execute
bench --site SITE run-tests --app omnexa_healthcare
```

---

*ErpGenEx Healthcare · Global Assessment v2026.06.10 · Independent Consultant View*
