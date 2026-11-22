// نصوص الواجهة حسب لغة الصفحة (<html lang>)
const EN = document.documentElement.lang === "en";
const RTL = document.documentElement.dir === "rtl";
const T = EN ? {
  pause: "Pause slideshow", play: "Play slideshow",
  missing: "Your request was not sent. Please fill in your name, organization, and need, then try again.",
  noReach: "Your request was not sent. Please add an email or mobile number so we can get back to you.",
  noConsent: "Your request was not sent. Please agree to the Privacy Policy first.",
  subject: "Contact request from ", ok: "We have received your request. Thank you for getting in touch. ",
  name: "Name: ", org: "Organization: ", reach: "Contact: ", type: "Type of need: ",
  fallback: (email) => "We couldn't send your request directly, so we opened your email program with a ready-made message. Please send it from there, or email us directly at " + email + ".",
} : {
  pause: "إيقاف العرض", play: "تشغيل العرض",
  missing: "لم يُرسَل الطلب. تأكد من تعبئة الاسم والجهة والاحتياج، ثم حاول مرة أخرى.",
  noReach: "لم يُرسَل الطلب. أضف بريدًا أو رقم جوال لنعود إليك عليه.",
  noConsent: "لم يُرسَل الطلب. وافق على سياسة الخصوصية أولًا.",
  subject: "طلب تواصل من ", ok: "وصلنا طلبك، شكرًا لتواصلك. ",
  name: "الاسم: ", org: "الجهة: ", reach: "للتواصل: ", type: "نوع الاحتياج: ",
  fallback: (email) => "تعذّر الإرسال المباشر الآن، فتحنا لك برنامج البريد برسالة جاهزة. أكمل الإرسال منه، أو راسلنا مباشرة على " + email + ".",
};

// القائمة: الجوال والقوائم المنسدلة
const nav = document.getElementById("nav");
const menuBtn = document.getElementById("menuBtn");
const megaButtons = [...nav.querySelectorAll(".item > button")];
const closeMenus = (except) => {
  megaButtons.forEach((b) => {
    if (b === except) return;
    b.setAttribute("aria-expanded", "false");
    b.nextElementSibling.classList.remove("open");
  });
};
megaButtons.forEach((b) => {
  b.addEventListener("click", () => {
    const open = b.getAttribute("aria-expanded") !== "true";
    closeMenus(b);
    b.setAttribute("aria-expanded", open);
    b.nextElementSibling.classList.toggle("open", open);
  });
});
menuBtn.addEventListener("click", () => {
  const open = nav.classList.toggle("open");
  menuBtn.setAttribute("aria-expanded", open);
});
document.addEventListener("click", (e) => { if (!e.target.closest(".top")) closeMenus(); });
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  closeMenus();
  nav.classList.remove("open");
  menuBtn.setAttribute("aria-expanded", "false");
});

// لوحة الصور في أعلى الرئيسية: تتبدل كل 5 ثوانٍ، ويوقفها الزر. لا تتحرك لمن يفضّل تقليل الحركة.
const media = document.getElementById("media");
if (media) {
  const figs = [...media.querySelectorAll("figure")];
  const dots = [...media.querySelectorAll(".dots i")];
  const pause = document.getElementById("pause");
  let i = 0, timer = null;
  let playing = !matchMedia("(prefers-reduced-motion: reduce)").matches;
  const show = (n) => {
    i = (n + figs.length) % figs.length;
    figs.forEach((f, k) => { f.classList.toggle("on", k === i); f.setAttribute("aria-hidden", k === i ? "false" : "true"); const a = f.querySelector("a"); if (a) a.tabIndex = k === i ? 0 : -1; });
    dots.forEach((d, k) => d.classList.toggle("on", k === i));
  };
  const icon = () => {
    pause.setAttribute("aria-label", playing ? T.pause : T.play);
    pause.querySelector("path").setAttribute("d", playing ? "M4 2h3v12H4zM9 2h3v12H9z" : "M4 2l10 6-10 6z");
  };
  const run = () => { clearInterval(timer); if (playing) timer = setInterval(() => show(i + 1), 5000); };
  pause.addEventListener("click", () => { playing = !playing; icon(); run(); });
  icon(); run();
}

// تبويبات «ابدأ من هنا»
const tabs = [...document.querySelectorAll('[role="tab"]')];
const selectTab = (t) => tabs.forEach((x) => {
  const on = x === t;
  x.setAttribute("aria-selected", on);
  x.tabIndex = on ? 0 : -1;
  document.getElementById(x.getAttribute("aria-controls")).hidden = !on;
});
tabs.forEach((t, k) => {
  t.addEventListener("click", () => selectTab(t));
  t.addEventListener("keydown", (e) => {
    // السهم باتجاه القراءة ينتقل إلى التبويب التالي: يسار في العربية، يمين في الإنجليزية
    const next = RTL ? "ArrowLeft" : "ArrowRight", prev = RTL ? "ArrowRight" : "ArrowLeft";
    const d = e.key === next ? 1 : e.key === prev ? -1 : 0;
    if (!d) return;
    const n = tabs[(k + d + tabs.length) % tabs.length];
    selectTab(n); n.focus();
  });
});

// نموذج التواصل (صفحة contact.html فقط)
// يُرسَل الطلب إلى Web3Forms (action في النموذج) فيصل إلى بريد الشركة المسجّل بمفتاح access_key.
// إن تعذّر الإرسال المباشر يفتح برنامج البريد برسالة جاهزة إلى data-email.
const lead = document.getElementById("lead");
if (lead) {
  const submitBtn = lead.querySelector('button[type="submit"]');
  lead.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("fMsg");
    const val = (id) => document.getElementById(id).value.trim();
    const show = (text, isError) => {
      msg.className = isError ? "msg err" : "msg";
      msg.textContent = text;
      msg.hidden = false;
    };
    if (!val("fName") || !val("fOrg") || !val("fNeed")) return show(T.missing, true);
    if (!val("fReach")) return show(T.noReach, true);
    if (!document.getElementById("fOk").checked) return show(T.noConsent, true);

    submitBtn.disabled = true;
    try {
      const data = Object.fromEntries(new FormData(lead));
      data.subject = T.subject + val("fOrg");
      const res = await fetch(lead.action, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(data),
      });
      const out = await res.json().catch(() => ({}));
      if (!res.ok || !out.success) throw new Error(out.message || "HTTP " + res.status);
      lead.reset();
      show(T.ok + (lead.dataset.response || ""), false);
    } catch (err) {
      const type = val("fType");
      const subject = T.subject + val("fOrg");
      const body = [T.name + val("fName"), T.org + val("fOrg"), T.reach + val("fReach"),
        type ? T.type + type : "", "", val("fNeed")].filter((x, i) => x || i === 4).join("\n");
      window.location.href = "mailto:" + lead.dataset.email + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
      show(T.fallback(lead.dataset.email), true);
    } finally {
      submitBtn.disabled = false;
    }
  });
}
