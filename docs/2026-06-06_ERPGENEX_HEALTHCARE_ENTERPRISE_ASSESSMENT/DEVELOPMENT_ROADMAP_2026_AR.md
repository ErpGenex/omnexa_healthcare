# خارطة تطوير عالمية — ERPGenEx Healthcare 2026–2028

**التاريخ:** 2026-06-10  
**الهدف:** رفع الجاهزية من **71%** إلى **90%+** خلال 24 شهر  
**المبدأ:** إضافات غير كاسرة · feature flags · اختبارات E2E لكل موجة

---

## Quick Wins — 30 يوم

| # | المهمة | المجال | الجهد | الأثر |
|---|--------|--------|-------|-------|
| 1 | دمج بوابة مريض مع موقع `/hospital` (حساب واحد) | UX | M | عالي |
| 2 | OTP تسجيل/دخول مريض | Security | S | عالي |
| 3 | waitlist للمواعيد (UI + API) | Scheduling | M | متوسط |
| 4 | نتائج مختبر/أشعة في البوابة بتصميم موحّد | Patient | S | عالي |
| 5 | تفعيل MFA لجميع الأطباء | Security | S | عالي |
| 6 | تقرير PHI access شهري | Compliance | S | متوسط |
| 7 | تحسين حجز 5 خطوات (تأكيد SMS/WhatsApp) | UX | S | عالي |
| 8 | خريطة أسرة visual (IPD board) | IPD | M | متوسط |
| 9 | CPT code picker في Encounter | Clinical | M | متوسط |
| 10 | توثيق DR runbook صحي | Ops | S | عالي |

---

## Phase 1 — 90 يوم

### المجموعة A: تجربة المريض
- تطبيق ويب مريض SPA (مواعيد، نتائج، فواتير، رسائل)
- دفع أونلاين (Stripe/HyperPay/Tap) مرتبط بـ Service Charge
- إشعارات push (FCM) عبر Mobile Device Token
- ملف عائلة / dependents

### المجموعة B: الطب عن بُعد
- تكامل WebRTC (Jitsi/Daily.co) أو Zoom SDK
- غرفة انتظار افتراضية + روابط للمريض
- وصفات رقمية post-televisit تلقائية

### المجموعة C: سريري
- تحسين LLM: ربط OpenAI/Azure مع human-in-the-loop
- Voice dictation streaming
- Nursing mobile eMAR page

### المجموعة D: تكامل
- PACS connector (Orthanc/DCM4CHE) production guide
- FHIR Patient/Appointment Subscription notifications

**مخرجات 90 يوم:** جاهزية **~78%** · telehealth MVP · patient payments

---

## Phase 2 — 6 أشهر

| المجال | مبادرات |
|--------|---------|
| **Home Health** | DocType Home Visit Request · تخطيط مسار · ربط LIS منزل |
| **RPM** | أجهزة Bluetooth/API (Withings, Apple Health import) |
| **AI Patient** | symptom checker + FAQ RAG على knowledge base المستشفى |
| **Radiology AI** | تكامل CAD API (partner) |
| **Medical Tourism v1** | باقات دولية · تسعير · coordinator workflow |
| **Native Mobile** | React Native shell (مريض + طبيب) |
| **Performance** | load test 10K appointments/day · Redis cache |
| **Compliance** | penetration test · DPIA GDPR |

**مخرجات 6 شهر:** جاهزية **~82%** · HIMSS EMRAM Stage 5–6

---

## Phase 3 — 12 شهر

- Population health dashboards + care gap automation
- Smart hospital: occupancy forecast ML · staffing optimizer
- Insurance appeals workflow كامل
- openEHR export optional
- JCI digital evidence pack
- Multi-language (5 لغات) للموقع والبوابة
- Teleradiology workflow
- Controlled substance track-and-trace

**مخرجات 12 شهر:** جاهزية **~87%** · ترتيب عالمي **~12–15**

---

## Phase 4 — 24 شهر

- AI clinical copilot (coding, diagnosis suggestions) مع governance board
- Full medical tourism (visa partner API, hotel, transfer)
- Wearable continuous monitoring ICU step-down
- Marketplace تكاملات (labs, PACS, payers)
- Multi-region DR (active-passive)
- HIMSS EMRAM Stage 7 assessment
- Certification path ISO 27001

**مخرجات 24 شهر:** جاهزية **~90–92%** · ترتيب **~8–12**

---

## Innovation Roadmap

| الابتكار | توقيت | الوصف |
|---------|-------|--------|
| Ambient AI scribe | 90d | ملاحظات من المحادثة مع مراجعة طبيب |
| Digital twin ward | 12m | محاكاة إشغال الأسرة |
| GenAI patient navigator | 6m | مساعد حجز ولغة طبيعية |
| Blockchain consent (optional) | 24m | سجل موافقات immutable |
| AR surgical planning | 24m | تكامل شركاء |

---

## مؤشرات النجاح (KPIs)

| KPI | اليوم | 12 شهر | 24 شهر |
|-----|-------|--------|--------|
| Patient digital adoption | ~40%* | 65% | 80% |
| Telehealth sessions/month | ~0 | 5K | 25K |
| Appointment booking online | ~50%* | 75% | 90% |
| Claim auto-submission | ~60%* | 85% | 95% |
| PHI incidents | target 0 | 0 | 0 |
| Consultant maturity score | 71 | 87 | 92 |

*تقديرات؛ تتطلب قياس production

---

## تبعيات تقنية

```
omnexa_healthcare (core HIS)
    ├── omnexa_experience (public web + portals)
    ├── omnexa_accounting (billing)
    ├── omnexa_consumer_finance (installments)
    └── third-party: WebRTC, FCM, PACS, LLM provider
```

---

*خارطة تطوير v2026.06.10 — مراجعة ربع سنوية*
