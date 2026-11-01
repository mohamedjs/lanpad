/* Production Landing Page for LANpad — Zero-dependency, Bilingual EN/AR, OS-aware live release binding */

const REPO = "mohamedjs/lanpad";
const STORAGE_PREFIX = "lanpad";

const T = {
  en: {
    "brand.name": "LANpad",
    "nav.download": "Download",
    "nav.features": "Features",
    "nav.architecture": "Architecture",
    "nav.faq": "FAQ",
    "hero.badge": "⚡ Ultra-low latency over local Wi-Fi",
    "hero.title": "Use your Mac trackpad or phone on any desktop.",
    "hero.lead": "Move, tap, glide, and type with zero lag. LANpad forwards raw binary pointer lock events and native keystrokes directly over your local network. No cloud, no lag, no drivers.",
    "hero.download": "Download for {os}",
    "hero.other": "Other platforms",
    "hero.version": "Version {v} · free & open source (MIT)",
    "hero.try": "Try Live Demo",
    "demo.connected": "Interactive Trackpad Demo",
    "demo.hint": "Glide mouse or drag touch here",
    "demo.left": "Left Click",
    "demo.right": "Right Click",
    "dl.title": "Get LANpad for your system",
    "dl.sub": "Run the server on the machine you want to control. Connect from any Mac, PC, iPhone or Android.",
    "dl.yours": "your device",
    "dl.copy": "Copy",
    "dl.copied": "Copied!",
    "dl.win.req": "Windows 10 or 11 (64-bit)",
    "dl.win.setup": "Download installer (.exe)",
    "dl.win.portable": "Portable zip (no install)",
    "dl.win.note": "Windows may show “Windows protected your PC” for new apps: choose More info → Run anyway.",
    "dl.mac.req": "macOS 12 Monterey or later",
    "dl.mac.arm": "Apple Silicon (M1–M4)",
    "dl.mac.intel": "Intel Mac (x86_64)",
    "dl.linux.req": "Ubuntu 20.04+, Debian, Fedora, Arch",
    "dl.linux.deb": "Download .deb (amd64)",
    "dl.linux.tar": "Portable .tar.gz",
    "dl.mob.expo": "Open Expo 58 App",
    "dl.mob.apk": "Download Android APK",
    "dl.all": "All releases",
    "feat.title": "Built for fluid precision",
    "feat.sub": "Designed to feel like the keyboard and mouse are directly wired to the machine.",
    "feat.speed.t": "5-Byte Binary Frames",
    "feat.speed.d": "Packs mouse moves into tight 5-byte delta buffers instead of heavy 30-byte JSON strings. Zero serialization overhead, zero lag.",
    "feat.gestures.t": "Native Momentum Gestures",
    "feat.gestures.d": "Two-finger scroll glides with sub-pixel momentum. Pinch-to-zoom and two-finger left/right swipes map seamlessly to workspace switching.",
    "feat.security.t": "Keyboard Lock & TLS",
    "feat.security.d": "Self-signed HTTPS unlocks Chrome's Keyboard Lock API so Esc, Tab, and Cmd shortcuts pass through directly without being eaten by macOS.",
    "feat.wifi.t": "Wi-Fi Power-Save Heartbeat",
    "feat.wifi.d": "Sends a 1-byte keepalive every 16ms during active capture so the laptop Wi-Fi radio never enters sleep state mid-drag.",
    "feat.mobile.t": "Expo 58 Mobile Remote",
    "feat.mobile.d": "Turn your phone or tablet into an emergency wireless touchpad and keyboard with tap-to-click, scroll bars, and haptic feedback.",
    "feat.privacy.t": "100% Local & Private",
    "feat.privacy.d": "Traffic never leaves your local Wi-Fi network. Protected with a constant-time secret token generated on your host machine.",
    "arch.title": "Modular Monolith Architecture",
    "arch.sub": "Clean, decoupled domain architecture inspired by Lura.",
    "faq.title": "Frequently Asked Questions",
    "faq.1.q": "Do I need to install anything on the Mac or client laptop?",
    "faq.1.a": "No! Open the URL printed by LANpad in Chrome or any Chromium browser. Pointer Lock and full keyboard capture work right inside the browser.",
    "faq.2.q": "How does the phone / tablet app work?",
    "faq.2.a": "The mobile app is built with modern Expo 58 (React Native). It connects to the same LANpad WebSocket port over Wi-Fi and provides a touch trackpad with haptic feedback.",
    "faq.3.q": "Why does Chrome ask about a self-signed certificate when --tls is on?",
    "faq.3.a": "LANpad generates a local certificate on your machine for HTTPS. Chrome requires a secure context (HTTPS) to unlock the Keyboard Lock API so full-screen Esc, Tab, and Cmd keys reach your remote desktop."
  },
  ar: {
    "brand.name": "LANpad",
    "nav.download": "التحميل",
    "nav.features": "المميزات",
    "nav.architecture": "البنية البرمجية",
    "nav.faq": "الأسئلة الشائعة",
    "hero.badge": "⚡ سرعة واستجابة فائقة عبر شبكة Wi-Fi المحلية",
    "hero.title": "تحكم في حاسوبك عبر تراك باد الماك أو هاتفك.",
    "hero.lead": "تحريك وتمرير ونقر وكتابة بدون أي تأخير. يقوم LANpad بإرسال حركة المؤشر بصيغة ثنائية خفيفة واختصارات لوحة المفاتيح مباشرة عبر شبكتك المحلية. لا خوادم خارجية، ولا تأخير.",
    "hero.download": "تحميل لـ {os}",
    "hero.other": "أنظمة أخرى",
    "hero.version": "إصدار {v} · مجاني ومفتوح المصدر (MIT)",
    "hero.try": "جرب المحاكي المباشر",
    "demo.connected": "محاكي لوحة اللمس التفاعلية",
    "demo.hint": "حرك الماوس أو المس الشاشة هنا للتجربة",
    "demo.left": "نقرة يسار",
    "demo.right": "نقرة يمين",
    "dl.title": "حمّل LANpad لنظام تشغيلك",
    "dl.sub": "شغّل الخادم على الجهاز الذي تريد التحكم به، واتصل من الماك أو الويندوز أو الآيفون أو الأندرويد.",
    "dl.yours": "جهازك الحالي",
    "dl.copy": "نسخ",
    "dl.copied": "تم النسخ!",
    "dl.win.req": "ويندوز 10 أو 11 (64 بت)",
    "dl.win.setup": "برنامج التثبيت (.exe)",
    "dl.win.portable": "نسخة محمولة ZIP (بدون تثبيت)",
    "dl.win.note": "قد يُظهر ويندوز رسالة حماية للتطبيقات الجديدة: اختر More info ثم Run anyway.",
    "dl.mac.req": "macOS 12 أو أحدث",
    "dl.mac.arm": "معالجات آبل سيليكون (M1–M4)",
    "dl.mac.intel": "معالجات إنتل (x86_64)",
    "dl.linux.req": "أوبونتو، ديبيان، فيدورا، وآرش",
    "dl.linux.deb": "تحميل .deb (لينكس)",
    "dl.linux.tar": "نسخة محمولة .tar.gz",
    "dl.mob.expo": "فتح تطبيق Expo 58",
    "dl.mob.apk": "تحميل تطبيق أندرويد APK",
    "dl.all": "كل الإصدارات",
    "feat.title": "دقة وانسيابية استثنائية",
    "feat.sub": "صُمم ليعطيك إحساس أن الفأرة ولوحة المفاتيح متصلة بسلك مباشر.",
    "feat.speed.t": "حزم ثنائية بـ 5 بايت فقط",
    "feat.speed.d": "يتم ضغط حركات الفأرة في حزم ثنائية فائقة الخفة بدلاً من نصوص JSON الثقيلة، لضمان استجابة صفرية التأخير.",
    "feat.gestures.t": "إيماءات طبيعية وسلسة",
    "feat.gestures.d": "تمرير سلس بإصبعين مع فيزياء القصور الذاتي، وتكبير/تصغير، والتبديل بين مساحات العمل بسهولة.",
    "feat.security.t": "قفل المفاتيح والتشفير",
    "feat.security.d": "اتصال HTTPS آمن يفعّل ميزة Keyboard Lock في كروم لعدم فقدان أزرار Esc و Tab و Cmd في الماك.",
    "feat.wifi.t": "نبضات منع خمول الواي فاي",
    "feat.wifi.d": "إرسال نبضة خفيفة كل 16ms أثناء الاستخدام النشط لمنع بطاقة الواي فاي من الدخول في وضع توفير الطاقة.",
    "feat.mobile.t": "تطبيق محمول Expo 58",
    "feat.mobile.d": "حول هاتفك أو جهازك اللوحي إلى تراك باد ولوحة مفاتيح لاسلكية متكاملة مع اهتزازات تفاعلية.",
    "feat.privacy.t": "محلي 100% وآمن",
    "feat.privacy.d": "البيانات لا تغادر شبكتك المحلية إطلاقاً، ومحمية برمز دخول سري ثابت يتم توليده محلياً.",
    "arch.title": "بنية برمجية معيارية متكاملة",
    "arch.sub": "تصميم modular monolith نظيف وعالي الجودة مستوحى من بنية Lura.",
    "faq.title": "الأسئلة الشائعة",
    "faq.1.q": "هل أحتاج تثبيت أي برنامج على جهاز الماك؟",
    "faq.1.a": "لا! يكفي فتح الرابط المطبوع في متصفح كروم، وستعمل لوحة اللمس والمفاتيح فوراً داخل المتصفح.",
    "faq.2.q": "كيف يعمل تطبيق الهاتف والأجهزة اللوحية؟",
    "faq.2.a": "التطبيق مبني بتقنية Expo 58 (React Native الحديثة)، يتصل مباشرة بمنفذ الخادم ويوفر لوحة لمس واهتزازات لمسية سلسة.",
    "faq.3.q": "لماذا يظهر تحذير الشهادة عند تفعيل --tls؟",
    "faq.3.a": "لأن الشهادة مولدة محلياً على جهازك؛ متصفح كروم يشترط اتصال HTTPS لفتح صلاحيات Keyboard Lock الكاملة."
  }
};

