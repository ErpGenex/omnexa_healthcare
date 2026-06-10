# إطار التخصصات + مركز تميز الأسنان

**المرحلتان 4–5** | **التاريخ:** 2026-06-06

---

## المرحلة 4 — محرك التخصصات الديناميكي

### المبدأ
**تخصص جديد = سجل `Healthcare Specialty Module` + JSON** — بدون تعديل كود Python لكل تخصص.

### DocType: Healthcare Specialty Module

| الحقل | الغرض |
|-------|--------|
| `module_code` | معرّف فريد (مثل `dental`) |
| `specialty` | رابط Healthcare Specialty |
| `chart_type` | none · dental_fdi · dental_universal · body_map · custom |
| `encounter_sections` | JSON أقسام الزيارة |
| `consultation_workflow` | JSON خطوات الاستشارة |
| `procedure_workflow` | JSON الإجراءات |
| `billing_workflow` | JSON الفوترة |
| `insurance_workflow` | JSON التأمين |
| `inventory_workflow` | JSON المخزون |

### التخصصات المدعومة (قابلة للتوسع)

Cardiology · Dermatology · Ophthalmology · Orthopedics · Pediatrics · ENT · Gynecology · Surgery · Psychiatry · Physiotherapy · Oncology · Neurology · Urology · Gastroenterology · **Dental**

### API

- `omnexa_healthcare.specialty_engine.list_specialty_modules`
- `omnexa_healthcare.specialty_engine.get_specialty_module_config`
- `specialty_emr.apply_clinical_template` — يقرأ من المحرك أولاً (backward compatible مع SPECIALTY_FORMS)

### التراجع
حذف سجل Module لا يؤثر على بيانات مرضى — fallback إلى SPECIALTY_FORMS الثابت.

---

## المرحلة 5 — مركز تميز الأسنان (Dental CoE)

### منفّذ اليوم ✅

| المكوّن | الوصف |
|---------|--------|
| `Healthcare Dental Chart Entry` | سجل لكل سن/سطح |
| `api/dental.py` | FDI (11–48) + Universal (1–32) |
| `upsert_dental_chart_entry` | إنشاء/تحديث بدون تكرار |
| `get_patient_dental_chart` | عرض المخطط الكامل |
| Specialty Module `dental` | أقسام: Tooth Chart, Periodontal, Treatment Plan, Imaging |

### مخطط المرحلة التالية 🟡

| الميزة | الوصف |
|--------|--------|
| UI تفاعلي | صفحة Desk بمخطط 32 سنًا قابل للنقر |
| Multi-visit plan | DocType خطة علاج متعددة الزيارات |
| Imaging | ربط Diagnostic Report بالسن |
| Orthodontics | مسارات تقويم + جداول زيارات |
| Crown & Bridge | BOM مخزون + Procedure Order |
| Implant | ربط Implant Trace الموجود |

### سير العمل المستهدف

```
استقبال → فحص → مخطط أسنان (FDI/Universal) → خطة علاج متعددة الزيارات
→ موافقة → تنفيذ (إجراءات/مخزون) → فوترة (نقد/تأمين/أقساط) → متابعة
```

### ترقيم الأسنان

- **FDI:** 11–18, 21–28, 31–38, 41–48 (معيار دولي)
- **Universal:** 1–32 (أمريكا)

---

*مرجع الكود: `specialty_engine.py` · `api/dental.py` · `patches/v1_0/seed_specialty_modules.py`*
