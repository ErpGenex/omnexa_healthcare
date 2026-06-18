/* Interactive FDI dental arch — Omnexa Healthcare */
(function () {
	"use strict";

	const UPPER_ORDER = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
	const LOWER_ORDER = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

	function archCoords(ids, cx, cy, rx, ry, startDeg, endDeg) {
		return ids.map((id, i) => {
			const frac = ids.length > 1 ? i / (ids.length - 1) : 0.5;
			const deg = startDeg + frac * (endDeg - startDeg);
			const rad = (deg * Math.PI) / 180;
			return { id: String(id), x: cx + rx * Math.cos(rad), y: cy + ry * Math.sin(rad), rot: deg + 90 };
		});
	}

	function toothState(tooth, data, state) {
		const tid = String(tooth.tooth_id || tooth);
		if (state.selectedTooth === tid) return "selected";
		const lessons = tooth.lessons || [];
		if (lessons.some((l) => l.status === "completed")) return "completed";
		if (lessons.length || tooth.has_lessons) return "available";
		const lessonTeeth = (state.highlightTeeth || []).map(String);
		if (lessonTeeth.length && lessonTeeth.includes(tid)) return "lesson";
		return "locked";
	}

	function toothSvg(coord, tooth, stateClass) {
		const w = 34;
		const h = 44;
		const x = coord.x - w / 2;
		const y = coord.y - h / 2;
		const label = coord.id;
		return `<g class="oj-dental-tooth oj-dental-tooth--${stateClass}" data-tooth="${label}" transform="translate(${x},${y}) rotate(${coord.rot - 90},${w / 2},${h / 2})">
			<path class="oj-dental-tooth-shape" d="M6 4 Q17 0 28 4 L30 18 Q17 42 4 18 Z" />
			<text x="17" y="24" text-anchor="middle" class="oj-dental-tooth-num">${label}</text>
		</g>`;
	}

	function buildArchSvg(data, state) {
		const teethMap = {};
		(data.teeth || []).forEach((t) => {
			teethMap[String(t.tooth_id)] = t;
		});
		const upper = archCoords(UPPER_ORDER, 400, 195, 290, 95, 205, 335);
		const lower = archCoords(LOWER_ORDER, 400, 355, 290, 95, 25, 155);
		const upperG = upper
			.map((c) => toothSvg(c, teethMap[c.id] || { tooth_id: c.id }, toothState(teethMap[c.id] || { tooth_id: c.id }, data, state)))
			.join("");
		const lowerG = lower
			.map((c) => toothSvg(c, teethMap[c.id] || { tooth_id: c.id }, toothState(teethMap[c.id] || { tooth_id: c.id }, data, state)))
			.join("");
		return `<svg class="oj-dental-svg" viewBox="0 0 800 520" role="img" aria-label="FDI dental chart">
			<defs>
				<linearGradient id="oj-jaw-bg" x1="0%" y1="0%" x2="0%" y2="100%">
					<stop offset="0%" stop-color="#1e293b"/>
					<stop offset="100%" stop-color="#0f172a"/>
				</linearGradient>
				<filter id="oj-tooth-glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
			</defs>
			<rect width="800" height="520" fill="url(#oj-jaw-bg)" rx="16"/>
			<ellipse cx="400" cy="270" rx="320" ry="200" fill="none" stroke="#334155" stroke-width="1" opacity="0.35"/>
			<text x="400" y="42" text-anchor="middle" class="oj-dental-svg-title">${window.OmnexaJourney ? OmnexaJourney.t("الفك العلوي", "Upper Jaw") : "Upper Jaw"}</text>
			<text x="400" y="498" text-anchor="middle" class="oj-dental-svg-title">${window.OmnexaJourney ? OmnexaJourney.t("الفك السفلي", "Lower Jaw") : "Lower Jaw"}</text>
			<g class="oj-dental-upper">${upperG}</g>
			<g class="oj-dental-lower">${lowerG}</g>
		</svg>`;
	}

	function yearButtons(years, current) {
		const OJ = window.OmnexaJourney;
		return years
			.map((y) => {
				const labels = [
					OJ.t("الأولى", "First"),
					OJ.t("الثانية", "Second"),
					OJ.t("الثالثة", "Third"),
					OJ.t("الرابعة", "Fourth"),
					OJ.t("الخامسة", "Fifth"),
				];
				const cls = current === y ? "is-active" : "";
				return `<button type="button" class="oj-dental-year-btn ${cls}" data-year="${y}"><span class="oj-dental-year-num">${y}</span><span class="oj-dental-year-lbl">${labels[y - 1] || y}</span></button>`;
			})
			.join("");
	}

	function lessonList(lessons, state) {
		const OJ = window.OmnexaJourney;
		if (!lessons.length) {
			return `<p class="oj-dental-muted">${OJ.t("لا دروس لهذه السنة", "No lessons for this year")}</p>`;
		}
		return lessons
			.map((les, idx) => {
				const done = les.status === "completed";
				const active = state.selectedLesson === les.id;
				return `<button type="button" class="oj-dental-lesson-row ${done ? "is-done" : ""} ${active ? "is-active" : ""}" data-lesson="${OJ.esc(les.id)}">
					<span class="oj-dental-lesson-idx">${idx + 1}</span>
					<span class="oj-dental-lesson-text">
						<strong>${OJ.esc(les.title_ar || les.title_en)}</strong>
						<small>${OJ.esc(les.title_en || "")}</small>
					</span>
				</button>`;
			})
			.join("");
	}

	function selectedPanel(data, state) {
		const OJ = window.OmnexaJourney;
		const tooth = (data.teeth || []).find((t) => String(t.tooth_id) === String(state.selectedTooth));
		const lesson = (data.year_lessons || []).find((l) => l.id === state.selectedLesson);
		if (!tooth && !lesson) {
			return `<div class="oj-dental-side-card">
				<h4>${OJ.t("السن المختار", "Selected Tooth")}</h4>
				<p class="oj-dental-muted">${OJ.t("اضغط على سن في المخطط أو اختر درسًا", "Click a tooth or pick a lesson")}</p>
			</div>`;
		}
		let html = "";
		if (tooth) {
			const lesRows = (tooth.lessons || [])
				.map((les) => {
					const done = les.status === "completed";
					return `<div class="oj-dental-lesson-mini ${done ? "is-done" : ""}">
						<strong>${OJ.esc(les.title_ar || les.title_en)}</strong>
						<button type="button" class="oj-btn oj-btn-sm ${done ? "oj-btn-outline" : "oj-btn-primary"} oj-complete-lesson" data-lesson="${OJ.esc(les.id)}" ${done || !state.patient ? "disabled" : ""}>${done ? OJ.t("مكتمل", "Done") : OJ.t("إكمال", "Complete")}</button>
					</div>`;
				})
				.join("");
			html += `<div class="oj-dental-side-card">
				<h4>${OJ.t("السن المختار", "Selected Tooth")}</h4>
				<div class="oj-dental-tooth-badge">${OJ.esc(tooth.tooth_id)}</div>
				<p><strong>${OJ.esc(tooth.label_ar)}</strong></p>
				<p class="oj-dental-muted">${OJ.esc(tooth.label_en)}</p>
				${lesRows || ""}
			</div>`;
		}
		if (lesson) {
			html += `<div class="oj-dental-side-card">
				<h4>${OJ.t("الدرس", "Lesson")}</h4>
				<p><strong>${OJ.esc(lesson.title_ar)}</strong></p>
				<p class="oj-dental-muted">${OJ.esc(lesson.title_en)}</p>
				${lesson.teeth && lesson.teeth.length ? `<p class="oj-dental-muted">${OJ.t("الأسنان", "Teeth")}: ${lesson.teeth.join(", ")}</p>` : ""}
			</div>`;
		}
		return html;
	}

	function legendHtml() {
		const OJ = window.OmnexaJourney;
		return `<div class="oj-dental-side-card oj-dental-legend-card">
			<h4>${OJ.t("مفتاح الألوان", "Color Key")}</h4>
			<ul class="oj-dental-legend oj-dental-legend--dark">
				<li><span class="oj-legend-dot available"></span>${OJ.t("دروس متاحة", "Available lessons")}</li>
				<li><span class="oj-legend-dot lesson"></span>${OJ.t("درس السنة", "Year lesson")}</li>
				<li><span class="oj-legend-dot selected"></span>${OJ.t("السن المحدد", "Selected tooth")}</li>
				<li><span class="oj-legend-dot completed"></span>${OJ.t("مكتمل", "Completed")}</li>
				<li><span class="oj-legend-dot locked"></span>${OJ.t("بدون درس", "No lesson")}</li>
			</ul>
		</div>`;
	}

	function render($body, data, state, handlers) {
		const OJ = window.OmnexaJourney;
		const years = [1, 2, 3, 4, 5];
		const year = state.academicYear || data.academic_year || 1;
		const lessons = data.year_lessons || [];
		$body.html(`
			<div class="oj-dental-studio">
				<aside class="oj-dental-years">
					<h5>${OJ.t("اختر السنة الدراسية", "Select Academic Year")}</h5>
					${yearButtons(years, year)}
				</aside>
				<aside class="oj-dental-lessons">
					<h5>${OJ.t("دروس السنة", "Year Lessons")} ${year}</h5>
					<div class="oj-dental-lesson-list">${lessonList(lessons, state)}</div>
					<button type="button" class="oj-btn oj-btn-sm oj-btn-outline oj-dental-show-all">${OJ.t("عرض كل الدروس", "Show all lessons")}</button>
				</aside>
				<main class="oj-dental-chart-main">
					${OJ.patientSearchBar({ placeholder: OJ.t("مريض العيادة (اختياري)", "Clinic patient (optional)") })}
					<div class="oj-dental-svg-wrap">${buildArchSvg(data, state)}</div>
				</main>
				<aside class="oj-dental-side">
					${selectedPanel(data, state)}
					${legendHtml()}
				</aside>
			</div>
		`);
		OJ.bindPatientSearch($body, handlers.onPatient, handlers.branch);
		$body.find(".oj-dental-year-btn").on("click", function () {
			handlers.onYear(parseInt($(this).attr("data-year"), 10) || 1);
		});
		$body.find(".oj-dental-lesson-row").on("click", function () {
			const id = $(this).attr("data-lesson");
			const les = lessons.find((l) => l.id === id);
			handlers.onLesson(id, (les && les.teeth) || []);
		});
		$body.find(".oj-dental-tooth").on("click", function () {
			handlers.onTooth($(this).attr("data-tooth"));
		});
		$body.find(".oj-complete-lesson").on("click", function () {
			handlers.onCompleteLesson($(this).attr("data-lesson"));
		});
		$body.find(".oj-dental-show-all").on("click", () => handlers.onShowAllLessons());
	}

	window.omnexa_healthcare = window.omnexa_healthcare || {};
	window.omnexa_healthcare.dentalChart = { render, UPPER_ORDER, LOWER_ORDER };
})();