const OS_NAMES = { windows: "Windows", macos: "macOS", linux: "Linux", mobile: "Mobile" };
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
};

let lang = store.get(`${STORAGE_PREFIX}_lang`) || ((navigator.language || "").startsWith("ar") ? "ar" : "en");
let release = null;
const detectedOS = detectOS();

function t(key, vars = {}) {
  let s = (T[lang] && T[lang][key]) || T.en[key] || key;
  for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v);
  return s;
}

function detectOS() {
  const ua = navigator.userAgent || "";
  const p = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
  if (/android|iphone|ipad|ipod/i.test(ua)) return "mobile";
  if (/win/i.test(p) || /windows/i.test(ua)) return "windows";
  if (/mac/i.test(p) || /mac os x/i.test(ua)) return "macos";
  if (/linux|x11|cros/i.test(p + ua)) return "linux";
  return "linux";
}

const PICK = {
  setup: /-Setup-.*\.exe$/i,
  portable: /windows-x64-.*\.zip$/i,
  "mac-arm": /macos-arm64.*\.(zip|tar\.gz)$/i,
  "mac-intel": /macos-x86_64.*\.(zip|tar\.gz)$/i,
  deb: /_amd64\.deb$/i,
  tar: /linux-x86_64.*\.(tar\.gz|zip)$/i,
  apk: /.*\.apk$/i,
  sums: /^SHA256SUMS/i,
};

async function loadRelease() {
  for (const url of ["release.json", `https://api.github.com/repos/${REPO}/releases/latest`]) {
    try {
      const res = await fetch(url, { cache: "no-cache" });
      if (res.ok) {
        const data = await res.json();
        if (data && data.assets) return data;
      }
    } catch {}
  }
  return null;
}

function asset(kind) {
  return release && release.assets.find((a) => PICK[kind] && PICK[kind].test(a.name));
}

function humanSize(bytes) {
  if (!bytes) return "";
  const mb = bytes / (1024 * 1024);
  return ` · ${mb.toFixed(1)} MB`;
}

function renderDownloads() {
  const fallback = `https://github.com/${REPO}/releases/latest`;
  if ($("#all-releases")) $("#all-releases").href = `https://github.com/${REPO}/releases`;

  $$("[data-asset]").forEach((el) => {
    const kind = el.getAttribute("data-asset");
    const a = asset(kind);
    const key = `dl.${el.closest("[data-os]")?.getAttribute("data-os") || "linux"}.${kind}`;
    const base = t(key);
    if (a) {
      el.href = a.browser_download_url;
      el.textContent = base + humanSize(a.size);
    } else {
      el.href = fallback;
      el.textContent = base;
    }
  });

  const sums = asset("sums");
  if ($("#checksums") && sums) {
    $("#checksums").href = sums.browser_download_url;
  }

  // Bind hero download CTA
  const heroBtn = $("#hero-download");
  const heroText = $("#hero-download-text");
  const heroIcon = $("#hero-os-icon");
  const osKey = detectedOS;
  const osName = OS_NAMES[osKey] || "Linux";
  const icons = { windows: "🪟", macos: "🍏", linux: "🐧", mobile: "📱" };

  if (heroIcon) heroIcon.textContent = icons[osKey] || "🐧";
  if (heroText) heroText.textContent = t("hero.download", { os: osName });

  const heroAssetMap = { windows: "setup", macos: "mac-arm", linux: "deb", mobile: "expo" };
  const heroAsset = asset(heroAssetMap[osKey]);
  if (heroBtn) {
    if (heroAsset) {
      heroBtn.href = heroAsset.browser_download_url;
    } else {
      heroBtn.href = "#download";
    }
  }

  // Highlight platform card
  $$(".platform").forEach((card) => {
    const isMine = card.getAttribute("data-os") === detectedOS;
    card.classList.toggle("active", isMine);
    card.classList.toggle("mine", isMine);
  });
}

function setLang(newLang) {
  lang = newLang;
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

  $$("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (T[lang] && T[lang][key]) {
      el.textContent = T[lang][key];
    }
  });

  $$("#lang-switch button").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-value") === lang);
  });

  store.set(`${STORAGE_PREFIX}_lang`, lang);
  renderDownloads();
}

function initTheme() {
  const saved = store.get(`${STORAGE_PREFIX}_theme`) || "dark";
  document.documentElement.setAttribute("data-theme", saved);

  $("#theme-toggle")?.addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "dark";
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    store.set(`${STORAGE_PREFIX}_theme`, next);
  });
}

function initLiveSimulator() {
  const surface = $("#demo-surface");
  const pointer = $("#demo-pointer");
  const hint = $("#surface-hint");
  const statPackets = $("#stat-packets");
  const statPos = $("#stat-pos");

  if (!surface || !pointer) return;

  let packetCount = 0;
  let lastX = 0, lastY = 0;

  function updateTouch(e) {
    const rect = surface.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

    const x = Math.max(0, Math.min(rect.width, clientX - rect.left));
    const y = Math.max(0, Math.min(rect.height, clientY - rect.top));

    pointer.style.display = "block";
    pointer.style.left = `${x}px`;
    pointer.style.top = `${y}px`;
    if (hint) hint.style.opacity = "0";

    const dx = Math.round(x - lastX);
    const dy = Math.round(y - lastY);
    lastX = x;
    lastY = y;

    packetCount += 1;
    if (statPackets) statPackets.textContent = `${packetCount} binary packets`;
    if (statPos) statPos.textContent = `ΔX: ${dx} ΔY: ${dy} · (${Math.round(x)}, ${Math.round(y)})`;
  }

  surface.addEventListener("mousemove", updateTouch);
  surface.addEventListener("touchmove", updateTouch, { passive: true });

  surface.addEventListener("mouseleave", () => {
    pointer.style.display = "none";
    if (hint) hint.style.opacity = "0.6";
  });

  $("#btn-left-click")?.addEventListener("click", () => {
    packetCount += 1;
    if (statPackets) statPackets.textContent = `${packetCount} binary packets (Left Click)`;
  });

  $("#btn-right-click")?.addEventListener("click", () => {
    packetCount += 1;
    if (statPackets) statPackets.textContent = `${packetCount} binary packets (Right Click)`;
  });
}

function initCopyButtons() {
  $$(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-copy");
      if (text) {
        navigator.clipboard.writeText(text).then(() => {
          const old = btn.textContent;
          btn.textContent = t("dl.copied") || "✓";
          setTimeout(() => { btn.textContent = old; }, 1500);
        });
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  setLang(lang);

  $$("#lang-switch button").forEach((btn) => {
    btn.addEventListener("click", () => {
      setLang(btn.getAttribute("data-value"));
    });
  });

  initLiveSimulator();
  initCopyButtons();

  // Load latest GitHub release metadata and bind assets
  release = await loadRelease();
  renderDownloads();
  if (release && $("#hero-version")) {
    const v = (release.tag_name || "").replace(/^v/, "") || "1.0.0";
    $("#hero-version").textContent = t("hero.version", { v });
  }
});
