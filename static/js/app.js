/**
 * 常州市智能医疗推荐系统 - 前端逻辑
 */
var API = "/api";

// ========== 工具函数 ==========
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }
function toast(msg) {
  var t = $("#toast");
  if (t) { t.textContent = msg; t.classList.add("show"); setTimeout(function() { t.classList.remove("show"); }, 2500); }
}
function esc(str) {
  var div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}
function uiIcon(name, extraClass) {
  return '<span class="icon-symbol icon-' + name + (extraClass ? " " + extraClass : "") + '"></span>';
}

function normalizeDoctorName(name) {
  return String(name || "")
    .replace(/\s+/g, "")
    .replace(/主任医师|副主任医师|主治医师|住院医师|教授|副教授|博士生导师|硕士研究生导师|医学博士|博士|硕士|，|,|、|。|（.*?）|\\(.*?\\)/g, "");
}

function photoPathFromManifestFile(file) {
  var name = String(file || "").replace(/\\/g, "/").split("/").pop();
  return name ? "/static/images/doctors/czfph_323/" + encodeURIComponent(name) : "";
}

function loadDoctorPhotoManifest() {
  return fetch("/static/images/doctors/czfph_323/manifest.json?v=photos10")
    .then(function(res) { return res.ok ? res.json() : []; })
    .then(function(list) {
      window._doctorPhotoMap = {};
      (list || []).forEach(function(item) {
        var key = normalizeDoctorName(item.name);
        var hospitalKey = key + "@" + normalizeDoctorName(item.hospital || item.hospital_name || "");
        var url = item.url || item.photo_url || photoPathFromManifestFile(item.file);
        if (key && url) {
          if (item.hospital || item.hospital_name) window._doctorPhotoMap[hospitalKey] = url;
          if (!window._doctorPhotoMap[key]) window._doctorPhotoMap[key] = url;
        }
      });
      return window._doctorPhotoMap;
    })
    .catch(function() {
      window._doctorPhotoMap = {};
      return window._doctorPhotoMap;
    });
}

function loadHospitalLogoManifest() {
  return fetch("/static/images/hospitals/manifest.json?v=logo5")
    .then(function(res) { return res.ok ? res.json() : {}; })
    .then(function(map) {
      window._hospitalLogoMap = map || {};
      return window._hospitalLogoMap;
    })
    .catch(function() {
      window._hospitalLogoMap = {};
      return window._hospitalLogoMap;
    });
}

function resolveDoctorPhoto(d) {
  if (!d) return "";
  if (d._photo_url) return d._photo_url;
  if (d.photo_url) return d.photo_url;
  if (d.image_url) return d.image_url;
  var map = window._doctorPhotoMap || {};
  var key = normalizeDoctorName(d.name);
  var hospitalKey = key + "@" + normalizeDoctorName(d.hospital_name || d.hospital || "");
  return map[hospitalKey] || map[key] || "";
}

function resolveHospitalLogo(h) {
  if (!h) return "";
  var map = window._hospitalLogoMap || {};
  var item = map[String(h.id)];
  return item && (item.icon_url || item.url) ? (item.icon_url || item.url) : "";
}

function hospitalLogoHtml(h, cls) {
  var logo = resolveHospitalLogo(h);
  if (!logo) return uiIcon("hospital", cls || "icon-inline");
  return '<img class="hospital-logo-img ' + (cls || "") + '" src="' + esc(logo) + '" alt="' + esc((h && h.name) || "医院图标") + '" onerror="this.style.display=&quot;none&quot;;this.parentNode.classList.add(&quot;logo-fallback&quot;);">' + uiIcon("hospital", "logo-fallback-icon");
}

function cacheHospital(h) {
  if (!h || h.id == null) return h;
  window._hospitalCache = window._hospitalCache || {};
  window._hospitalCache[String(h.id)] = h;
  return h;
}

function getHospitalById(hid) {
  var key = String(hid);
  if (window._hospitalCache && window._hospitalCache[key]) return window._hospitalCache[key];
  var pools = [window._hospitals, window._dashboardHospitals];
  for (var p = 0; p < pools.length; p++) {
    var list = pools[p] || [];
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === key) return cacheHospital(list[i]);
    }
  }
  return null;
}

function openHospitalNavigation(hid) {
  var h = getHospitalById(hid);
  if (!h) {
    toast("暂无该医院导航信息");
    return;
  }
  var name = h.name || "医院";
  var address = h.address || "";
  var lat = parseFloat(h.lat);
  var lng = parseFloat(h.lng);
  var url = "";
  if (isFinite(lat) && isFinite(lng)) {
    url = "https://uri.amap.com/navigation?to=" + encodeURIComponent(lng + "," + lat + "," + name) + "&mode=car&policy=1&callnative=0";
  } else {
    url = "https://www.amap.com/search?query=" + encodeURIComponent(name + " " + address);
  }
  window.open(url, "_blank", "noopener");
}

function doctorAvatarHtml(d, cls) {
  var photo = resolveDoctorPhoto(d);
  if (photo) {
    return '<img class="doctor-photo ' + (cls || "") + '" src="' + esc(photo) + '" alt="' + esc((d && d.name) || "医生照片") + '" onerror="this.style.display=&quot;none&quot;;this.parentNode.classList.add(&quot;photo-fallback&quot;);">';
  }
  return uiIcon("doctor", "icon-lg");
}

function doctorHasPhoto(d) {
  return !!resolveDoctorPhoto(d);
}

function sortDoctorsPhotoFirst(list) {
  return (list || []).slice().sort(function(a, b) {
    var pa = doctorHasPhoto(a) ? 0 : 1;
    var pb = doctorHasPhoto(b) ? 0 : 1;
    if (pa !== pb) return pa - pb;
    var ha = a.hospital_id || 0;
    var hb = b.hospital_id || 0;
    if (ha !== hb) return ha - hb;
    var da = a._department_group || normalizeDepartmentName(a.department);
    var db = b._department_group || normalizeDepartmentName(b.department);
    var dc = String(da || "").localeCompare(String(db || ""), "zh-CN");
    if (dc !== 0) return dc;
    return String(a.name || "").localeCompare(String(b.name || ""), "zh-CN");
  });
}

function sortDoctorItemsPhotoFirst(items) {
  return (items || []).slice().sort(function(a, b) {
    var da = a && a.doctor ? a.doctor : a;
    var db = b && b.doctor ? b.doctor : b;
    var pa = doctorHasPhoto(da) ? 0 : 1;
    var pb = doctorHasPhoto(db) ? 0 : 1;
    if (pa !== pb) return pa - pb;
    return 0;
  });
}

function fillLoginDemo() {
  var user = document.getElementById("loginDialogUser") || document.getElementById("loginHeroUser");
  var pass = document.getElementById("loginDialogPass") || document.getElementById("loginHeroPass");
  if (user) user.value = "user";
  if (pass) pass.value = "123456";
  toast("已填入演示账号");
}

function selectLoginRole(btn) {
  if (!btn) return;
  $$(".login-role").forEach(function(item) { item.classList.remove("active"); });
  btn.classList.add("active");
  sessionStorage.setItem("medicalLoginRoleDraft", btn.dataset.role || btn.textContent || "用户");
}

function quickLoginRole(role) {
  sessionStorage.setItem("medicalLoginRoleDraft", role || "用户");
  var user = document.getElementById("loginHeroUser");
  var pass = document.getElementById("loginHeroPass");
  if (user && !user.value) user.value = "user";
  if (pass && !pass.value) pass.value = "123456";
  loginApp("hero");
}

function openLoginModal() {
  var dialog = document.getElementById("loginDialog");
  if (dialog) dialog.classList.add("show");
  var user = document.getElementById("loginDialogUser");
  if (user) setTimeout(function() { user.focus(); }, 50);
}

function closeLoginModal() {
  var dialog = document.getElementById("loginDialog");
  if (dialog) dialog.classList.remove("show");
}

function handleTopAuthClick() {
  if (sessionStorage.getItem("medicalAuth") === "1") {
    navigate("mine");
  } else {
    openLoginModal();
  }
}

function getLoginFields(source) {
  if (source === "hero") {
    return { user: document.getElementById("loginHeroUser"), pass: document.getElementById("loginHeroPass") };
  }
  return { user: document.getElementById("loginDialogUser") || document.getElementById("loginHeroUser"), pass: document.getElementById("loginDialogPass") || document.getElementById("loginHeroPass") };
}

function loginApp(source) {
  var fields = getLoginFields(source);
  var user = (fields.user || {}).value || "";
  var pass = (fields.pass || {}).value || "";
  if (!user.trim() || !pass.trim()) {
    toast("请输入账号和密码");
    return;
  }
  sessionStorage.setItem("medicalAuth", "1");
  sessionStorage.setItem("medicalUser", user.trim());
  sessionStorage.setItem("medicalRole", sessionStorage.getItem("medicalLoginRoleDraft") || "普通用户");
  sessionStorage.setItem("medicalLoginAt", new Date().toLocaleString("zh-CN", { hour12: false }));
  closeLoginModal();
  updateAuthButton();
  toast("登录成功");
  if (source === "dialog") navigate("mine");
}

function logoutApp() {
  sessionStorage.removeItem("medicalAuth");
  sessionStorage.removeItem("medicalUser");
  updateAuthButton();
  toast("已退出登录");
}

function updateAuthButton() {
  var btn = document.getElementById("topLoginBtn");
  if (!btn) return;
  if (sessionStorage.getItem("medicalAuth") === "1") {
    var user = sessionStorage.getItem("medicalUser") || "用户";
    btn.innerHTML = '<span class="top-user-avatar logged">' + esc(user.slice(0, 1).toUpperCase()) + '</span><span class="top-user-name">' + esc(user) + '</span>';
    btn.title = "进入我的";
    btn.classList.add("logged-in");
  } else {
    btn.innerHTML = '<span class="top-user-avatar">未</span><span class="top-user-name">未登录</span>';
    btn.title = "用户登录";
    btn.classList.remove("logged-in");
  }
}

function initAuth() {
  updateAuthButton();
  getStoredAutoLocation();
  ensureAssistantWidget();
  Promise.all([loadDoctorPhotoManifest(), loadHospitalLogoManifest()]).then(function() {
    navigate("dashboard");
  });
}

var DISTRICT_POINTS = [
  { name: "天宁区", lat: 31.7760, lng: 119.9600 },
  { name: "钟楼区", lat: 31.7850, lng: 119.9450 },
  { name: "武进区", lat: 31.7300, lng: 119.9500 },
  { name: "新北区", lat: 31.8200, lng: 119.9700 },
  { name: "金坛区", lat: 31.7200, lng: 119.5800 },
  { name: "溧阳市", lat: 31.4100, lng: 119.4800 }
];
var AUTO_LOCATION_STORAGE_KEY = "medicalAutoLocation";

function nearestDistrict(lat, lng) {
  var best = DISTRICT_POINTS[0];
  var bestDistance = Infinity;
  for (var i = 0; i < DISTRICT_POINTS.length; i++) {
    var p = DISTRICT_POINTS[i];
    var d = haversineKm(lat, lng, p.lat, p.lng);
    if (d < bestDistance) { best = p; bestDistance = d; }
  }
  return { name: best.name, distance: bestDistance };
}

function getStoredAutoLocation() {
  if (window._autoLocation) return window._autoLocation;
  try {
    var saved = JSON.parse(localStorage.getItem(AUTO_LOCATION_STORAGE_KEY) || "null");
    if (saved && isFinite(saved.lat) && isFinite(saved.lng)) {
      window._autoLocation = saved;
      return saved;
    }
  } catch (e) {}
  return null;
}

function formatAutoLocation(loc) {
  loc = loc || getStoredAutoLocation();
  if (!loc) return "未获取定位，按手动区域估算";
  return (loc.district || "已定位") +
    (loc.accuracy ? " · 精度约 " + loc.accuracy + " 米" : "") +
    (loc.updatedAt ? " · " + loc.updatedAt : "");
}

function saveAutoLocation(loc) {
  if (!loc) return;
  var saved = {
    lat: loc.lat,
    lng: loc.lng,
    district: loc.district || "已定位",
    accuracy: loc.accuracy || 0,
    updatedAt: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
  };
  window._autoLocation = saved;
  try { localStorage.setItem(AUTO_LOCATION_STORAGE_KEY, JSON.stringify(saved)); } catch (e) {}
  syncAutoLocationControls(saved, "已自动定位");
  if (window._currentPage === "mine") renderMine();
}

function syncAutoLocationControls(loc, prefix) {
  loc = loc || getStoredAutoLocation();
  if (!loc) return false;
  var select = document.getElementById("recDistrict");
  if (select && loc.district) select.value = loc.district;
  var status = document.getElementById("recLocationStatus");
  if (status) {
    status.textContent = (prefix || "已读取定位") + "，按当前坐标计算距离；最近区域：" + (loc.district || "已定位") + "。" +
      (loc.accuracy ? " 精度约 " + loc.accuracy + " 米。" : "");
  }
  return true;
}

function buildDistrictControl() {
  var opts = "";
  for (var i = 0; i < DISTRICT_POINTS.length; i++) {
    var d = DISTRICT_POINTS[i].name;
    opts += '<option value="' + esc(d) + '">' + esc(d) + '</option>';
  }
  return '<div class="form-group">' +
    '<label class="form-label">所在区域</label>' +
    '<div class="location-control">' +
      '<select class="form-select" id="recDistrict" onchange="clearAutoLocation()">' + opts + '</select>' +
    '</div>' +
    '<div id="recLocationStatus" class="location-status">正在尝试系统自动定位；未授权时按所选区域估算距离。</div>' +
  '</div>';
}

function clearAutoLocation() {
  window._autoLocation = null;
  window._manualLocationMode = true;
  autoLocationRequestSeq++;
  try { localStorage.removeItem(AUTO_LOCATION_STORAGE_KEY); } catch (e) {}
  var status = document.getElementById("recLocationStatus");
  if (status) status.textContent = "已切换为手动区域，按所选区域估算距离。";
  if (window._currentPage === "mine") renderMine();
}

function applyAutoLocationPosition(pos, source, token) {
  if (!pos || !pos.coords || token !== autoLocationRequestSeq || window._manualLocationMode) return;
  var lat = pos.coords.latitude;
  var lng = pos.coords.longitude;
  var near = nearestDistrict(lat, lng);
  var accuracy = Math.round(pos.coords.accuracy || 0);
  saveAutoLocation({ lat: lat, lng: lng, district: near.name, accuracy: accuracy });
  var status = document.getElementById("recLocationStatus");
  if (status) {
    status.textContent = "已自动定位，按当前坐标计算距离；最近区域：" + near.name + "。" +
      (accuracy ? " 精度约 " + accuracy + " 米。" : "") +
      (source === "fast" ? " 正在继续校准..." : "");
  }
}

function autoLocationErrorText(err) {
  if (!err) return "定位失败，请手动选择区域。";
  if (err.code === 1) return "浏览器未授权定位，请允许位置权限，或手动选择区域。";
  if (err.code === 2) return "暂时无法获取位置信息，请检查网络/GPS，或手动选择区域。";
  return "定位响应超时，请手动选择区域；系统仍可按所选区域估算距离。";
}

function requestAutoLocation() {
  var status = document.getElementById("recLocationStatus");
  if (!navigator.geolocation) {
    if (status) status.textContent = "当前浏览器不支持定位，请手动选择区域。";
    toast("当前浏览器不支持定位");
    return;
  }
  window._manualLocationMode = false;
  autoLocationRequestSeq++;
  var token = autoLocationRequestSeq;
  if (status) status.textContent = "正在自动定位：先快速获取位置，再进行高精度校准...";

  navigator.geolocation.getCurrentPosition(function(pos) {
    applyAutoLocationPosition(pos, "fast", token);
    toast("已获取当前位置，正在校准精度");
  }, function(err) {
    if (!window._autoLocation && token === autoLocationRequestSeq) {
      if (status) status.textContent = autoLocationErrorText(err);
    }
  }, { enableHighAccuracy: false, timeout: 4500, maximumAge: 600000 });

  navigator.geolocation.getCurrentPosition(function(pos) {
    applyAutoLocationPosition(pos, "precise", token);
    toast("定位已校准");
  }, function(err) {
    if (!window._autoLocation && token === autoLocationRequestSeq) {
      if (status) status.textContent = autoLocationErrorText(err);
      toast("定位失败，请手动选择区域");
    } else if (status && window._autoLocation) {
      status.textContent = status.textContent.replace(" 正在继续校准...", "");
    }
  }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 });
}

function requestRecommendAutoLocation() {
  if (getStoredAutoLocation()) {
    syncAutoLocationControls(window._autoLocation, "已同步上次定位");
    return;
  }
  window._recommendAutoLocationRequested = true;
  requestAutoLocation();
}

// ========== 优推收藏 ==========
var starredDoctors = {};

function toggleStar(docId, docName) {
  if (starredDoctors[docId]) {
    delete starredDoctors[docId];
    toast("已取消优推：" + docName);
  } else {
    starredDoctors[docId] = docName;
    toast("已添加优推：" + docName);
  }
  updateStarButtons();
  updateRerankToolbar();
}

function updateStarButtons() {
  $$(".star-toggle").forEach(function(btn) {
    var did = parseInt(btn.dataset.doctorId);
    if (starredDoctors[did]) {
      btn.innerHTML = uiIcon("star", "icon-inline") + "已优推";
      btn.classList.add("starred");
    } else {
      btn.innerHTML = uiIcon("star", "icon-inline") + "优推";
      btn.classList.remove("starred");
    }
  });
}

function getStarredIds() {
  return Object.keys(starredDoctors).map(function(k) { return parseInt(k); });
}

function cacheDoctor(d, hospital) {
  if (!d || !d.id) return;
  if (!window._doctorById) window._doctorById = {};
  d._department_group = normalizeDepartmentName(d.department);
  d._photo_url = resolveDoctorPhoto(d);
  if (hospital) {
    d._hospital_name = hospital.name || d._hospital_name || d.hospital_name;
    d._hospital_level = hospital.level || d._hospital_level;
    d._hospital_type = hospital.type || d._hospital_type;
    d._hospital_address = hospital.address || d._hospital_address;
  }
  window._doctorById[d.id] = d;
}

function getDoctorHospitalName(d) {
  return d._hospital_name || d.hospital_name || "未知医院";
}

function normalizeDepartmentName(name) {
  var n = String(name || "").replace(/\s+/g, "");
  if (!n || n === "✅") return "未分科";
  if (n.indexOf("心脏中心") >= 0 || n.indexOf("心胸外科") >= 0 || n.indexOf("心脏大血管") >= 0) return "心脏大血管外科";
  if (n.indexOf("心血管") >= 0 || n.indexOf("心脑血管") >= 0 || n.indexOf("心内科") >= 0) return "心血管内科";
  if (n.indexOf("呼吸") >= 0) return "呼吸与危重症医学科";
  if (n.indexOf("消化") >= 0 || n.indexOf("脾胃") >= 0) return "消化内科";
  if (n.indexOf("肾脏风湿") >= 0) return "肾内科";
  if (n.indexOf("肾内") >= 0 || n.indexOf("肾脏内") >= 0 || n.indexOf("肾病") >= 0) return "肾内科";
  if (n.indexOf("内分泌") >= 0) return "内分泌代谢科";
  if (n.indexOf("骨质疏松") >= 0 || n.indexOf("骨伤") >= 0 || n.indexOf("骨外") >= 0 || n.indexOf("脊柱") >= 0 || n === "骨科") return "骨科";
  if (n.indexOf("耳鼻咽喉") >= 0) return "耳鼻咽喉科";
  if (n.indexOf("肝胆") >= 0 || n.indexOf("普外") >= 0 || n === "普通外科" || n === "外科") return "普通外科";
  if (n.indexOf("肿瘤") >= 0 || n.indexOf("放疗") >= 0 || n.indexOf("血液肿瘤") >= 0 || n.indexOf("妇瘤") >= 0) return "肿瘤科";
  if (n.indexOf("生殖医学") >= 0) return "生殖医学科";
  if (n.indexOf("产前诊断") >= 0) return "产前诊断科";
  if (n.indexOf("妇女保健") >= 0) return "妇女保健科";
  if (n.indexOf("宫颈") >= 0 || n.indexOf("计划生育") >= 0 || n === "妇科" || n === "产科" || n === "妇产科" || n.indexOf("妇科/产科") >= 0) return "妇产科";
  if (n.indexOf("儿童保健") >= 0 || n === "儿保科") return "儿童保健科";
  if (n.indexOf("新生儿") >= 0) return "新生儿科";
  if (n.indexOf("儿外") >= 0) return "儿外科";
  if (n === "儿科") return "儿科";
  if (n.indexOf("心理") >= 0 || n.indexOf("心身") >= 0) return "心理科";
  if (n.indexOf("中医科及特色门诊") >= 0) return "中医科";
  if (n.indexOf("针灸") >= 0 || n.indexOf("推拿") >= 0) return "针灸推拿科";
  if (n.indexOf("肛肠") >= 0 || n.indexOf("疮疡") >= 0) return "肛肠科";
  if (n.indexOf("感染") >= 0) return "感染科";
  return name || "未分科";
}

function openDoctorProfile(docId) {
  var cached = window._doctorById && window._doctorById[docId];
  if (cached) {
    showDoctorProfile(cached);
    return;
  }
  fetch(API + "/doctors/detail/" + docId).then(function(res) { return res.json(); }).then(function(json) {
    if (json.code !== 200) { toast(json.message || "未找到医生信息"); return; }
    var d = json.data.doctor;
    cacheDoctor(d, json.data.hospital);
    showDoctorProfile(d);
  }).catch(function() {
    toast("医生信息加载失败");
  });
}

function showDoctorProfile(d) {
  cacheDoctor(d);
  setAssistantContext("doctor", d);
  var kws = (d.keywords || d.specialties || []).slice(0, 12).map(function(k) {
    return '<span class="float-tag">' + esc(k) + '</span>';
  }).join("");
  var deptGroup = d._department_group || normalizeDepartmentName(d.department);
  var originalDept = d.department && d.department !== deptGroup ? '<div class="profile-original-dept">原始科室：' + esc(d.department) + '</div>' : "";
  var scNote = d.surgery_count_note || (d.surgery_count ? d.surgery_count + "例" : "暂无");
  var papers = d.sci_papers ? "SCI " + d.sci_papers + "篇" : (d.total_papers ? "论文 " + d.total_papers + "篇" : "暂无");
  var achievements = (d.achievements || []).slice(0, 5).map(function(a) {
    return '<li>' + esc(a) + '</li>';
  }).join("");
  var modal = document.getElementById("doctorProfileModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "doctorProfileModal";
    modal.className = "profile-modal";
    modal.onclick = function(e) { if (e.target === modal) closeDoctorProfile(); };
    document.body.appendChild(modal);
  }
  modal.innerHTML =
    '<div class="profile-card" role="dialog" aria-modal="true">' +
      '<button class="profile-close" onclick="closeDoctorProfile()" aria-label="关闭">&times;</button>' +
      '<div class="profile-head">' +
        '<div class="profile-avatar">' + doctorAvatarHtml(d, "profile-photo") + '</div>' +
        '<div>' +
          '<div class="profile-name">' + esc(d.name) + '</div>' +
          '<div class="profile-title">' + esc([d.title, d.academic_title].filter(function(v) { return v; }).join(" · ")) + '</div>' +
          '<div class="profile-hospital">' + esc(getDoctorHospitalName(d)) + ' · ' + esc(deptGroup || "") + '</div>' +
          originalDept +
        '</div>' +
      '</div>' +
      '<div class="profile-grid">' +
        '<div><span>医院层级</span><strong>' + esc(d._hospital_level || "暂无") + '</strong></div>' +
        '<div><span>手术/经验</span><strong>' + esc(scNote) + '</strong></div>' +
        '<div><span>论文成果</span><strong>' + esc(papers) + '</strong></div>' +
        '<div><span>专利/基金</span><strong>' + esc([d.national_funding ? "国自然" : "", d.patents ? "专利" + d.patents + "项" : ""].filter(function(v) { return v; }).join(" · ") || "暂无") + '</strong></div>' +
      '</div>' +
      '<div class="profile-section"><h4>擅长方向</h4><div class="dc-keywords">' + (kws || '<span class="empty-mini">暂无擅长标签</span>') + '</div></div>' +
      (achievements ? '<div class="profile-section"><h4>荣誉/成果</h4><ul class="profile-list">' + achievements + '</ul></div>' : '') +
      '<div class="profile-actions">' +
        '<button class="btn btn-sm star-toggle' + (starredDoctors[d.id] ? ' starred' : '') + '" data-doctor-id="' + d.id + '" onclick="event.stopPropagation();toggleStar(' + d.id + ',\'' + esc(d.name).replace(/'/g, "\\'") + '\')">' + uiIcon("star", "icon-inline") + (starredDoctors[d.id] ? '已优推' : '优推') + '</button>' +
      '</div>' +
    '</div>';
  modal.classList.add("show");
}

function closeDoctorProfile() {
  var modal = document.getElementById("doctorProfileModal");
  if (modal) modal.classList.remove("show");
}

// ========== 常量 ==========
var SCENARIO_LABELS = { surgery: "手术/重症需求", common: "常见病症", complex: "疑难/罕见病", first_visit: "初次就诊" };
var SCENARIO_ICONS = { surgery: "surgery", common: "pill", complex: "lab", first_visit: "hospital" };
var SCENARIO_TIPS = {
  surgery: "手术经验权重最高(40%)，优先推荐手术量大、经验丰富的专家",
  common: "专科匹配与距离可及优先，普通病症避免过度占用顶级专家资源",
  complex: "学术水平权重最高(30%)，优先推荐科研能力强、有国自然的专家",
  first_visit: "亚专业匹配权重最高(30%)，帮您找到最对口的医生"
};
var SCENARIO_CATEGORY_WEIGHTS = {
  surgery: [
    ["手术/重症", 42, "#1e40af"],
    ["疑难/罕见病", 24, "#c559f0"],
    ["常见病症", 18, "#10b981"],
    ["初次就诊", 16, "#3b82f6"]
  ],
  common: [
    ["常见病症", 44, "#10b981"],
    ["初次就诊", 22, "#3b82f6"],
    ["疑难/罕见病", 18, "#c559f0"],
    ["手术/重症", 16, "#1e40af"]
  ],
  complex: [
    ["疑难/罕见病", 40, "#c559f0"],
    ["手术/重症", 25, "#1e40af"],
    ["初次就诊", 20, "#3b82f6"],
    ["常见病症", 15, "#10b981"]
  ],
  first_visit: [
    ["初次就诊", 38, "#3b82f6"],
    ["常见病症", 27, "#10b981"],
    ["疑难/罕见病", 20, "#c559f0"],
    ["手术/重症", 15, "#1e40af"]
  ]
};

// ========== 时钟 ==========
function updateClock() {
  var el = document.getElementById("currentTime");
  if (!el) return;
  var now = new Date();
  el.textContent = now.toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
setInterval(updateClock, 1000);
updateClock();

// ========== 路由 ==========
var pages = {
  dashboard: renderDashboard,
  recommend: renderRecommend,
  hospitals: renderHospitals,
  doctors: renderDoctors,
  map: renderMap,
  mine: renderMine,
  "api-docs": renderApiDocs,
  "hospital-detail": renderHospitalDetailPage
};

function navigate(page, params) {
  window._currentPage = page;
  $$(".nav-item").forEach(function(el) { el.classList.remove("active"); });
  var nav = document.querySelector('[data-page="' + page + '"]');
  if (nav) nav.classList.add("active");
  var pageNames = { dashboard: "首页总览", recommend: "智能推荐", hospitals: "医院列表", doctors: "医生列表", map: "地图视图", mine: "我的", "api-docs": "接口文档", "hospital-detail": "医院详情" };
  setAssistantContext("page", { page: page, title: pageNames[page] || "当前页面" });
  if (page === "hospital-detail" && params) {
    window._hospitalDetailParams = params;
  }
  var render = pages[page];
  if (render) render(params);
}

$$(".nav-item").forEach(function(item) {
  item.addEventListener("click", function() { navigate(item.dataset.page); });
});

var vizReplayObserver = null;
var vizReplayMutationObserver = null;
var vizReplayDebounce = null;
var vizReplayScrollBound = false;
var VIZ_REPLAY_SELECTOR = [
  ".column-fill",
  ".mini-bar-row i",
  ".horizontal-row i",
  ".probability-row i",
  ".scenario-weight-track i",
  ".score-bar-fill",
  ".dc-score-fill"
].join(",");
var VIZ_REPLAY_GROUP_SELECTOR = [
  ".column-chart",
  ".mini-bar-chart",
  ".horizontal-chart",
  ".probability-list",
  ".scenario-weight-card",
  ".score-bar",
  ".dc-score-bar"
].join(",");

function replayVizAnimation(el) {
  if (!el) return;
  var isColumn = el.classList.contains("column-fill");
  var prop = isColumn ? "height" : "width";
  var targetKey = isColumn ? "vizTargetHeight" : "vizTargetWidth";
  var target = el.dataset[targetKey] || el.style[prop] || window.getComputedStyle(el)[prop];
  if (!target || target === "0px" || target === "0%") return;
  el.dataset[targetKey] = target;
  el.style.animation = "none";
  el.style.transition = "none";
  el.style[prop] = "0";
  void el.offsetWidth;
  requestAnimationFrame(function() {
    el.style.transition = prop + " 0.86s cubic-bezier(0.22, 1, 0.36, 1)";
    el.style[prop] = target;
  });
  setTimeout(function() {
    el.style.transition = "";
    el.style.animation = "";
  }, 920);
}

function isVizElementFullyVisible(el) {
  if (!el) return false;
  var r = el.getBoundingClientRect();
  var vw = window.innerWidth || document.documentElement.clientWidth;
  var vh = window.innerHeight || document.documentElement.clientHeight;
  var inViewport = r.top >= 8 && r.bottom <= vh - 8 && r.right > 0 && r.left < vw;
  var main = document.getElementById("mainContent");
  if (!main) return inViewport;
  var rr = main.getBoundingClientRect();
  var inMain = r.top >= rr.top + 8 && r.bottom <= rr.bottom - 8 && r.right > rr.left && r.left < rr.right;
  return inViewport && inMain;
}

function replayVisibleVizOnScroll() {
  var main = document.getElementById("mainContent");
  if (!main) return;
  var groups = Array.prototype.slice.call(main.querySelectorAll(VIZ_REPLAY_GROUP_SELECTOR));
  groups.forEach(function(group) {
    var visible = isVizElementFullyVisible(group);
    if (!visible) {
      group.dataset.vizVisible = "0";
      return;
    }
    if (group.dataset.vizVisible === "1") return;
    group.dataset.vizVisible = "1";
    Array.prototype.slice.call(group.querySelectorAll(VIZ_REPLAY_SELECTOR)).forEach(replayVizAnimation);
  });
}

function ensureVizReplayScroll() {
  var main = document.getElementById("mainContent");
  if (!main || vizReplayScrollBound) return;
  vizReplayScrollBound = true;
  var scrollTimer = null;
  function onScrollEnd() {
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(replayVisibleVizOnScroll, 140);
  }
  main.addEventListener("scroll", onScrollEnd, { passive: true });
  window.addEventListener("scroll", onScrollEnd, { passive: true });
  window.addEventListener("wheel", onScrollEnd, { passive: true });
  window.addEventListener("touchmove", onScrollEnd, { passive: true });
}

function ensureVizReplayWatcher() {
  var main = document.getElementById("mainContent");
  if (!main || vizReplayMutationObserver) return;
  vizReplayMutationObserver = new MutationObserver(function() {
    if (vizReplayDebounce) clearTimeout(vizReplayDebounce);
    vizReplayDebounce = setTimeout(function() {
      initScrollVizReplay(main);
    }, 80);
  });
  vizReplayMutationObserver.observe(main, { childList: true, subtree: true });
}

function initScrollVizReplay(root) {
  return;
}

function countBy(list, getter) {
  var counts = {};
  (list || []).forEach(function(item) {
    var key = getter(item) || "未知";
    counts[key] = (counts[key] || 0) + 1;
  });
  return counts;
}

function buildDashboardBars(counts) {
  var total = Object.keys(counts).reduce(function(sum, key) { return sum + counts[key]; }, 0) || 1;
  return Object.keys(counts).sort(function(a, b) { return counts[b] - counts[a]; }).map(function(key) {
    var pct = Math.round(counts[key] / total * 100);
    return '<div class="viz-bar-row">' +
      '<div class="viz-bar-label"><span>' + esc(key) + '</span><strong>' + counts[key] + '</strong></div>' +
      '<div class="viz-bar-track"><div class="viz-bar-fill" style="width:' + pct + '%;"></div></div>' +
    '</div>';
  }).join("");
}

var CHART_COLORS = ["#1e40af", "#3b82f6", "#10b981", "#c559f0", "#f59e0b", "#ef4444"];
var DISTRICT_NAMES = ["天宁区", "钟楼区", "武进区", "金坛区", "溧阳市", "新北区"];

function getHospitalDistrict(h) {
  var text = [h.name, h.address].join(" ");
  if (text.indexOf("武进") >= 0) return "武进区";
  if (text.indexOf("金坛") >= 0) return "金坛区";
  if (text.indexOf("溧阳") >= 0) return "溧阳市";
  if (text.indexOf("新北") >= 0 || text.indexOf("三井") >= 0) return "新北区";
  if (text.indexOf("钟楼") >= 0) return "钟楼区";
  return "天宁区";
}

function countByValue(list, key) {
  var counts = {};
  (list || []).forEach(function(item) {
    var value = typeof key === "function" ? key(item) : item[key];
    value = value || "未知";
    counts[value] = (counts[value] || 0) + 1;
  });
  return counts;
}

function sumByGroup(list, groupGetter, valueGetter) {
  var counts = {};
  (list || []).forEach(function(item) {
    var group = groupGetter(item) || "未知";
    var value = Number(valueGetter(item) || 0);
    counts[group] = (counts[group] || 0) + value;
  });
  return counts;
}

function buildInlineBarChart(counts, unit) {
  var keys = Object.keys(counts);
  var max = keys.reduce(function(m, key) { return Math.max(m, Number(counts[key]) || 0); }, 1);
  return '<div class="mini-bar-chart">' + keys.map(function(key, i) {
    var value = Number(counts[key]) || 0;
    var pct = Math.max(4, Math.round(value / max * 100));
    return '<div class="mini-bar-row">' +
      '<span>' + esc(key) + '</span>' +
      '<div><i style="width:' + pct + '%;background:' + CHART_COLORS[i % CHART_COLORS.length] + ';"></i></div>' +
      '<b>' + value + (unit || "") + '</b>' +
    '</div>';
  }).join("") + '</div>';
}

function buildColumnChart(counts) {
  var keys = Object.keys(counts).sort(function(a, b) { return counts[b] - counts[a]; }).slice(0, 12);
  var max = keys.reduce(function(m, key) { return Math.max(m, counts[key]); }, 1);
  return '<div class="column-chart column-chart-fluid">' + keys.map(function(key, i) {
    var height = Math.max(12, Math.round(counts[key] / max * 100));
    var color = CHART_COLORS[i % CHART_COLORS.length];
    return '<div class="column-item">' +
      '<div class="column-value">' + counts[key] + '</div>' +
      '<div class="column-track"><div class="column-fill" style="height:' + height + '%;background:' + color + ';"></div></div>' +
      '<div class="column-label">' + esc(key) + '</div>' +
    '</div>';
  }).join("") + '</div>';
}

function buildPieChart(counts) {
  var keys = Object.keys(counts).sort(function(a, b) { return counts[b] - counts[a]; });
  var total = keys.reduce(function(sum, key) { return sum + counts[key]; }, 0) || 1;
  var cursor = 0;
  var stops = [];
  var labels = [];
  keys.forEach(function(key, i) {
    var pct = counts[key] / total * 100;
    var start = cursor;
    var end = cursor + pct;
    var color = CHART_COLORS[i % CHART_COLORS.length];
    stops.push(color + " " + start.toFixed(2) + "% " + end.toFixed(2) + "%");
    var angle = (start + pct / 2) / 100 * Math.PI * 2 - Math.PI / 2;
    var x = 50 + Math.cos(angle) * 46;
    var y = 50 + Math.sin(angle) * 46;
    labels.push('<span class="pie-around-label" style="left:' + x.toFixed(1) + '%;top:' + y.toFixed(1) + '%;--label-color:' + color + ';">' +
      '<b>' + esc(key) + '</b><em>' + pct.toFixed(1) + '%</em></span>');
    cursor = end;
  });
  return '<div class="pie-chart-wrap">' +
    '<div class="pie-chart-orbit"><div class="pie-chart" style="background:conic-gradient(' + stops.join(",") + ');"><div><strong>' + total + '</strong><span>总计</span></div></div>' + labels.join("") + '</div>' +
  '</div>';
}

function buildResourceRadar(stats, hospitals) {
  var topLevelCount = hospitals.filter(function(h) { return h.level === "三级甲等"; }).length;
  var specialistCount = hospitals.filter(function(h) { return h.type === "专科医院"; }).length;
  var districtCount = Object.keys(countByValue(hospitals, getHospitalDistrict)).length;
  var values = {
    "医院覆盖": Math.min(100, (hospitals.length / 21) * 100),
    "医生资源": Math.min(100, ((stats.total_real_doctors || stats.total_doctors) / 1892) * 100),
    "床位供给": Math.min(100, (stats.total_beds / 19300) * 100),
    "门诊承载": Math.min(100, (stats.daily_outpatients_total / 66600) * 100),
    "急诊能力": Math.round(((hospitals.filter(function(h) { return h.emergency; }).length || 1) / hospitals.length) * 100),
    "三甲占比": Math.round(topLevelCount / hospitals.length * 100),
    "专科覆盖": Math.round(specialistCount / hospitals.length * 100),
    "区域覆盖": Math.round(districtCount / DISTRICT_NAMES.length * 100)
  };
  var labels = Object.keys(values);
  var points = labels.map(function(_, i) {
    var angle = Math.PI * 2 * i / labels.length - Math.PI / 2;
    return [50 + Math.cos(angle) * 43, 50 + Math.sin(angle) * 43];
  });
  var poly = labels.map(function(label, i) {
    var ratio = values[label] / 100;
    var p = points[i];
    return (50 + (p[0] - 50) * ratio).toFixed(1) + "," + (50 + (p[1] - 50) * ratio).toFixed(1);
  }).join(" ");
  return '<div class="dashboard-radar"><svg viewBox="0 0 100 100">' +
    [0.25, 0.5, 0.75, 1].map(function(r) {
      return '<polygon class="radar-grid radar-grid-' + Math.round(r * 100) + '" points="' + points.map(function(p) {
        return (50 + (p[0] - 50) * r).toFixed(1) + "," + (50 + (p[1] - 50) * r).toFixed(1);
      }).join(" ") + '"></polygon>';
    }).join("") +
    points.map(function(p) { return '<line class="radar-axis" x1="50" y1="50" x2="' + p[0].toFixed(1) + '" y2="' + p[1].toFixed(1) + '"></line>'; }).join("") +
    '<polygon class="radar-fill" points="' + poly + '"></polygon>' +
    labels.map(function(label, i) {
      var p = points[i];
      var x = 50 + (p[0] - 50) * 1.14;
      var y = 50 + (p[1] - 50) * 1.14;
      return '<text class="radar-label" x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '">' + esc(label) + '</text>';
    }).join("") +
    '<text class="radar-center" x="50" y="49">资源</text><text class="radar-center-sub" x="50" y="57">能力</text>' +
  '</svg><div>' + labels.map(function(label, i) {
    return '<span><i style="background:' + CHART_COLORS[i % CHART_COLORS.length] + ';"></i><b>' + esc(label) + '</b><em>' + Math.round(values[label]) + '%</em></span>';
  }).join("") + '</div></div>';
}

function buildHorizontalBarChart(counts, unit) {
  var keys = Object.keys(counts).sort(function(a, b) { return counts[b] - counts[a]; }).slice(0, 12);
  var max = keys.reduce(function(m, key) { return Math.max(m, counts[key]); }, 1);
  return '<div class="horizontal-chart">' + keys.map(function(key, i) {
    var value = counts[key];
    var pct = value > 0 ? Math.max(5, Math.round(value / max * 100)) : 0;
    return '<div class="horizontal-row">' +
      '<span>' + esc(key) + '</span>' +
      '<div><i style="width:' + pct + '%;background:' + CHART_COLORS[i % CHART_COLORS.length] + ';"></i></div>' +
      '<b>' + value + (unit || "") + '</b>' +
    '</div>';
  }).join("") + '</div>';
}

function buildScenarioDonut() {
  var counts = { "重症优先": 40, "常见病": 30, "疑难病": 20, "初诊匹配": 10 };
  return buildPieChart(counts);
}

function symptomScores(condition) {
  var text = condition || "";
  var map = {
    "发热": ["发热", "高烧", "低烧", "发烧"],
    "疼痛": ["痛", "疼", "胸痛", "腹痛", "头痛", "腰痛"],
    "消化": ["胃", "腹", "反酸", "腹泻", "恶心", "呕吐"],
    "呼吸": ["咳", "喘", "胸闷", "呼吸", "肺", "气短"],
    "神经": ["头晕", "麻木", "抽搐", "意识", "偏瘫", "癫痫"]
  };
  var scores = {};
  if (!text.trim()) {
    Object.keys(map).forEach(function(key) { scores[key] = 0; });
    return scores;
  }
  Object.keys(map).forEach(function(key) {
    var hits = map[key].reduce(function(sum, token) { return sum + (text.indexOf(token) >= 0 ? 1 : 0); }, 0);
    scores[key] = Math.min(100, 18 + hits * 28);
  });
  return scores;
}

function buildRadarVisual(condition) {
  var scores = symptomScores(condition);
  var points = [
    [50, 8, scores["发热"]], [88, 35, scores["疼痛"]], [74, 84, scores["消化"]],
    [26, 84, scores["呼吸"]], [12, 35, scores["神经"]]
  ];
  var poly = points.map(function(p) {
    var cx = 50, cy = 50;
    var ratio = p[2] / 100;
    return (cx + (p[0] - cx) * ratio).toFixed(1) + "," + (cy + (p[1] - cy) * ratio).toFixed(1);
  }).join(" ");
  var labels = ["发热", "疼痛", "消化", "呼吸", "神经"];
  return '<div class="symptom-visual-card">' +
    '<div class="radar-wrap"><svg viewBox="0 0 100 100" aria-label="病情雷达图">' +
      '<polygon points="50,8 88,35 74,84 26,84 12,35" class="radar-grid"></polygon>' +
      '<polygon points="' + poly + '" class="radar-fill"></polygon>' +
      points.map(function(p, i) { return '<text x="' + p[0] + '" y="' + p[1] + '">' + labels[i] + '</text>'; }).join("") +
    '</svg></div>' +
    '<div class="probability-list">' + Object.keys(scores).sort(function(a, b) { return scores[b] - scores[a]; }).map(function(k) {
      var v = scores[k];
      var cls = v >= 70 ? "high" : (v >= 45 ? "mid" : "low");
      return '<div class="probability-row ' + cls + '"><span>' + esc(k) + '相关</span><div><i style="width:' + v + '%;"></i></div><b>' + v + '%</b></div>';
    }).join("") + '</div>' +
  '</div>';
}

function buildDashboardCarousel(stats) {
  var photos = Object.keys(window._doctorPhotoMap || {}).map(function(k) { return window._doctorPhotoMap[k]; }).slice(0, 6);
  var photoHtml = photos.map(function(src, i) {
    return '<img src="' + esc(src) + '" alt="医生照片' + (i + 1) + '">';
  }).join("");
  return '<section class="dashboard-carousel">' +
    '<div class="carousel-track">' +
      '<article class="carousel-slide slide-active contest-combo-slide">' +
        '<div class="contest-combo-visual single-contest-visual" aria-label="常州大学与2026常州城市可信数据空间创新应用大赛">' +
          '<img src="/static/images/carousel/contest_university_combo.jpg" alt="常州大学与2026常州城市可信数据空间创新应用大赛">' +
        '</div>' +
      '</article>' +
      '<article class="carousel-slide">' +
        '<div class="carousel-copy"><span>智能推荐</span><h2>把病情、科室、医生和距离放在一张图里</h2><p>红旗症状识别、医院层级加权、医生画像排序，减少人工判断反复横跳。</p><button class="btn btn-primary" onclick="navigate(\'recommend\')">开始推荐</button></div>' +
        '<div class="carousel-visual photo-mosaic">' + photoHtml + '</div>' +
      '</article>' +
      '<article class="carousel-slide">' +
        '<div class="carousel-copy"><span>资源覆盖</span><h2>' + stats.total_hospitals + ' 家医院与 ' + (stats.total_real_doctors || stats.total_doctors) + ' 位医生</h2><p>医院等级、专科实力、门诊规模和医生履历统一汇总，适合前台快速筛选。</p><button class="btn btn-outline" onclick="navigate(\'hospitals\')">查看医院</button></div>' +
        '<div class="carousel-visual carousel-metrics"><div><strong>' + (stats.total_beds / 1000).toFixed(1) + 'k</strong><span>床位</span></div><div><strong>' + (stats.daily_outpatients_total / 10000).toFixed(1) + '万</strong><span>日均门诊</span></div><div><strong>4</strong><span>推荐场景</span></div></div>' +
      '</article>' +
      '<article class="carousel-slide">' +
        '<div class="carousel-copy"><span>辅助分诊</span><h2>大病小病先分层，再推荐医生</h2><p>疑似急症优先看急诊能力和医院层级；普通病优先距离、可及性和门诊资源。</p><button class="btn btn-primary" onclick="navigate(\'doctors\')">查看医生</button></div>' +
        '<div class="carousel-visual triage-stack"><div>疑似急症</div><div>较重病情</div><div>小病/常见病</div><div>信息不足</div></div>' +
      '</article>' +
    '</div>' +
    '<div class="carousel-dots" aria-label="轮播分页">' +
      '<button type="button" class="active" onclick="setDashboardCarouselSlide(0)" aria-label="切换到常州大学"></button>' +
      '<button type="button" onclick="setDashboardCarouselSlide(1)" aria-label="切换到智能推荐"></button>' +
      '<button type="button" onclick="setDashboardCarouselSlide(2)" aria-label="切换到资源覆盖"></button>' +
      '<button type="button" onclick="setDashboardCarouselSlide(3)" aria-label="切换到辅助分诊"></button>' +
    '</div>' +
  '</section>';
}

var dashboardCarouselIndex = 0;

function setDashboardCarouselSlide(index) {
  var carousel = document.querySelector(".dashboard-carousel");
  if (!carousel) return;
  var slides = carousel.querySelectorAll(".carousel-slide");
  var dots = carousel.querySelectorAll(".carousel-dots button");
  if (!slides.length) return;
  var activeIndex = Math.max(0, Math.min(index || 0, slides.length - 1));
  dashboardCarouselIndex = activeIndex;
  carousel.classList.add("carousel-manual");
  slides.forEach(function(slide, i) {
    slide.classList.toggle("slide-active", i === activeIndex);
  });
  dots.forEach(function(dot, i) {
    dot.classList.toggle("active", i === activeIndex);
  });
}

function moveDashboardCarousel(delta) {
  var carousel = document.querySelector(".dashboard-carousel");
  if (!carousel) return;
  var count = carousel.querySelectorAll(".carousel-slide").length;
  if (!count) return;
  setDashboardCarouselSlide((dashboardCarouselIndex + delta + count) % count);
}

function initDashboardCarousel() {
  var carousel = document.querySelector(".dashboard-carousel");
  if (!carousel) return;
  var startX = 0;
  var startY = 0;
  var isPointerDown = false;
  dashboardCarouselIndex = 0;
  setDashboardCarouselSlide(0);

  carousel.addEventListener("pointerdown", function(e) {
    isPointerDown = true;
    startX = e.clientX;
    startY = e.clientY;
  });
  carousel.addEventListener("pointerup", function(e) {
    if (!isPointerDown) return;
    isPointerDown = false;
    var dx = e.clientX - startX;
    var dy = e.clientY - startY;
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy) * 1.2) {
      moveDashboardCarousel(dx < 0 ? 1 : -1);
    }
  });
  carousel.addEventListener("pointercancel", function() {
    isPointerDown = false;
  });
}

function buildAlgorithmFlow() {
  var steps = [
    ["输入", "疾病/症状"],
    ["分诊", "红旗风险"],
    ["匹配", "科室路径"],
    ["召回", "医生医院"],
    ["精排", "多指标排序"],
    ["解释", "推荐理由"]
  ];
  return '<div class="algorithm-flowline">' + steps.map(function(step, i) {
    return '<div class="flow-node"><span>' + (i + 1) + '</span><strong>' + step[0] + '</strong><em>' + step[1] + '</em></div>';
  }).join('<i></i>') + '</div>';
}

function buildDashboardCommandCenter(stats, hospitals, doctors) {
  var deptCount = Object.keys(buildDepartmentCounts(hospitals)).length;
  var specialistCount = (hospitals || []).filter(function(h) { return h.type === "专科医院"; }).length;
  var emergencyCount = (hospitals || []).filter(function(h) { return h.emergency; }).length;
  var metricHtml = [
    [stats.total_hospitals || hospitals.length, "公办医院", "覆盖常州主要区域"],
    [deptCount, "覆盖科室", "按疾病自动匹配"],
    [(stats.total_real_doctors || stats.total_doctors || doctors.length), "推荐医生", "公开资料整理"],
    [emergencyCount, "急诊能力", "红旗症状兜底"]
  ].map(function(m) {
    return '<div class="resource-metric"><strong>' + esc(m[0]) + '</strong><span>' + esc(m[1]) + '</span><em>' + esc(m[2]) + '</em></div>';
  }).join("");
  var diseaseChips = [
    ["肺结节想找常州公办医院医生", "complex"],
    ["反复咳嗽三个月", "common"],
    ["儿童高热咳嗽", "first_visit"],
    ["牙痛牙龈肿胀", "common"],
    ["腰痛半年怀疑腰椎间盘突出", "first_visit"],
    ["糖尿病复诊配药", "common"]
  ].map(function(item) {
    var encoded = encodeURIComponent(item[0]);
    return '<button onclick="dashboardQuickRecommend(decodeURIComponent(\'' + encoded + '\'), \'' + item[1] + '\')">' + esc(item[0]) + '</button>';
  }).join("");
  return '<section class="care-command">' +
    '<div class="care-intake">' +
      '<span class="care-eyebrow">SafeCare 常州公办医疗资源智能推荐平台</span>' +
      '<h2>一问生成就医路径，一图解释推荐原因</h2>' +
      '<p>基于疾病、位置、科室能力、医生专长和红旗症状规则，辅助选择更合适的常州公办就医路径。</p>' +
      '<div class="care-search">' +
        '<input id="dashboardQuickCondition" placeholder="请输入疾病、症状或就医需求，例如：肺结节想找常州公办医院医生">' +
        '<button class="btn btn-primary" onclick="dashboardQuickRecommend()">开始智能推荐</button>' +
      '</div>' +
      '<div class="care-quick">' + diseaseChips + '</div>' +
      '<div class="care-alert"><strong>急症提示</strong><span>胸痛、呼吸困难、意识障碍、大出血、疑似卒中等情况，请立即拨打120或前往就近急诊。本平台仅提供就医资源推荐与分诊辅助。</span></div>' +
    '</div>' +
    '<div class="resource-cockpit">' +
      '<div class="cockpit-head"><span>常州医疗资源数据面板</span><b>' + specialistCount + ' 家专科资源</b></div>' +
      '<div class="resource-metric-grid">' + metricHtml + '</div>' +
      '<div class="confidence-strip"><div><strong>推荐可信度</strong><span>规则分诊 + 多目标排序 + 推荐解释</span></div><b>87%</b></div>' +
      buildAlgorithmFlow() +
    '</div>' +
  '</section>';
}

function dashboardQuickRecommend(condition, scenario) {
  var input = $("#dashboardQuickCondition");
  var value = (condition || (input ? input.value : "") || "").trim();
  if (!value) {
    toast("请先输入疾病、症状或就医需求");
    if (input) input.focus();
    return;
  }
  window._recommendPrefill = { condition: value, scenario: scenario || "first_visit" };
  navigate("recommend");
}

function buildDoctorTypeCounts(doctors) {
  return countByValue(doctors || [], function(d) {
    var title = d.title || "";
    if (title.indexOf("主任") >= 0 && title.indexOf("副") < 0) return "主任医师";
    if (title.indexOf("副主任") >= 0) return "副主任医师";
    if (title.indexOf("主治") >= 0) return "主治医师";
    return "其他";
  });
}

function buildDepartmentCounts(hospitals) {
  var counts = {};
  (hospitals || []).forEach(function(h) {
    (h.departments || []).forEach(function(dept) {
      counts[dept] = (counts[dept] || 0) + 1;
    });
  });
  return counts;
}

function buildDashboardVisuals(stats, hospitals) {
  var levelCounts = countBy(hospitals, function(h) { return h.level; });
  var typeCounts = countBy(hospitals, function(h) { return h.type; });
  var deptCounts = buildDepartmentCounts(hospitals);
  return '<div class="dashboard-viz-grid">' +
    '<div class="card viz-card"><div class="card-header"><span class="card-title">医院等级柱状图</span></div>' + buildColumnChart(levelCounts) + '</div>' +
    '<div class="card viz-card"><div class="card-header"><span class="card-title">医院类型饼状图</span></div>' + buildPieChart(typeCounts) + '</div>' +
    '<div class="card viz-card"><div class="card-header"><span class="card-title">资源能力雷达图</span></div>' + buildResourceRadar(stats, hospitals) + '</div>' +
    '<div class="card viz-card"><div class="card-header"><span class="card-title">推荐场景权重环图</span></div>' + buildScenarioDonut() + '</div>' +
    '<div class="card viz-card viz-card-wide"><div class="card-header"><span class="card-title">热门科室动态柱状图</span><span style="font-size:12px;color:var(--text-secondary);">按接入医院覆盖数排序</span></div>' + buildColumnChart(deptCounts) + '</div>' +
  '</div>';
}

function buildTransitFusionPanel(transit) {
  transit = transit || {};
  var companyBus = transit.company_bus_counts || {};
  var ticketCounts = transit.ticket_counts || {};
  var route = transit.max_bus_route || {};
  var stationSummary = transit.station_summary || {};
  var taxiSummary = transit.taxi_summary || {};
  var bikeSummary = transit.bike_summary || {};
  var bikeVehicleSummary = transit.bike_vehicle_summary || {};
  var accessList = transit.hospital_station_access || [];
  var taxiAccessList = transit.hospital_taxi_access || [];
  var bikeAccessList = transit.hospital_bike_access || [];
  var bikeVehicleList = transit.hospital_bike_vehicle_distribution || [];
  var accessCounts = { "2公里内有站点": 0, "3公里内有站点": 0, "需换乘/接驳": 0 };
  var taxiHospitalCounts = {};
  var bikeHospitalSupply = {};
  var bikeVehicleCounts = {};
  var nearestTotal = 0;
  var nearestCount = 0;
  for (var i = 0; i < accessList.length; i++) {
    var item = accessList[i];
    if (item.nearby_station_count_2km > 0) accessCounts["2公里内有站点"]++;
    else if (item.nearby_station_count_3km > 0) accessCounts["3公里内有站点"]++;
    else accessCounts["需换乘/接驳"]++;
    if (typeof item.nearest_station_distance_km === "number") {
      nearestTotal += item.nearest_station_distance_km;
      nearestCount++;
    }
  }
  for (var j = 0; j < Math.min(taxiAccessList.length, 6); j++) {
    var taxiItem = taxiAccessList[j];
    var count = taxiItem.nearby_taxi_destination_count_3km || taxiItem.nearby_taxi_destination_count_5km || 0;
    if (count > 0) taxiHospitalCounts[shortHospitalName(taxiItem.hospital_name)] = count;
  }
  for (var k = 0; k < Math.min(bikeAccessList.length, 6); k++) {
    var bikeItem = bikeAccessList[k];
    var supply = bikeItem.bike_supply_2km || 0;
    if (supply > 0) bikeHospitalSupply[shortHospitalName(bikeItem.hospital_name)] = supply;
  }
  for (var m = 0; m < Math.min(bikeVehicleList.length, 6); m++) {
    var vehicleItem = bikeVehicleList[m];
    var vehicles = vehicleItem.normal_vehicle_count_2km || 0;
    if (vehicles > 0) bikeVehicleCounts[shortHospitalName(vehicleItem.hospital_name)] = vehicles;
  }
  var avgNearest = nearestCount ? (nearestTotal / nearestCount).toFixed(1) : "--";
  var transitMetrics = [
    ["公交线路", transit.total_routes || 0, "常武地区"],
    ["公交站点", stationSummary.total_stations || 0, "脱敏经纬度"],
    ["分配车辆", transit.total_bus_count || 0, "线路供给"],
    ["站台形式", Object.keys(stationSummary.platform_shape_counts || {}).length, "路缘/港湾/场站"],
    ["平均票价", (transit.avg_ticket || 0) + "元", "出行成本"],
    ["最近站均距", avgNearest + "km", "医院样本"],
    ["打车订单", taxiSummary.total_orders || 0, "脱敏样本"],
    ["平均打车费", (taxiSummary.avg_fact_price || 0) + "元", "就医成本"],
    ["平均里程", (taxiSummary.avg_drive_mile || 0) + "km", "载客距离"],
    ["骑行站点", bikeSummary.total_stations || 0, "绿色出行"],
    ["可租车辆", bikeSummary.total_bike_num || 0, "展示数据"],
    ["锁车桩", bikeSummary.total_lock_num || 0, "停放供给"],
    ["助力车辆", bikeSummary.total_e_bike_num || 0, "接驳展示"],
    ["车辆样本", bikeVehicleSummary.total_vehicles || 0, "实时分布"],
    ["正常车辆", bikeVehicleSummary.normal_vehicle_count || 0, "状态展示"],
    ["正常率", (bikeVehicleSummary.normal_vehicle_rate || 0) + "%", "运维状态"]
  ].map(function(metric) {
    return '<div><span>' + metric[0] + '</span><strong>' + metric[1] + '</strong><em>' + metric[2] + '</em></div>';
  }).join("");
  return '<div class="card transit-fusion-card">' +
    '<div class="card-header">' +
      '<span class="card-title">公共交通融合数据</span>' +
      '<span class="tag tag-green">政府脱敏数据</span>' +
    '</div>' +
    '<div class="transit-kpi-grid">' + transitMetrics + '</div>' +
    '<div class="transit-fusion-layout">' +
      '<div class="transit-chart-block">' +
        '<div class="transit-chart-title">分公司车辆供给</div>' +
        buildHorizontalBarChart(companyBus, "辆") +
      '</div>' +
      '<div class="transit-chart-block">' +
        '<div class="transit-chart-title">出租车到院样本</div>' +
        buildHorizontalBarChart(taxiHospitalCounts, "单") +
      '</div>' +
      '<div class="transit-chart-block">' +
        '<div class="transit-chart-title">绿色出行站点供给</div>' +
        buildHorizontalBarChart(bikeHospitalSupply, "辆") +
      '</div>' +
      '<div class="transit-chart-block">' +
        '<div class="transit-chart-title">共享车辆展示分布</div>' +
        buildHorizontalBarChart(bikeVehicleCounts, "辆") +
      '</div>' +
      '<div class="transit-chart-block">' +
        '<div class="transit-chart-title">医院周边站点覆盖</div>' +
        buildPieChart(accessCounts) +
      '</div>' +
    '</div>' +
    '<div class="transit-note">' +
      '<strong>融合用途：</strong>公交线路、站点和出租车样本用于解释到院公共交通与即时出行可达性；共享骑行只作为绿色出行推广和站点分布展示，不参与病情、医院或医生推荐排序。' +
      (route.route_name ? '<span>车辆供给最高线路：' + esc(route.route_name) + '，分配车辆 ' + (route.bus_count || 0) + ' 台。</span>' : '') +
      (taxiSummary.total_orders ? '<span>出租车运营样本：' + taxiSummary.total_orders + ' 单，平均实收 ' + (taxiSummary.avg_fact_price || 0) + ' 元，平均里程 ' + (taxiSummary.avg_drive_mile || 0) + ' km。</span>' : '') +
      (bikeSummary.total_stations ? '<span>共享骑行展示：' + bikeSummary.total_stations + ' 个站点，' + (bikeSummary.total_bike_num || 0) + ' 辆可租车辆，' + (bikeSummary.total_lock_num || 0) + ' 个锁车桩。</span>' : '') +
      (bikeVehicleSummary.total_vehicles ? '<span>车辆状态样本：' + bikeVehicleSummary.total_vehicles + ' 辆，正常车辆 ' + (bikeVehicleSummary.normal_vehicle_count || 0) + ' 辆，仅用于地图分布和运维展示。</span>' : '') +
    '</div>' +
  '</div>';
}

function hospitalIconType(hospital) {
  var type = hospital.type || "";
  if (type.indexOf("中医") >= 0) return "tcm";
  if (type.indexOf("专科") >= 0) return "special";
  return "general";
}

function shortHospitalName(name) {
  return String(name || "").replace(/^常州市?/, "").replace(/医院$/, "") || "医院";
}

function hospitalIconInitial(name) {
  var clean = shortHospitalName(name)
    .replace(/^第([一二三四五六七八九十]+)/, "$1")
    .replace(/人民|医疗集团|集团|中心|附属|院区/g, "")
    .trim();
  return (Array.from(clean)[0] || "医").toUpperCase();
}

function buildHospitalMiniIcons(hospitals) {
  var list = hospitals || [];
  var pages = [];
  for (var i = 0; i < list.length; i += 6) {
    var items = list.slice(i, i + 6).map(function(h) {
      var cls = hospitalIconType(h);
      return '<button class="hospital-mini-icon ' + cls + '" onclick="event.stopPropagation();openHospitalProfile(' + h.id + ')" title="' + esc(h.name) + '">' +
        hospitalLogoHtml(h, "mini-logo") +
        '<span class="hospital-logo-initial">' + esc(hospitalIconInitial(h.name)) + '</span>' +
      '</button>';
    }).join("");
    pages.push('<div class="hospital-mini-page">' + items + '</div>');
  }
  return '<div class="hospital-mini-scroll" aria-label="接入医院图标列表"><div class="hospital-mini-icon-grid">' + pages.join("") + '</div></div>' +
    '<div class="hospital-scroll-hint">左右滑动查看更多医院</div>';
}

function openHospitalProfile(hid) {
  var cached = null;
  var list = window._dashboardHospitals || window._hospitals || [];
  for (var i = 0; i < list.length; i++) {
    if (String(list[i].id) === String(hid)) cached = list[i];
  }
  if (cached && cached.departments && cached.strengths) {
    showHospitalProfile(cached);
    return;
  }
  fetch(API + "/hospitals/" + hid).then(function(res) { return res.json(); }).then(function(json) {
    if (json.code !== 200) { toast(json.message || "未找到医院信息"); return; }
    showHospitalProfile(json.data.hospital || json.data);
  }).catch(function() {
    toast("医院信息加载失败");
  });
}

function showHospitalProfile(h) {
  cacheHospital(h);
  setAssistantContext("hospital", h);
  var modal = document.getElementById("hospitalProfileModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "hospitalProfileModal";
    modal.className = "profile-modal hospital-profile-modal";
    modal.onclick = function(e) { if (e.target === modal) closeHospitalProfile(); };
    document.body.appendChild(modal);
  }
  var strengths = (h.strengths || []).slice(0, 8).map(function(s) {
    var score = (h.strength_scores || {})[s];
    return '<span class="float-tag">' + esc(s) + (score ? ' · ' + score : '') + '</span>';
  }).join("");
  var departments = (h.departments || []).slice(0, 16).map(function(d) {
    return '<span class="float-tag muted">' + esc(d) + '</span>';
  }).join("");
  modal.innerHTML =
    '<div class="profile-card hospital-profile-card" role="dialog" aria-modal="true">' +
      '<button class="profile-close" onclick="closeHospitalProfile()" aria-label="关闭">&times;</button>' +
      '<div class="profile-head hospital-profile-head">' +
        '<div class="profile-avatar hospital-profile-avatar ' + hospitalIconType(h) + '">' +
          hospitalLogoHtml(h, "profile-logo") +
          '<span class="hospital-logo-initial">' + esc(hospitalIconInitial(h.name)) + '</span>' +
        '</div>' +
        '<div>' +
          '<div class="profile-name">' + esc(h.name) + '</div>' +
          '<div class="profile-title">' + esc([h.level, h.type].filter(function(v) { return v; }).join(" · ")) + '</div>' +
          '<div class="profile-hospital">' + esc(h.address || "暂无地址") + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="profile-grid hospital-profile-grid">' +
        '<div><span>医院等级</span><strong>' + esc(h.level || "暂无") + '</strong></div>' +
        '<div><span>医院类型</span><strong>' + esc(h.type || "暂无") + '</strong></div>' +
        '<div><span>床位规模</span><strong>' + esc(h.beds ? h.beds + " 张" : "暂无") + '</strong></div>' +
        '<div><span>日均门诊</span><strong>' + esc(h.daily_outpatients ? h.daily_outpatients + " 人次" : "暂无") + '</strong></div>' +
        '<div><span>急诊能力</span><strong>' + (h.emergency ? "支持急诊" : "常规门诊") + '</strong></div>' +
      '</div>' +
      '<div class="profile-section"><h4>联系方式</h4><div class="hospital-contact-line"><span>电话</span><strong>' + esc(h.phone || "暂无") + '</strong></div><div class="hospital-contact-line"><span>地址</span><strong>' + esc(h.address || "暂无") + '</strong></div></div>' +
      '<div class="profile-section"><h4>重点专科</h4><div class="dc-keywords">' + (strengths || '<span class="empty-mini">暂无重点专科信息</span>') + '</div></div>' +
      '<div class="profile-section"><h4>科室设置</h4><div class="dc-keywords">' + (departments || '<span class="empty-mini">暂无科室信息</span>') + '</div></div>' +
      (h.description ? '<div class="profile-section"><h4>医院简介</h4><p class="hospital-profile-desc">' + esc(h.description) + '</p></div>' : '') +
      '<div class="profile-actions">' +
        '<button class="btn btn-primary btn-sm" onclick="openHospitalNavigation(' + h.id + ')">立即导航</button>' +
        '<button class="btn btn-outline btn-sm" onclick="closeHospitalProfile()">关闭</button>' +
        '<button class="btn btn-primary btn-sm" onclick="closeHospitalProfile();navigate(\'hospital-detail\',{hid:' + h.id + '})">查看完整详情</button>' +
      '</div>' +
    '</div>';
  modal.classList.add("show");
}

function closeHospitalProfile() {
  var modal = document.getElementById("hospitalProfileModal");
  if (modal) modal.classList.remove("show");
}

// ========== 首页 ==========
function renderDashboard() {
  var main = $("#mainContent");
  if (!main) return;
  main.innerHTML = '<div class="loading"><div class="spinner"></div><p style="margin-top:12px">加载中...</p></div>';
  Promise.all([
    fetch(API + "/stats").then(function(res) { return res.json(); }),
    fetch(API + "/hospitals").then(function(res) { return res.json(); }),
    fetch(API + "/doctors").then(function(res) { return res.json(); }),
    fetch(API + "/transit/stats").then(function(res) { return res.json(); })
  ]).then(function(results) {
    var stats = results[0].data;
    var hospitals = results[1].data || [];
    var doctors = results[2].data || [];
    var transitStats = results[3].data || {};
    var doctorTypes = buildDoctorTypeCounts(doctors);
    var bedByDistrict = sumByGroup(hospitals, getHospitalDistrict, function(h) { return h.beds; });
    var outpatientByDistrict = sumByGroup(hospitals, getHospitalDistrict, function(h) { return h.daily_outpatients; });
    window._dashboardHospitals = hospitals;
    main.innerHTML =
      buildDashboardCommandCenter(stats, hospitals, doctors) +
      buildDashboardCarousel(stats) +
      '<h2 class="page-title">系统首页</h2>' +
      '<p class="page-subtitle">运行概览 · 医院、专家、床位与门诊规模一屏掌握</p>' +
      '<div class="stats-row">' +
        '<div class="stat-card accent-blue hospital-access-stat"><div class="stat-headline"><div class="stat-icon">' + uiIcon("hospital") + '</div><div><div class="stat-value">' + stats.total_hospitals + '</div><div class="stat-label">接入医院</div></div></div>' + buildHospitalMiniIcons(hospitals) + '</div>' +
        '<div class="stat-card accent-green"><div class="stat-headline"><div class="stat-icon">' + uiIcon("doctor") + '</div><div><div class="stat-value">' + (stats.total_real_doctors || stats.total_doctors) + '</div><div class="stat-label">在册专家</div></div></div>' + buildInlineBarChart(doctorTypes, "") + '</div>' +
        '<div class="stat-card accent-orange"><div class="stat-headline"><div class="stat-icon">' + uiIcon("bed") + '</div><div><div class="stat-value">' + (stats.total_beds / 1000).toFixed(1) + 'k</div><div class="stat-label">总床位数</div></div></div>' + buildInlineBarChart(bedByDistrict, "") + '</div>' +
        '<div class="stat-card accent-red"><div class="stat-headline"><div class="stat-icon">' + uiIcon("users") + '</div><div><div class="stat-value">' + (stats.daily_outpatients_total / 10000).toFixed(1) + '万</div><div class="stat-label">日均门诊量</div></div></div>' + buildInlineBarChart(outpatientByDistrict, "") + '</div>' +
      '</div>' +
      buildTransitFusionPanel(transitStats) +
      buildDashboardVisuals(stats, hospitals) +
      '<div class="card">' +
        '<div class="card-header"><span class="card-title">核心功能</span></div>' +
        '<div class="feature-grid">' +
          '<div class="feature-card"><div class="feature-card-icon">' + uiIcon("target") + '</div><h4>智能推荐引擎</h4><p>4种场景动态权重，精准匹配医院和医生。</p></div>' +
          '<div class="feature-card"><div class="feature-card-icon">' + uiIcon("dashboard") + '</div><h4>真实医生数据</h4><p>覆盖手术量、SCI论文、国自然、专利等量化指标。</p></div>' +
          '<div class="feature-card"><div class="feature-card-icon">' + uiIcon("map") + '</div><h4>地理位置服务</h4><p>按区域和定位计算距离，辅助就近选择优质医疗。</p></div>' +
          '<div class="feature-card"><div class="feature-card-icon">' + uiIcon("api") + '</div><h4>开放数据接口</h4><p>提供 RESTful API，方便第三方系统对接。</p></div>' +
        '</div>' +
      '</div>' +
      '<div class="card dashboard-map-card"><div class="card-header"><span class="card-title">医院空间分布</span><span style="font-size:12px;color:var(--text-secondary);">地图已移入首页底部</span></div><div id="dashboardMapContainer" class="map-container-enhanced dashboard-map"></div></div>';
    initDashboardCarousel();
    setTimeout(function() { renderMapInto("dashboardMapContainer", false); }, 200);
  }).catch(function() {
    main.innerHTML = '<div class="empty-state"><p>加载失败，请刷新重试</p></div>';
  });
}

// ========== 获取当前场景 ==========
function getSelectedScenario() {
  var active = document.querySelector(".scenario-option.active");
  return active ? active.dataset.scenario : "common";
}

function setRecommendScenario(scenario) {
  $$(".scenario-option").forEach(function(o) {
    o.classList.toggle("active", o.dataset.scenario === scenario);
  });
  var tipEl = $("#scenarioTip");
  if (tipEl) tipEl.innerHTML = uiIcon(SCENARIO_ICONS[scenario], "icon-inline") + esc(SCENARIO_TIPS[scenario]);
  var weightEl = $("#scenarioWeightViz");
  if (weightEl) weightEl.innerHTML = buildScenarioWeightViz(scenario);
  updateRecommendLiveViz();
}

function buildPatientProfileForm() {
  return '<div class="patient-profile-card">' +
    '<div class="patient-profile-head">' +
      '<div><strong>患者画像</strong><span>补充信息越完整，推荐排序越容易贴近真实就诊需求</span></div>' +
      '<span class="tag tag-green">可选</span>' +
    '</div>' +
    '<div class="patient-profile-grid">' +
      '<div class="form-group"><label class="form-label">年龄</label><input class="form-input" id="recAge" type="number" min="0" max="120" placeholder="例如：45"></div>' +
      '<div class="form-group"><label class="form-label">性别</label><select class="form-select" id="recGender"><option value="">未选择</option><option>男</option><option>女</option></select></div>' +
      '<div class="form-group"><label class="form-label">疾病名称</label><input class="form-input" id="recDiseaseName" placeholder="例如：冠心病、肺炎、腰椎间盘突出"></div>' +
      '<div class="form-group"><label class="form-label">检查类型</label><select class="form-select" id="recExamType"><option value="">未选择</option><option>普通门诊</option><option>复诊配药</option><option>检查报告解读</option><option>体检报告异常</option><option>手术咨询</option><option>急诊评估</option></select></div>' +
      '<div class="form-group"><label class="form-label">是否急诊</label><select class="form-select" id="recUrgency"><option value="">未选择</option><option>否，常规就诊</option><option>不确定，需要评估</option><option>是，需要尽快处理</option></select></div>' +
      '<div class="form-group"><label class="form-label">医保</label><select class="form-select" id="recInsurance"><option value="">未选择</option><option>常州职工医保</option><option>常州居民医保</option><option>江苏省医保</option><option>异地医保</option><option>自费</option></select></div>' +
      '<div class="form-group"><label class="form-label">期望就诊时间</label><select class="form-select" id="recVisitTime"><option value="">未选择</option><option>今天</option><option>明天</option><option>三天内</option><option>一周内</option><option>周末</option><option>工作日均可</option></select></div>' +
      '<div class="form-group"><label class="form-label">是否接受转诊</label><select class="form-select" id="recTransfer"><option value="">未选择</option><option>接受转诊</option><option>优先本区医院</option><option>优先三甲医院</option><option>不接受转诊</option><option>听从系统建议</option></select></div>' +
    '</div>' +
  '</div>';
}

function buildRecommendVoiceControl() {
  return '<div class="recommend-voice-card">' +
    '<div class="recommend-voice-head">' +
      '<div><strong>语音智能填表</strong><span>点击开始收音，完整说完后再次点击按钮结束收音并自动填表。</span></div>' +
      '<button type="button" id="recommendVoiceBtn" class="btn btn-outline btn-sm recommend-voice-btn" onclick="toggleRecommendVoiceFill()">' + uiIcon("api", "icon-inline") + '开始语音</button>' +
    '</div>' +
    '<div id="recommendVoiceStatus" class="recommend-voice-status">示例：我45岁男，天宁区，胸痛胸闷2天，想看冠心病，常州职工医保，希望今天就诊，优先三甲医院。</div>' +
    '<div id="recommendVoiceTranscript" class="recommend-voice-transcript"></div>' +
  '</div>';
}

function setRecommendField(id, value, filled, label) {
  if (!value) return;
  var el = document.getElementById(id);
  if (!el) return;
  el.value = value;
  if (filled && label) filled.push(label + "：" + value);
}

function parseChineseNumber(numText) {
  var text = String(numText || "");
  var map = { 零: 0, 一: 1, 二: 2, 两: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9 };
  if (/^\d+$/.test(text)) return parseInt(text, 10);
  if (text === "十") return 10;
  var tenIndex = text.indexOf("十");
  if (tenIndex >= 0) {
    var left = text.slice(0, tenIndex);
    var right = text.slice(tenIndex + 1);
    var tens = left ? map[left] || 0 : 1;
    var ones = right ? map[right] || 0 : 0;
    return tens * 10 + ones;
  }
  var value = 0;
  for (var i = 0; i < text.length; i++) value = value * 10 + (map[text[i]] || 0);
  return value || null;
}

function cleanVoiceDiseaseName(value) {
  var v = String(value || "").trim();
  v = v.replace(/^(一下|一下子|医生|医院|科室|看看|看一下)/, "");
  v = v.replace(/(医生|医院|科室|门诊|问题|方面|相关)$/g, "");
  if (!v || v.length < 2 || /今天|明天|医保|男|女|天宁|钟楼|武进|新北|金坛|溧阳/.test(v)) return "";
  return v;
}

function extractRecommendVoiceInfo(text) {
  var t = String(text || "").replace(/\s+/g, "");
  var info = {};
  var ageMatch = t.match(/(?:年龄)?(\d{1,3})(?:岁|周岁)/);
  if (ageMatch) info.age = ageMatch[1];
  if (!info.age) {
    var cnAgeMatch = t.match(/(?:年龄)?([一二两三四五六七八九十]{1,4})(?:岁|周岁)/);
    if (cnAgeMatch) {
      var cnAge = parseChineseNumber(cnAgeMatch[1]);
      if (cnAge && cnAge <= 120) info.age = String(cnAge);
    }
  }
  if (/女|女性|女士|姑娘|妈妈|母亲/.test(t)) info.gender = "女";
  else if (/男|男性|男士|先生|爸爸|父亲/.test(t)) info.gender = "男";

  for (var i = 0; i < DISTRICT_POINTS.length; i++) {
    var name = DISTRICT_POINTS[i].name;
    var shortName = name.replace(/[区市]$/, "");
    if (t.indexOf(name) >= 0 || t.indexOf(shortName) >= 0) { info.district = name; break; }
  }

  if (/急诊|马上|立刻|尽快|严重|呼吸困难|意识|大出血|卒中|胸痛/.test(t)) info.urgency = "是，需要尽快处理";
  if (/不确定|不知道是不是急/.test(t)) info.urgency = "不确定，需要评估";
  if (/不急|常规|普通门诊/.test(t)) info.urgency = "否，常规就诊";

  if (/急诊/.test(t)) info.examType = "急诊评估";
  else if (/手术|支架|开刀/.test(t)) info.examType = "手术咨询";
  else if (/体检|指标|异常/.test(t)) info.examType = "体检报告异常";
  else if (/报告|化验|检查结果|解读/.test(t)) info.examType = "检查报告解读";
  else if (/复诊|配药|开药/.test(t)) info.examType = "复诊配药";
  else if (/门诊|挂号|就诊|看病/.test(t)) info.examType = "普通门诊";

  if (/常州职工医保|职工医保/.test(t)) info.insurance = "常州职工医保";
  else if (/常州居民医保|居民医保/.test(t)) info.insurance = "常州居民医保";
  else if (/江苏省医保|省医保/.test(t)) info.insurance = "江苏省医保";
  else if (/异地医保|外地医保/.test(t)) info.insurance = "异地医保";
  else if (/自费/.test(t)) info.insurance = "自费";

  if (/今天|今日/.test(t)) info.visitTime = "今天";
  else if (/明天|明日/.test(t)) info.visitTime = "明天";
  else if (/三天|3天/.test(t)) info.visitTime = "三天内";
  else if (/一周|7天|七天/.test(t)) info.visitTime = "一周内";
  else if (/周末|星期六|星期天|星期日/.test(t)) info.visitTime = "周末";
  else if (/工作日/.test(t)) info.visitTime = "工作日均可";

  if (/不接受转诊|不想转诊|不要转诊/.test(t)) info.transfer = "不接受转诊";
  else if (/优先三甲|三甲/.test(t)) info.transfer = "优先三甲医院";
  else if (/本区|附近|就近/.test(t)) info.transfer = "优先本区医院";
  else if (/接受转诊|可以转诊|愿意转诊/.test(t)) info.transfer = "接受转诊";
  else if (/听从系统|听系统|系统建议/.test(t)) info.transfer = "听从系统建议";

  if (/手术|支架|开刀|重症|严重|急诊/.test(t)) info.scenario = "surgery";
  else if (/疑难|罕见|反复|长期|不明原因/.test(t)) info.scenario = "complex";
  else if (/常见|普通|复诊|配药/.test(t)) info.scenario = "common";
  else if (/初次|第一次|不确定|不知道挂什么科/.test(t)) info.scenario = "first_visit";

  var diseases = ["冠心病", "心绞痛", "心肌梗死", "肺炎", "肺结节", "高血压", "糖尿病", "腰椎间盘突出", "颈椎病", "胃炎", "胆结石", "阑尾炎", "脑梗", "脑卒中", "哮喘", "支气管炎", "骨折", "肾结石", "甲状腺结节", "乳腺结节", "白内障", "鼻炎", "中耳炎"];
  for (var d = 0; d < diseases.length; d++) {
    if (t.indexOf(diseases[d]) >= 0) { info.disease = diseases[d]; break; }
  }
  var diseaseMatch = t.match(/(?:疾病|病名|诊断|怀疑|考虑|想看|想咨询|咨询)(?:是|为|有)?([^，。；,.、]{2,16})/);
  if (!info.disease && diseaseMatch) info.disease = cleanVoiceDiseaseName(diseaseMatch[1]);
  info.condition = text;
  return info;
}

function applyRecommendVoiceInfo(text) {
  var info = extractRecommendVoiceInfo(text);
  var filled = [];
  setRecommendField("recAge", info.age, filled, "年龄");
  setRecommendField("recGender", info.gender, filled, "性别");
  setRecommendField("recDiseaseName", info.disease, filled, "疾病");
  setRecommendField("recExamType", info.examType, filled, "检查类型");
  setRecommendField("recUrgency", info.urgency, filled, "急诊");
  setRecommendField("recInsurance", info.insurance, filled, "医保");
  setRecommendField("recVisitTime", info.visitTime, filled, "就诊时间");
  setRecommendField("recTransfer", info.transfer, filled, "转诊");
  setRecommendField("recDistrict", info.district, filled, "区域");
  if (info.scenario) { setRecommendScenario(info.scenario); filled.push("场景：" + (SCENARIO_LABELS[info.scenario] || info.scenario)); }
  var cond = document.getElementById("recCondition");
  if (cond && info.condition) {
    cond.value = info.condition;
    filled.push("病情描述：已填入");
  }
  var status = document.getElementById("recommendVoiceStatus");
  if (status) status.textContent = filled.length ? "已自动填入：" + filled.join("；") : "已识别语音，但未匹配到明确字段，请手动补充。";
  var transcript = document.getElementById("recommendVoiceTranscript");
  if (transcript) transcript.textContent = text;
  updateRecommendLiveViz();
}

function toggleRecommendVoiceFill() {
  if (recommendVoiceRecognition) {
    recommendVoiceStopRequested = true;
    var stopBtn = document.getElementById("recommendVoiceBtn");
    var stopStatus = document.getElementById("recommendVoiceStatus");
    if (stopBtn) stopBtn.innerHTML = uiIcon("api", "icon-inline") + "处理中";
    if (stopStatus) stopStatus.textContent = "正在结束收音并整理识别内容...";
    try { recommendVoiceRecognition.stop(); } catch (e) {}
    return;
  }
  var SpeechRecognition = getSpeechRecognitionCtor();
  if (!SpeechRecognition) {
    toast("当前浏览器不支持语音识别，请使用 Chrome 或 Edge");
    return;
  }
  stopASVoice();
  var btn = document.getElementById("recommendVoiceBtn");
  var status = document.getElementById("recommendVoiceStatus");
  var transcript = document.getElementById("recommendVoiceTranscript");
  recommendVoiceTranscriptText = "";
  recommendVoiceStopRequested = false;
  try {
    var recognition = new SpeechRecognition();
    recommendVoiceRecognition = recognition;
    recognition.lang = "zh-CN";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;
    if (btn) { btn.classList.add("listening"); btn.innerHTML = uiIcon("api", "icon-inline") + "结束收音"; }
    if (status) status.textContent = "正在收音，请一次性说完；说完后再次点击“结束收音”自动填表。";
    if (transcript) transcript.textContent = "";
    recognition.onresult = function(event) {
      var interim = "";
      for (var i = event.resultIndex; i < event.results.length; i++) {
        var txt = event.results[i][0].transcript || "";
        if (event.results[i].isFinal) recommendVoiceTranscriptText += txt;
        else interim += txt;
      }
      if (transcript) transcript.textContent = recommendVoiceTranscriptText + interim;
    };
    recognition.onerror = function(event) {
      var type = event && event.error ? event.error : "";
      if (type === "not-allowed") { recommendVoiceStopRequested = true; toast("浏览器未授权麦克风，请允许后再试"); }
      else if (type === "no-speech") toast("暂时没有识别到语音，可继续说或再次点击结束");
      else { recommendVoiceStopRequested = true; toast("语音识别失败，请手动输入"); }
    };
    recognition.onend = function() {
      var text = (recommendVoiceTranscriptText || (transcript ? transcript.textContent : "") || "").trim();
      if (!recommendVoiceStopRequested && recommendVoiceRecognition) {
        try {
          recognition.start();
          return;
        } catch (e) {
          if (status) status.textContent = "浏览器已自动暂停收音，请再次点击按钮结束或重录。";
        }
      }
      if (btn) { btn.classList.remove("listening"); btn.innerHTML = uiIcon("api", "icon-inline") + "重新语音"; }
      recommendVoiceRecognition = null;
      recommendVoiceStopRequested = false;
      if (text) applyRecommendVoiceInfo(text);
      else if (status) status.textContent = "未识别到有效内容，请点击“重新语音”再试一次。";
    };
    recognition.start();
  } catch (e) {
    recommendVoiceRecognition = null;
    recommendVoiceStopRequested = false;
    if (btn) { btn.classList.remove("listening"); btn.innerHTML = uiIcon("api", "icon-inline") + "开始语音"; }
    toast("语音识别启动失败，请检查浏览器权限");
  }
}

function collectPatientProfile() {
  var fields = [
    ["年龄", "recAge"],
    ["性别", "recGender"],
    ["疾病名称", "recDiseaseName"],
    ["检查类型", "recExamType"],
    ["就诊紧急度", "recUrgency"],
    ["医保", "recInsurance"],
    ["期望就诊时间", "recVisitTime"],
    ["是否接受转诊", "recTransfer"]
  ];
  var profile = {};
  fields.forEach(function(item) {
    var el = document.getElementById(item[1]);
    var value = el ? String(el.value || "").trim() : "";
    if (value) profile[item[0]] = value;
  });
  return profile;
}

function buildConditionWithPatientProfile(condition, profile, district) {
  var parts = [];
  Object.keys(profile || {}).forEach(function(key) {
    parts.push(key + "：" + profile[key]);
  });
  if (district) parts.push("所在区域：" + district);
  parts.push("症状/病情：" + condition);
  return parts.join("；");
}

function buildDiseaseSignalCards() {
  return '<div class="recommend-disease-types">' +
    '<button type="button" onclick="setRecommendScenario(\'common\')"><span>普通病</span><b>门诊优先</b></button>' +
    '<button type="button" onclick="setRecommendScenario(\'first_visit\')"><span>不明确</span><b>先分诊</b></button>' +
    '<button type="button" onclick="setRecommendScenario(\'complex\')"><span>疑难病</span><b>专科优先</b></button>' +
    '<button type="button" onclick="setRecommendScenario(\'surgery\')"><span>较重/手术</span><b>专家优先</b></button>' +
  '</div>';
}

function estimateDeptMatches(condition) {
  var text = condition || "";
  var matches = {
    "呼吸内科": ["咳", "喘", "肺", "胸闷", "呼吸", "痰", "气短", "感冒", "鼻塞", "流涕", "咽痛"],
    "心血管内科": ["胸痛", "心慌", "心脏", "冠脉", "支架", "高血压"],
    "消化内科": ["胃", "腹", "腹泻", "呕吐", "反酸", "肝", "胆"],
    "神经内科": ["头晕", "头痛", "麻木", "偏瘫", "抽搐", "意识"],
    "骨科": ["腰", "腿", "骨", "关节", "颈椎", "骨折", "外伤"],
    "儿科": ["小儿", "儿童", "孩子", "宝宝", "发热咳嗽"],
    "妇产科": ["孕", "产", "妇", "月经", "阴道", "乳腺"],
    "急诊科": ["昏迷", "大出血", "剧烈", "呼吸困难", "不能说话", "抽搐"]
  };
  var scores = {};
  if (!text.trim()) {
    return { "呼吸内科": 0, "心血管内科": 0, "消化内科": 0, "神经内科": 0, "骨科": 0 };
  }
  Object.keys(matches).forEach(function(dept) {
    var hits = matches[dept].reduce(function(sum, token) {
      return sum + (text.indexOf(token) >= 0 ? 1 : 0);
    }, 0);
    scores[dept] = Math.min(96, 18 + hits * 24);
  });
  return Object.keys(scores).sort(function(a, b) { return scores[b] - scores[a]; }).slice(0, 5).reduce(function(obj, key) {
    obj[key] = scores[key];
    return obj;
  }, {});
}

function estimateRiskMix(condition, scenario) {
  var text = condition || "";
  var labels = riskMetricLabels(scenario);
  if (!text.trim()) return zeroRiskMix(scenario);
  var urgentWords = ["胸痛", "胸闷", "呼吸困难", "喘不上气", "气短", "憋气", "昏迷", "意识不清", "意识模糊", "大出血", "抽搐", "剧烈", "不能说话", "说话不清", "偏瘫", "一侧无力", "肢体无力", "口角歪斜", "突然", "大汗"];
  var urgentHits = urgentWords.reduce(function(sum, token) { return sum + (text.indexOf(token) >= 0 ? 1 : 0); }, 0);
  var routine = 62;
  var urgent = 24;
  var severe = 14;
  if (scenario === "surgery") { routine = 34; urgent = 32; severe = 34; }
  if (scenario === "complex") { routine = 38; urgent = 24; severe = 38; }
  if (scenario === "first_visit") { routine = 54; urgent = 28; severe = 18; }
  if (urgentHits) {
    severe = Math.min(82, severe + urgentHits * 18);
    urgent = Math.min(70, urgent + urgentHits * 10);
    routine = Math.max(8, 100 - severe - urgent);
  }
  var mix = {};
  mix[labels[0]] = routine;
  mix[labels[1]] = urgent;
  mix[labels[2]] = severe;
  return mix;
}

function riskMetricLabels(scenario) {
  if (scenario === "complex") return ["基础风险", "需尽快就诊", "疑难复杂度"];
  if (scenario === "surgery") return ["普通门诊适配", "手术需求", "重症风险"];
  if (scenario === "first_visit") return ["常规首诊", "需尽快就诊", "待排查风险"];
  return ["普通病", "需尽快就诊", "重症风险"];
}

function zeroRiskMix(scenario) {
  var labels = riskMetricLabels(scenario);
  var mix = {};
  labels.forEach(function(label) { mix[label] = 0; });
  return mix;
}

function buildRiskPills(mix) {
  return '<div class="risk-pill-row">' + Object.keys(mix).map(function(key) {
    var value = mix[key];
    var cls = (key.indexOf("重症") >= 0 || key.indexOf("复杂") >= 0 || key.indexOf("排查") >= 0) ? "danger" : (key.indexOf("尽快") >= 0 || key.indexOf("手术") >= 0 ? "warn" : "safe");
    return '<div class="risk-pill ' + cls + '"><span>' + esc(key) + '</span><strong>' + value + '%</strong><i style="width:' + value + '%;"></i></div>';
  }).join("") + '</div>';
}

function riskMixFromTriage(triage, scenario) {
  if (!triage) return zeroRiskMix(scenario);
  var labels = riskMetricLabels(scenario);
  var score = Number(triage.severity_score || 0);
  var routine = 0;
  var urgent = 0;
  var severe = 0;
  if (triage.level === "emergency") {
    routine = 0;
    urgent = Math.max(8, 100 - score);
    severe = Math.min(100, Math.max(88, score));
  } else if (triage.level === "urgent") {
    routine = Math.max(8, 100 - score);
    urgent = Math.min(92, Math.max(62, score));
    severe = Math.min(55, Math.round(score * 0.55));
  } else {
    routine = Math.max(50, 100 - score);
    urgent = Math.min(35, Math.round(score * 0.45));
    severe = Math.min(22, Math.round(score * 0.28));
  }
  if (scenario === "complex" && triage.level === "routine") {
    severe = Math.max(severe, Math.min(72, Math.round((triage.severity_score || 35) * 0.9)));
    routine = Math.max(0, 100 - urgent - severe);
  }
  var mix = {};
  mix[labels[0]] = routine;
  mix[labels[1]] = urgent;
  mix[labels[2]] = severe;
  return mix;
}

function deptScoresFromRecommendData(data, condition) {
  if (!data) return estimateDeptMatches("");
  var scores = estimateDeptMatches(condition || data.condition || "");
  var matched = data.matched_department || (data.triage && data.triage.matched_department) || "";
  if (matched) scores[matched] = Math.max(scores[matched] || 0, 86);
  (data.recommended_doctors || []).slice(0, 8).forEach(function(item, index) {
    var d = item.doctor || {};
    var dept = d._department_group || normalizeDepartmentName(d.department || item.matched_dept || "");
    if (!dept) return;
    var score = Math.round((item.match_score || 0.55) * 100) - index * 3;
    scores[dept] = Math.max(scores[dept] || 0, Math.max(35, score));
  });
  return Object.keys(scores).sort(function(a, b) { return scores[b] - scores[a]; }).slice(0, 5).reduce(function(obj, key) {
    obj[key] = Math.max(0, Math.min(96, scores[key]));
    return obj;
  }, {});
}

function buildRecommendInsightPanel(condition, scenario, data) {
  scenario = scenario || getSelectedScenario();
  var hasAnalysis = !!(data && data.triage);
  var deptScores = hasAnalysis ? deptScoresFromRecommendData(data, condition) : estimateDeptMatches("");
  var riskMix = hasAnalysis ? riskMixFromTriage(data.triage, scenario) : estimateRiskMix("", scenario);
  var scenarioLabel = SCENARIO_LABELS[scenario] || "智能推荐";
  var radarCondition = hasAnalysis ? (condition || data.condition || "") : "";
  var headText = hasAnalysis ? "已完成分析" : "点击推荐后更新";
  return '<div class="recommend-insight-panel">' +
    '<div class="insight-head">' +
      '<div><span>AI 实时研判</span><strong>' + esc(scenarioLabel) + '</strong></div>' +
      '<em>' + esc(headText) + '</em>' +
    '</div>' +
    buildRiskPills(riskMix) +
    '<div class="insight-grid">' +
      '<div class="insight-box insight-radar"><div class="insight-title">症状系统雷达</div>' + buildRadarVisual(radarCondition) + '</div>' +
      '<div class="insight-box"><div class="insight-title">科室匹配概率</div>' + buildHorizontalBarChart(deptScores, "%") + '</div>' +
    '</div>' +
    '<div class="recommend-pathway">' +
      '<div><b>01</b><span>病情描述</span></div><i></i>' +
      '<div><b>02</b><span>风险分层</span></div><i></i>' +
      '<div><b>03</b><span>科室匹配</span></div><i></i>' +
      '<div><b>04</b><span>医生/医院推荐</span></div>' +
    '</div>' +
  '</div>';
}

function updateRecommendLiveViz(data) {
  var input = document.getElementById("recCondition");
  var panel = document.getElementById("recommendLiveViz");
  if (!panel) return;
  var scenario = getSelectedScenario();
  if (data && data.scenario && !scenario) scenario = data.scenario;
  if (data && data.effective_scenario && !scenario) scenario = data.effective_scenario;
  panel.innerHTML = buildRecommendInsightPanel(input ? input.value : "", scenario, data || null);
}

// ========== 智能推荐 ==========
function renderRecommend() {
  $("#mainContent").innerHTML =
    '<div class="recommend-hero recommend-hero-rich">' +
      '<div>' +
        '<h2 class="page-title">智能推荐</h2>' +
        '<p class="page-subtitle">把病情描述、风险分层、科室匹配和医生推荐放在同一个问诊工作台里，推荐结果弹窗展示，页面保留实时研判摘要。</p>' +
      '</div>' +
      '<button class="btn btn-outline recommend-assistant-btn" onclick="startAssistant()">打开小助手</button>' +
    '</div>' +
    '<div class="care-alert recommend-safety-alert"><strong>安全提示</strong><span>普通感冒、轻微咳嗽、鼻塞流涕等可按常见病门诊推荐；只有出现胸痛、呼吸困难、意识障碍、大出血、疑似卒中等红旗症状时，系统才会升级为急症提醒。</span></div>' +
    '<div class="recommend-signal-row">' +
      '<div class="signal-blue"><strong>专科匹配</strong><span>症状、疾病、手术名称自动映射科室</span></div>' +
      '<div class="signal-green"><strong>病情分层</strong><span>普通、急症、重症分别调整推荐权重</span></div>' +
      '<div class="signal-amber"><strong>距离可及</strong><span>支持区域估算和浏览器自动定位</span></div>' +
      '<div class="signal-purple"><strong>结果解释</strong><span>展示首推医生、医院和匹配原因</span></div>' +
    '</div>' +
    '<div class="recommend-layout">' +
      '<div class="card recommend-form-wrapper">' +
        '<div class="card-header recommend-card-header"><span class="card-title">病情录入工作台</span><span class="tag tag-blue">动态权重</span></div>' +
        buildDiseaseSignalCards() +
        '<div class="form-group">' +
          '<label class="form-label">推荐场景</label>' +
          '<div class="scenario-selector" id="scenarioSelector">' +
            '<div class="scenario-option" data-scenario="surgery"><div class="sc-icon">' + uiIcon("surgery", "icon-lg") + '</div><div class="sc-name">手术/重症</div></div>' +
            '<div class="scenario-option active" data-scenario="common"><div class="sc-icon">' + uiIcon("pill", "icon-lg") + '</div><div class="sc-name">常见病症</div></div>' +
            '<div class="scenario-option" data-scenario="complex"><div class="sc-icon">' + uiIcon("lab", "icon-lg") + '</div><div class="sc-name">疑难/罕见病</div></div>' +
            '<div class="scenario-option" data-scenario="first_visit"><div class="sc-icon">' + uiIcon("hospital", "icon-lg") + '</div><div class="sc-name">初次就诊</div></div>' +
          '</div>' +
          '<div id="scenarioTip" class="scenario-tip">' + uiIcon("pill", "icon-inline") + '专科匹配与距离可及优先，普通病症避免过度占用顶级专家资源</div>' +
          '<div id="scenarioWeightViz">' + buildScenarioWeightViz("common") + '</div>' +
        '</div>' +
        '<div id="recommendFormInner">' +
          buildPatientProfileForm() +
          buildRecommendVoiceControl() +
          '<div class="form-group"><label class="form-label">病情 / 症状描述 *</label><textarea class="form-input recommend-condition-input" id="recCondition" rows="6" placeholder="请尽量完整描述症状、持续时间、疼痛位置、既往病史或想咨询的疾病/手术，例如：胸痛胸闷 2 天，活动后加重，想咨询冠脉支架相关医生。"></textarea></div>' +
          '<div class="quick-examples">' +
            '<button class="quick-chip" onclick="setRecommendExample(\'胸痛胸闷需要做冠脉支架\')">胸痛胸闷</button>' +
            '<button class="quick-chip" onclick="setRecommendExample(\'反复咳嗽三个月\')">反复咳嗽</button>' +
            '<button class="quick-chip" onclick="setRecommendExample(\'腰痛半年，怀疑腰椎间盘突出\')">腰痛半年</button>' +
            '<button class="quick-chip" onclick="setRecommendExample(\'小儿发热咳嗽\')">小儿发热</button>' +
          '</div>' +
          buildDistrictControl() +
          '<button class="btn btn-primary" onclick="doRecommend()" style="width:100%;justify-content:center;padding:12px;">立即推荐</button>' +
          '<div class="recommend-note">可输入疾病名、症状、科室名或手术名称。初次就诊可点击右下角悬浮球，让小助手逐步问诊。</div>' +
        '</div>' +
      '</div>' +
      '<div class="recommend-side">' +
        '<div id="recommendLiveViz">' + buildRecommendInsightPanel("", "common") + '</div>' +
        '<div class="recommend-results" id="recResults">' +
          buildRecommendEmptyState() +
        '</div>' +
        buildRecommendRecordPanel() +
      '</div>' +
    '</div>';

  setTimeout(function() {
    $$(".scenario-option").forEach(function(opt) {
      opt.addEventListener("click", function() {
        var prev = getSelectedScenario();
        var sc = this.dataset.scenario;
        setRecommendScenario(sc);
        if (sc === "first_visit" && prev !== "first_visit") startAssistant();
      });
    });
    var liveInput = $("#recCondition");
    if (liveInput) {
      liveInput.addEventListener("input", function() {
        updateRecommendLiveViz();
      });
    }
    if (window._recommendPrefill) {
      var prefill = window._recommendPrefill;
      var input = $("#recCondition");
      if (prefill.scenario) setRecommendScenario(prefill.scenario);
      if (input) input.value = prefill.condition || "";
      delete window._recommendPrefill;
    }
    requestRecommendAutoLocation();
  }, 100);
}

function buildScenarioWeightViz(scenario) {
  var rows = SCENARIO_CATEGORY_WEIGHTS[scenario] || SCENARIO_CATEGORY_WEIGHTS.surgery;
  var html = '<div class="scenario-weight-card">' +
    '<div class="scenario-weight-head"><strong>病类判断权重</strong><span>当前场景下系统优先判断的病情类型</span></div>' +
    '<div class="scenario-weight-grid">';
  for (var i = 0; i < rows.length; i++) {
    html += '<div class="scenario-weight-row">' +
      '<div class="scenario-weight-label"><span>' + esc(rows[i][0]) + '</span><b>' + rows[i][1] + '%</b></div>' +
      '<div class="scenario-weight-track"><i style="width:' + rows[i][1] + '%;background:' + rows[i][2] + ';"></i></div>' +
    '</div>';
  }
  html += '</div></div>';
  return html;
}

function buildRecommendEmptyState() {
  return '<div class="recommend-empty-panel">' +
    '<div class="recommend-empty-head">' +
      '<strong>等待生成推荐结果</strong>' +
      '<p>填写左侧病情描述后，完整推荐会以弹窗展示；这里保留摘要和再次打开入口。</p>' +
    '</div>' +
    '<div class="recommend-empty-grid">' +
      '<div><b>01</b><span>识别病情轻重</span></div>' +
      '<div><b>02</b><span>匹配专科方向</span></div>' +
      '<div><b>03</b><span>计算医生权重</span></div>' +
      '<div><b>04</b><span>结合医院与距离</span></div>' +
    '</div>' +
    '<div class="recommend-flow-mini">' +
      '<span style="width:74%;"></span>' +
      '<span style="width:58%;"></span>' +
      '<span style="width:88%;"></span>' +
    '</div>' +
  '</div>';
}

var RECOMMEND_RECORD_KEY = "medicalRecommendRecords";
var TEST_SESSION_KEY = "medicalTesterSessionId";

function getTesterSessionId() {
  var id = localStorage.getItem(TEST_SESSION_KEY);
  if (!id) {
    id = "tester-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(TEST_SESSION_KEY, id);
  }
  return id;
}

function getRecommendRecords() {
  try {
    var list = JSON.parse(localStorage.getItem(RECOMMEND_RECORD_KEY) || "[]");
    return Array.isArray(list) ? list : [];
  } catch (e) {
    return [];
  }
}

function saveRecommendRecord(record) {
  var list = getRecommendRecords();
  list.unshift(record);
  localStorage.setItem(RECOMMEND_RECORD_KEY, JSON.stringify(list.slice(0, 8)));
  renderRecommendRecords();
  uploadTestRecord(record);
}

function uploadTestRecord(record) {
  if (!record) return;
  var payload = {
    tester_session: getTesterSessionId(),
    page: location.pathname,
    record: record,
    user: sessionStorage.getItem("medicalUser") || "",
    role: sessionStorage.getItem("medicalRole") || "",
    screen: { width: window.innerWidth, height: window.innerHeight }
  };
  fetch(API + "/test-record", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).catch(function() {});
}

function clearRecommendRecords() {
  localStorage.removeItem(RECOMMEND_RECORD_KEY);
  renderRecommendRecords();
  toast("已清空推荐记录");
}

function buildRecommendRecordPanel() {
  var records = getRecommendRecords();
  var chatCount = asState && asState.msgs ? asState.msgs.length : 0;
  return '<div class="card recommend-record-card">' +
    '<div class="card-header recommend-record-head">' +
      '<span class="card-title">聊天记录与推荐记录</span>' +
    '</div>' +
    '<div class="recommend-record-launch">' +
      '<div><strong>' + records.length + ' 条推荐记录</strong><span>当前会话 ' + chatCount + ' 条聊天消息</span></div>' +
      '<button class="btn btn-primary btn-sm" onclick="openRecommendRecordModal()">查看记录</button>' +
      '<button class="btn btn-outline btn-sm" onclick="startAssistant()">继续问小助手</button>' +
    '</div>' +
  '</div>';
}

function buildRecommendChatLog() {
  var msgs = asState && asState.msgs && asState.msgs.length ? asState.msgs : [];
  if (!msgs.length) {
    var records = getRecommendRecords();
    for (var i = 0; i < records.length; i++) {
      if (records[i].messages && records[i].messages.length) {
        msgs = records[i].messages;
        break;
      }
    }
  }
  if (!msgs.length) return '<div class="recommend-record-empty">暂无聊天记录，点击右下角小助手开始问诊。</div>';
  return msgs.slice(-8).map(function(msg) {
    return '<div class="recommend-chat-line ' + (msg.role === "user" ? "user" : "assistant") + '">' +
      '<span>' + (msg.role === "user" ? "我" : "小助手") + '</span>' +
      '<p>' + esc(msg.text) + '</p>' +
    '</div>';
  }).join("");
}

function buildRecommendRecordList(records) {
  if (!records || !records.length) return '<div class="recommend-record-empty">暂无推荐记录。</div>';
  return records.map(function(item, index) {
    return '<button class="recommend-record-item" onclick="restoreRecommendRecord(' + index + ')">' +
      '<div><strong>' + esc(item.condition || "问诊记录") + '</strong><span>' + esc(item.time || "") + ' · ' + esc(item.source || "智能推荐") + '</span></div>' +
      '<em>' + esc(item.department || "科室待确认") + ' · ' + esc(item.triage || "常规") + '</em>' +
      '<b>' + (item.doctorCount || 0) + ' 位医生 / ' + (item.hospitalCount || 0) + ' 家医院</b>' +
    '</button>';
  }).join("");
}

function renderRecommendRecords() {
  var launch = document.querySelector(".recommend-record-launch");
  if (launch) {
    var records = getRecommendRecords();
    var chatCount = asState && asState.msgs ? asState.msgs.length : 0;
    launch.querySelector("strong").textContent = records.length + " 条推荐记录";
    launch.querySelector("span").textContent = "当前会话 " + chatCount + " 条聊天消息";
  }
  var chat = document.getElementById("recommendChatLog");
  if (chat) chat.innerHTML = buildRecommendChatLog();
  var list = document.getElementById("recommendRecordList");
  if (list) list.innerHTML = buildRecommendRecordList(getRecommendRecords());
}

function openRecommendRecordModal() {
  var modal = document.getElementById("recommendRecordModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "recommendRecordModal";
    modal.className = "recommend-result-modal recommend-record-modal";
    modal.onclick = function(e) { if (e.target === modal) closeRecommendRecordModal(); };
    document.body.appendChild(modal);
  }
  modal.innerHTML =
    '<div class="recommend-result-card recommend-record-modal-card" role="dialog" aria-modal="true">' +
      '<button class="profile-close" onclick="closeRecommendRecordModal()" aria-label="关闭">&times;</button>' +
      '<div class="recommend-result-head">' +
        '<div><span class="tag tag-blue">问诊记录</span><h3>聊天记录与推荐记录</h3><p>可查看小助手最近对话，也可点击历史推荐快速回填病情描述。</p></div>' +
      '</div>' +
      '<div class="recommend-record-modal-grid">' +
        '<div class="recommend-record-section"><div class="recommend-record-title">小助手聊天</div><div id="recommendChatLog" class="recommend-chat-log">' + buildRecommendChatLog() + '</div><button class="btn btn-outline btn-sm" onclick="closeRecommendRecordModal();startAssistant()" style="margin-top:10px;">继续问小助手</button></div>' +
        '<div class="recommend-record-section"><div class="recommend-record-title">最近推荐</div><div id="recommendRecordList">' + buildRecommendRecordList(getRecommendRecords()) + '</div><button class="btn btn-outline btn-sm" onclick="clearRecommendRecords()" style="margin-top:10px;">清空记录</button></div>' +
      '</div>' +
    '</div>';
  modal.classList.add("show");
}

function closeRecommendRecordModal() {
  var modal = document.getElementById("recommendRecordModal");
  if (modal) modal.classList.remove("show");
}

function parseStructuredRecommendCondition(text) {
  var raw = String(text || "").trim();
  var fields = {};
  raw.split(/[；;]/).forEach(function(part) {
    var item = part.trim();
    if (!item) return;
    var match = item.match(/^([^：:]{2,10})[：:]\s*(.+)$/);
    if (!match) return;
    fields[match[1].trim()] = match[2].trim();
  });
  var symptom = fields["症状/病情"] || fields["病情"] || fields["症状"] || "";
  if (!symptom && raw) {
    symptom = raw.replace(/(?:年龄|性别|疾病名称|疾病|检查类型|就诊紧急度|是否急诊|医保|期望就诊时间|是否接受转诊|所在区域)[：:][^；;]+[；;]?/g, "").trim();
  }
  if (!fields["疾病名称"] && fields["疾病"]) fields["疾病名称"] = fields["疾病"];
  if (!fields["就诊紧急度"] && fields["是否急诊"]) fields["就诊紧急度"] = fields["是否急诊"];
  return { fields: fields, symptom: symptom || raw };
}

function restoreRecommendRecord(index) {
  var record = getRecommendRecords()[index];
  if (!record) return;
  var parsed = parseStructuredRecommendCondition(record.condition || "");
  var fields = parsed.fields || {};
  setRecommendField("recAge", fields["年龄"]);
  setRecommendField("recGender", fields["性别"]);
  setRecommendField("recDiseaseName", fields["疾病名称"]);
  setRecommendField("recExamType", fields["检查类型"]);
  setRecommendField("recUrgency", fields["就诊紧急度"]);
  setRecommendField("recInsurance", fields["医保"]);
  setRecommendField("recVisitTime", fields["期望就诊时间"]);
  setRecommendField("recTransfer", fields["是否接受转诊"]);
  setRecommendField("recDistrict", fields["所在区域"]);
  var input = document.getElementById("recCondition");
  if (input) {
    input.value = parsed.symptom || "";
    input.focus();
  }
  updateRecommendLiveViz();
  toast("已按字段恢复推荐记录");
}

function makeRecommendRecord(data, condition, source) {
  var now = new Date();
  var msgs = asState && asState.msgs ? asState.msgs.slice(-10) : [];
  return {
    time: now.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }),
    source: source || "智能推荐",
    condition: condition || data.condition || "",
    department: data.matched_department || "",
    triage: data.triage ? (data.triage.label || "") : "",
    expertPreference: data.expert_preference || "system",
    visitPath: data.resource_strategy ? (data.resource_strategy.visit_path || "") : "",
    doctorCount: (data.recommended_doctors || []).length,
    hospitalCount: (data.recommended_hospitals || []).length,
    messages: msgs
  };
}

function buildResourceStrategyPanel(data) {
  if (!data || !data.resource_strategy) return "";
  var strategy = data.resource_strategy || {};
  var triage = data.triage || {};
  var preference = data.expert_preference || strategy.expert_preference || "system";
  var level = triage.level || "routine";
  var tagClass = level === "emergency" ? "tag-red" : (level === "urgent" ? "tag-orange" : "tag-green");
  var warning = strategy.code === "routine_must_expert"
    ? '<div class="resource-strategy-warning">系统已尊重“必须专家号”，但当前病情倾向普通病症，不建议优先占用顶级专家资源。</div>'
    : "";
  return '<div class="resource-strategy-panel">' +
    '<div class="resource-strategy-main">' +
      '<span class="tag ' + tagClass + '">' + esc(triage.label || "分诊完成") + '</span>' +
      '<h4>' + esc(strategy.title || "就诊资源适配") + '</h4>' +
      '<p>' + esc(strategy.notice || "系统已按病情轻重、距离可及和科室匹配进行综合推荐。") + '</p>' +
    '</div>' +
    '<div class="resource-strategy-grid">' +
      '<div><span>建议路径</span><strong>' + esc(strategy.visit_path || "普通门诊") + '</strong></div>' +
      '<div><span>专家号意图</span><strong>' + esc(EXPERT_PREFERENCE_LABELS[preference] || preference) + '</strong></div>' +
      '<div><span>匹配科室</span><strong>' + esc(data.matched_department || "待确认") + '</strong></div>' +
    '</div>' +
    warning +
  '</div>';
}

function buildRecommendSummaryPanel(data, condition) {
  var doctors = data.recommended_doctors || [];
  var hospitals = data.recommended_hospitals || [];
  var triage = data.triage || {};
  var strategy = data.resource_strategy || {};
  var topDoctor = doctors.length ? doctors[0].doctor : null;
  var topHospital = hospitals.length ? hospitals[0].hospital : null;
  return '<div class="recommend-summary-panel">' +
    '<div class="recommend-summary-head">' +
      '<span class="tag tag-blue">已生成</span>' +
      '<strong>推荐结果已弹出</strong>' +
      '<p>' + esc(condition || data.condition || "本次病情") + '</p>' +
    '</div>' +
    '<div class="recommend-summary-grid">' +
      '<div><span>分诊等级</span><b>' + esc(triage.label || "常规就诊") + '</b></div>' +
      '<div><span>匹配科室</span><b>' + esc(data.matched_department || "待确认") + '</b></div>' +
      '<div><span>建议路径</span><b>' + esc(strategy.visit_path || "普通门诊") + '</b></div>' +
      '<div><span>推荐医院</span><b>' + hospitals.length + ' 家</b></div>' +
    '</div>' +
    (topDoctor ? '<div class="recommend-topline"><span>首推医生</span><strong>' + esc(topDoctor.name) + '</strong><em>' + esc(topDoctor.hospital_name || "") + '</em></div>' : '') +
    (topHospital ? '<div class="recommend-topline"><span>首推医院</span><strong>' + esc(topHospital.name) + '</strong><em>' + esc(topHospital.level || "") + '</em></div>' : '') +
    '<button class="btn btn-primary" onclick="openRecommendResultModal()" style="width:100%;justify-content:center;margin-top:14px;">查看完整弹窗结果</button>' +
  '</div>';
}

function openRecommendResultModal(title, html) {
  var modal = document.getElementById("recommendResultModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "recommendResultModal";
    modal.className = "recommend-result-modal";
    modal.onclick = function(e) { if (e.target === modal) closeRecommendResultModal(); };
    document.body.appendChild(modal);
  }
  if (html) window._lastRecommendResultHtml = html;
  modal.innerHTML =
    '<div class="recommend-result-card" role="dialog" aria-modal="true">' +
      '<button class="profile-close" onclick="closeRecommendResultModal()" aria-label="关闭">&times;</button>' +
      '<div class="recommend-result-head">' +
        '<div><span class="tag tag-blue">智能推荐</span><h3>' + esc(title || "推荐结果") + '</h3><p>可直接优推医生，或按距离重新排序已优推医生。</p></div>' +
      '</div>' +
      '<div class="recommend-result-body">' + (window._lastRecommendResultHtml || '<div class="empty-state"><p>暂无推荐结果</p></div>') + '</div>' +
    '</div>';
  modal.classList.add("show");
  setTimeout(function() { updateStarButtons(); updateRerankToolbar(); }, 50);
}

function closeRecommendResultModal() {
  var modal = document.getElementById("recommendResultModal");
  if (modal) modal.classList.remove("show");
}

function setRecommendExample(text) {
  var input = document.getElementById("recCondition");
  if (!input) return;
  input.value = text;
  input.focus();
  updateRecommendLiveViz();
}

function buildTriageBanner(triage) {
  if (!triage) return "";
  if (triage.level === "emergency" || triage.level === "urgent") {
    var severeReasons = (triage.reasons || []).map(function(r) { return esc(r); }).join("；");
    return '<div class="triage-top-alert triage-top-' + esc(triage.level) + '">' +
      '<div class="triage-top-main">' +
        '<span class="tag ' + (triage.level === "emergency" ? "tag-red" : "tag-orange") + '">' + esc(triage.label || "急症提示") + '</span>' +
        '<strong>' + esc(triage.care_level || "请优先急诊评估") + '</strong>' +
        '<b>风险值 ' + (triage.severity_score || 0) + '</b>' +
      '</div>' +
      (severeReasons ? '<p class="triage-top-reason">' + severeReasons + '</p>' : '') +
      (triage.disclaimer ? '<p class="triage-top-disclaimer">' + esc(triage.disclaimer) + '</p>' : '') +
    '</div>';
  }
  var color = triage.level === "emergency" ? "tag-red" : (triage.level === "urgent" ? "tag-orange" : "tag-green");
  var reasons = (triage.reasons || []).map(function(r) { return esc(r); }).join("；");
  var bucket = triage.severity_bucket ? '<span class="tag tag-soft" style="margin-left:8px;">' + esc(triage.severity_bucket) + '</span>' : "";
  return '<div class="card triage-card triage-' + esc(triage.level || "routine") + '" style="margin-bottom:16px;">' +
    '<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;">' +
      '<div><span class="tag ' + color + '">' + esc(triage.label || "分诊提示") + '</span>' +
      bucket +
      '<span style="margin-left:8px;font-size:13px;color:var(--text-secondary);">' + esc(triage.care_level || "") + '</span></div>' +
      '<span style="font-size:12px;color:var(--text-secondary);">风险值 ' + (triage.severity_score || 0) + '</span>' +
    '</div>' +
    (reasons ? '<p style="margin-top:10px;font-size:13px;color:var(--text-secondary);">' + reasons + '</p>' : '') +
    (triage.disclaimer ? '<p style="margin-top:8px;font-size:12px;color:var(--text-secondary);">' + esc(triage.disclaimer) + '</p>' : '') +
  '</div>';
}

function isSevereTriage(triage) {
  return triage && (triage.level === "emergency" || triage.level === "urgent");
}

function buildEmergencyPriorityPanel(data) {
  if (!data || !isSevereTriage(data.triage)) return "";
  var doctorItem = (data.recommended_doctors || [])[0];
  var hospitalItem = (data.recommended_hospitals || [])[0];
  var d = doctorItem ? doctorItem.doctor : null;
  var h = hospitalItem ? hospitalItem.hospital : null;
  var doctorDistance = doctorItem && doctorItem.hospital_distance_km != null ? Number(doctorItem.hospital_distance_km).toFixed(1) + "km" : "";
  var hospitalDistance = hospitalItem && hospitalItem.distance != null ? hospitalItem.distance + "km" : "";
  return '<div class="emergency-priority-panel">' +
    '<div class="emergency-priority-head">' +
      '<span class="tag tag-red">急症提醒</span>' +
      '<strong>请立即拨打120或前往就近急诊</strong>' +
      '<p>以下医生/医院仅作为就近急诊与专科能力参考，不替代急救处置。</p>' +
      '<div class="emergency-call-line"><span>医院急救电话</span><a href="tel:120" onclick="event.stopPropagation()">120</a><button class="btn btn-primary btn-sm" onclick="event.stopPropagation();window.location.href=\'tel:120\'">拨打120</button></div>' +
    '</div>' +
    '<div class="emergency-priority-grid">' +
      (d ? '<div class="emergency-priority-card">' +
        '<span>最近优先专家</span>' +
        '<h4>' + esc(d.name) + '</h4>' +
        '<p>' + esc([d.title, d.hospital_name, d._department_group || normalizeDepartmentName(d.department)].filter(function(v) { return v; }).join(" · ")) + '</p>' +
        '<div class="emergency-priority-meta">' +
          (doctorDistance ? '<b>距医院约 ' + esc(doctorDistance) + '</b>' : '') +
          '<b>急症优先分 ' + Math.round((doctorItem.emergency_priority_score || doctorItem.match_score || 0) * 100) + '%</b>' +
        '</div>' +
        '<button class="btn btn-primary btn-sm" onclick="openDoctorProfile(' + d.id + ')">查看医生</button>' +
      '</div>' : '') +
      (h ? '<div class="emergency-priority-card">' +
        '<span>最近急诊医院</span>' +
        '<h4>' + esc(h.name) + '</h4>' +
        '<p>' + esc([h.level, h.type, h.address].filter(function(v) { return v; }).join(" · ")) + '</p>' +
        '<div class="emergency-priority-meta">' +
          (hospitalDistance ? '<b>距您约 ' + esc(hospitalDistance) + '</b>' : '') +
          '<b>' + (h.emergency ? "支持急诊" : "常规门诊") + '</b>' +
        '</div>' +
        '<button class="btn btn-primary btn-sm" onclick="openHospitalNavigation(' + h.id + ')">立即导航</button>' +
      '</div>' : '') +
    '</div>' +
  '</div>';
}

// ========== 执行推荐 ==========
var EXPERT_PREFERENCE_LABELS = {
  system: "系统判断",
  no_expert: "不需要专家号",
  wish_expert: "希望专家号",
  must_expert: "必须专家号",
  named_followup: "已有指定专家复诊"
};

function doRecommend() {
  var condEl = $("#recCondition");
  if (!condEl) return;
  var condition = condEl.value.trim();
  if (!condition) { toast("请输入病情或症状描述"); return; }
  requestManualFollowupBeforeRecommend(condition);
}

function requestManualFollowupBeforeRecommend(condition) {
  var scenario = getSelectedScenario();
  var patientProfile = collectPatientProfile ? collectPatientProfile() : {};
  var districtEl = $("#recDistrict");
  var district = districtEl ? districtEl.value : "天宁区";
  var enrichedCondition = buildConditionWithPatientProfile ? buildConditionWithPatientProfile(condition, patientProfile, district) : condition;
  var resultsDiv = $("#recResults");
  if (resultsDiv) resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在判断是否需要补充信息...</p></div>';
  fetch(API + "/followup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ condition: enrichedCondition, scenario: scenario })
  }).then(function(res) { return res.json(); }).then(function(json) {
    if (resultsDiv) resultsDiv.innerHTML = "";
    var questions = json && json.data && json.data.followup ? (json.data.followup.questions || []) : [];
    if (questions.length) {
      openManualFollowupModal(questions, function(answers) {
        appendManualFollowupAnswers(questions, answers);
        openExpertPreferenceModal();
      });
    } else {
      openExpertPreferenceModal();
    }
  }).catch(function() {
    if (resultsDiv) resultsDiv.innerHTML = "";
    openExpertPreferenceModal();
  });
}

function openManualFollowupModal(questions, done) {
  var modal = document.getElementById("manualFollowupModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "manualFollowupModal";
    modal.className = "expert-preference-modal";
    modal.onclick = function(e) { if (e.target === modal) closeManualFollowupModal(); };
    document.body.appendChild(modal);
  }
  var index = 0;
  var answers = {};
  function renderQuestion() {
    var q = questions[index];
    var options = q.options || [];
    modal.innerHTML =
      '<div class="expert-preference-card" role="dialog" aria-modal="true">' +
        '<button class="profile-close" onclick="closeManualFollowupModal()" aria-label="关闭">&times;</button>' +
        '<div class="expert-preference-head">' +
          '<span class="tag tag-blue">补充问诊 ' + (index + 1) + '/' + questions.length + '</span>' +
          '<h3>' + esc(q.question || "请补充信息") + '</h3>' +
          '<p>' + esc(q.reason || "补充信息越完整，推荐科室越准确。") + '</p>' +
        '</div>' +
        (options.length ? '<div class="expert-preference-options">' + options.map(function(opt) {
          return '<button type="button" class="expert-preference-option" data-answer="' + esc(opt) + '"><strong>' + esc(opt) + '</strong></button>';
        }).join("") + '</div>' :
        '<textarea id="manualFollowupText" class="form-input" rows="4" placeholder="请补充说明"></textarea><div class="expert-preference-actions" style="margin-top:14px;"><button class="btn btn-primary" id="manualFollowupSend">下一题</button></div>') +
      '</div>';
    if (options.length) {
      modal.querySelectorAll(".expert-preference-option").forEach(function(btn) {
        btn.addEventListener("click", function() { saveAnswer(btn.getAttribute("data-answer") || ""); });
      });
    } else {
      var send = document.getElementById("manualFollowupSend");
      if (send) send.onclick = function() {
        var input = document.getElementById("manualFollowupText");
        saveAnswer(input ? input.value.trim() : "");
      };
    }
  }
  function saveAnswer(value) {
    answers[qKey(questions[index], index)] = value || "未补充";
    index++;
    if (index >= questions.length) {
      closeManualFollowupModal();
      if (typeof done === "function") done(answers);
      return;
    }
    renderQuestion();
  }
  modal._manualFollowupDone = done;
  modal.classList.add("show");
  renderQuestion();
}

function qKey(q, index) {
  return (q && q.id ? q.id : ("q" + index));
}

function closeManualFollowupModal() {
  var modal = document.getElementById("manualFollowupModal");
  if (modal) modal.classList.remove("show");
}

function appendManualFollowupAnswers(questions, answers) {
  var input = document.getElementById("recCondition");
  if (!input) return;
  var parts = [];
  questions.forEach(function(q, i) {
    var val = answers[qKey(q, i)];
    var label = manualFollowupAnswerLabel(q);
    if (val) parts.push(label + "：" + val);
  });
  if (parts.length) {
    input.value = input.value.trim() + "；补充问诊：" + parts.join("；");
  }
}

function manualFollowupAnswerLabel(q) {
  var id = q && q.id ? q.id : "";
  var map = {
    main_symptom_more: "补充症状",
    duration: "持续时间",
    severity: "严重程度",
    onset_pattern: "发病方式",
    symptom_location: "不适部位",
    companion_symptoms: "伴随表现",
    trigger_factor: "诱因场景",
    history_medicine: "病史用药检查",
    visit_goal: "就诊目的",
    red_flag_check: "危险信号",
    neuro_detail: "神经系统风险补充",
    chest_breath_detail: "胸部呼吸补充",
    resp_infection_detail: "呼吸感染补充",
    digest_detail: "消化系统补充",
    tumor_detail: "报告病灶补充",
    known_disease_status: "疾病来源",
    known_disease_evidence: "检查治疗依据",
    known_disease_goal: "就诊目的",
    topk_detail: "候选疾病补充"
  };
  return map[id] || "补充信息";
}

function closeExpertPreferenceModal() {
  var modal = document.getElementById("expertPreferenceModal");
  if (modal) modal.classList.remove("show");
}

function openExpertPreferenceModal(message) {
  var modal = document.getElementById("expertPreferenceModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "expertPreferenceModal";
    modal.className = "expert-preference-modal";
    modal.onclick = function(e) { if (e.target === modal) closeExpertPreferenceModal(); };
    document.body.appendChild(modal);
  }
  modal.innerHTML =
    '<div class="expert-preference-card" role="dialog" aria-modal="true">' +
      '<button class="profile-close" onclick="closeExpertPreferenceModal()" aria-label="关闭">&times;</button>' +
      '<div class="expert-preference-head">' +
        '<span class="tag tag-blue">PARS资源适配</span>' +
        '<h3>是否需要专家号？</h3>' +
        '<p>系统会先判断病情等级，再结合你的专家号意图推荐普通门诊、专科门诊或专家号。</p>' +
      '</div>' +
      (message ? '<div class="expert-preference-warning">' + esc(message) + '</div>' : '') +
      '<div class="expert-preference-options">' +
        buildExpertPreferenceButton("system", "系统判断", "由系统按病情轻重和资源适配自动决定。") +
        buildExpertPreferenceButton("no_expert", "不需要专家号", "普通病症优先距离、可及性和普通门诊资源。") +
        buildExpertPreferenceButton("wish_expert", "希望专家号", "适度提高专家号权重，但普通病不优先占用顶级专家资源。") +
        buildExpertPreferenceButton("must_expert", "必须专家号", "尊重选择，但普通病会提示资源节约建议。") +
        buildExpertPreferenceButton("named_followup", "指定专家复诊", "适合已有诊疗关系或复诊需求。") +
      '</div>' +
    '</div>';
  modal.classList.add("show");
}

function buildExpertPreferenceButton(value, title, desc) {
  return '<button type="button" class="expert-preference-option" onclick="chooseExpertPreference(\'' + value + '\')">' +
    '<strong>' + esc(title) + '</strong><span>' + esc(desc) + '</span>' +
  '</button>';
}

function chooseExpertPreference(preference) {
  if (preference !== "must_expert") {
    finalizeExpertPreference(preference);
    return;
  }
  var condEl = $("#recCondition");
  var condition = condEl ? condEl.value.trim() : "";
  var scenario = getSelectedScenario();
  var districtEl = $("#recDistrict");
  var district = districtEl ? districtEl.value : "天宁区";
  var patientProfile = collectPatientProfile();
  var enrichedCondition = buildConditionWithPatientProfile(condition, patientProfile, district);
  fetch(API + "/triage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ condition: enrichedCondition, scenario: scenario })
  }).then(function(res) { return res.json(); }).then(function(json) {
    var triage = json && json.data ? json.data.triage : null;
    if (triage && triage.level === "routine") {
      showMustExpertConfirm();
    } else {
      finalizeExpertPreference(preference);
    }
  }).catch(function() {
    showMustExpertConfirm();
  });
}

function showMustExpertConfirm() {
  var modal = document.getElementById("expertPreferenceModal");
  if (!modal) return;
  modal.innerHTML =
    '<div class="expert-preference-card expert-preference-confirm" role="dialog" aria-modal="true">' +
      '<button class="profile-close" onclick="closeExpertPreferenceModal()" aria-label="关闭">&times;</button>' +
      '<div class="expert-preference-head">' +
        '<span class="tag tag-orange">资源节约提示</span>' +
        '<h3>当前病情倾向普通病症</h3>' +
        '<p>不建议优先占用顶级专家资源。你仍可继续按专家号优先推荐，系统会尊重选择并保留资源适配说明。</p>' +
      '</div>' +
      '<div class="expert-preference-actions">' +
        '<button class="btn btn-outline" onclick="finalizeExpertPreference(\'system\')">返回普通推荐</button>' +
        '<button class="btn btn-primary" onclick="finalizeExpertPreference(\'must_expert\')">仍然推荐专家号</button>' +
      '</div>' +
    '</div>';
}

function finalizeExpertPreference(preference) {
  closeExpertPreferenceModal();
  executeRecommend(preference || "system");
}

function executeRecommend(expertPreference) {
  expertPreference = expertPreference || "system";
  var condEl = $("#recCondition");
  if (!condEl) return;
  var condition = condEl.value.trim();
  if (!condition) { toast("请输入病情或症状描述"); return; }
  var scenario = getSelectedScenario();
  var districtEl = $("#recDistrict");
  var district = districtEl ? districtEl.value : "天宁区";
  var patientProfile = collectPatientProfile();
  var enrichedCondition = buildConditionWithPatientProfile(condition, patientProfile, district);
  var resultsDiv = $("#recResults");
  if (!resultsDiv) return;
  updateRecommendLiveViz();
  resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在分析推荐...</p></div>';

  var payload = { condition: enrichedCondition, scenario: scenario, district: district, patient_profile: patientProfile, expert_preference: expertPreference };
  if (window._autoLocation) {
    payload.lat = window._autoLocation.lat;
    payload.lng = window._autoLocation.lng;
    payload.district = window._autoLocation.district || district;
    payload.condition = buildConditionWithPatientProfile(condition, patientProfile, payload.district);
  }

  fetch(API + "/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(function(res) { return res.json(); }).then(function(json) {
    if (json.code !== 200) { resultsDiv.innerHTML = '<div class="empty-state"><p>' + esc(json.message) + '</p></div>'; return; }
    var data = json.data;
    var effectiveScenario = data.effective_scenario || scenario;
    updateRecommendLiveViz(data);
    var html = buildEmergencyPriorityPanel(data);
    html += buildTriageBanner(data.triage);
    html += buildResourceStrategyPanel(data);
    html += buildRadarVisual(data.condition || condition);
    if (data.matched_department) {
      html += '<div style="margin-bottom:16px;font-size:14px;">匹配科室：<span class="tag tag-blue" style="font-size:13px;">' + esc(data.matched_department) + '</span><span style="margin-left:8px;font-size:11px;color:var(--text-secondary);">场景: ' + esc(SCENARIO_LABELS[effectiveScenario] || effectiveScenario) + '</span>' + (data.data_source === "real" ? '<span class="tag tag-green" style="margin-left:4px;">真实数据</span>' : "") + '</div>';
    }
    html += '<h4 style="margin-bottom:12px;">推荐医生 (' + data.recommended_doctors.length + '位) · 动态权重</h4>';
    if (data.recommended_doctors.length === 0) {
      html += '<div class="empty-state" style="padding:20px;"><p>暂未找到匹配的医生</p></div>';
    } else {
      html += '<div class="doctor-grid doctor-grid-recommend">' + buildDoctorCards(data.recommended_doctors) + '</div>';
      html += '<div id="rerankToolbar" style="display:none;align-items:center;gap:10px;padding:10px 14px;margin-top:16px;background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;font-size:13px;">' +
        '<span id="rerankCount" style="font-weight:600;color:#92400e;">已优推 0 位医生</span>' +
        '<button id="rerankBtn" class="btn btn-sm" onclick="rerankByDistance()" style="background:#f59e0b;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-weight:600;">按距离重排优推医生</button>' +
        '</div>' +
        '<div id="rerankResults"></div>';
    }
    html += '<h4 style="margin:24px 0 12px;">推荐医院 (' + data.recommended_hospitals.length + ')</h4>';
    if (data.recommended_hospitals.length === 0) {
      html += '<div class="empty-state" style="padding:20px;"><p>暂未找到匹配的医院</p></div>';
    } else {
      html += buildHospitalCards(data.recommended_hospitals);
    }
    window._lastRecommendResultHtml = html;
    resultsDiv.innerHTML = buildRecommendSummaryPanel(data, data.condition || enrichedCondition);
    saveRecommendRecord(makeRecommendRecord(data, data.condition || enrichedCondition, "手动推荐"));
    openRecommendResultModal("智能推荐结果", html);
  }).catch(function() {
    resultsDiv.innerHTML = '<div class="empty-state"><p>请求失败，请稍后重试</p></div>';
  });
}

// ========== 医生卡片构建 ==========
function buildDoctorCards(doctors) {
  if (!doctors || doctors.length === 0) return "";
  doctors = sortDoctorItemsPhotoFirst(doctors);
  var html = "";
  var rankLabels = ["gold", "silver", "bronze"];
  doctors.forEach(function(item, i) {
    var d = item.doctor;
    cacheDoctor(d);
    var rk = i < 3 ? rankLabels[i] : "";
    var scNote = d.surgery_count_note || (d.surgery_count ? d.surgery_count + "例" : "暂无数据");
    var papers = d.sci_papers ? "SCI " + d.sci_papers + "篇" : (d.total_papers ? "论文" + d.total_papers + "篇" : "");
    var fund = d.national_funding ? " · 国自然" : "";
    var patent = d.patents ? " · 专利" + d.patents + "项" : "";
    var acadParts = [papers, fund, patent].filter(function(v) { return v; });
    var acad = acadParts.length ? acadParts.join(" · ") : "";
    var kws = (d.keywords || d.specialties || []).slice(0, 10).map(function(k) { return '<span class="float-tag">' + esc(k) + '</span>'; }).join("");
    var pathBadge = item.visit_path ? '<span class="dc-path-badge">' + esc(item.visit_path) + '</span>' : "";
    html += '<div class="doctor-card-enhanced doctor-card-clickable doctor-grid-card" onclick="openDoctorProfile(' + d.id + ')" tabindex="0" role="button">' +
      '<div class="dc-rank"><span class="rank-badge ' + rk + '">' + (i + 1) + '</span></div>' +
      '<div class="dc-avatar">' + doctorAvatarHtml(d) + '</div>' +
      '<div class="dc-info">' +
        '<div class="dc-header">' +
          '<span class="dc-name">' + esc(d.name) + '</span>' +
          '<span class="dc-title">' + esc(d.title + " " + (d.academic_title || "")) + '</span>' +
          pathBadge +
          (d.position ? '<span class="tag tag-blue" style="font-size:10px;">' + esc(d.position) + '</span>' : "") +
          '<button class="btn btn-sm star-toggle' + (starredDoctors[d.id] ? ' starred' : '') + '" data-doctor-id="' + d.id + '" onclick="event.stopPropagation();toggleStar(' + d.id + ',\'' + esc(d.name).replace(/'/g, "\\'") + '\')" style="margin-left:auto;flex-shrink:0;font-size:11px;padding:3px 8px;">' + uiIcon("star", "icon-inline") + (starredDoctors[d.id] ? '已优推' : '优推') + '</button>' +
        '</div>' +
        '<div class="dc-dept">' + esc(d.hospital_name + " · " + (d._department_group || normalizeDepartmentName(d.department))) + '</div>' +
        '<div class="dc-keywords">' + kws + '</div>' +
        '<div class="dc-stats">' +
          (scNote !== "暂无数据" ? '<span class="dc-stat-item">' + uiIcon("surgery", "icon-inline") + esc(scNote) + '</span>' : "") +
          (acad ? '<span class="dc-stat-item">' + uiIcon("doc", "icon-inline") + esc(acad) + '</span>' : "") +
          (d.education ? '<span class="dc-stat-item">' + uiIcon("cap", "icon-inline") + esc(d.education) + '</span>' : "") +
        '</div>' +
        (d.achievements && d.achievements.length ? '<div class="dc-achievements">' + uiIcon("award", "icon-inline") + esc(d.achievements.slice(0, 3).join(" · ")) + '</div>' : "") +
        '<div class="dc-score-bar"><div class="dc-score-fill" style="width:' + Math.min(100, item.match_score * 100) + '%;"></div><span class="dc-score-text">匹配度: ' + (item.match_score * 100).toFixed(1) + '</span></div>' +
      '</div>' +
    '</div>';
  });
  return html;
}

// ========== 距离重排 ==========
function updateRerankToolbar() {
  var tb = document.getElementById("rerankToolbar");
  if (!tb) return;
  var ids = getStarredIds();
  if (ids.length === 0) {
    tb.style.display = "none";
    return;
  }
  tb.style.display = "flex";
  var countEl = document.getElementById("rerankCount");
  if (countEl) countEl.textContent = "已优推 " + ids.length + " 位医生";
}

function rerankByDistance() {
  var ids = getStarredIds();
  if (ids.length === 0) { toast("请先点击优推选择医生"); return; }
  var districtEl = document.getElementById("recDistrict");
  var district = districtEl ? districtEl.value : (window._savedDistrict || "天宁区");

  var btn = document.getElementById("rerankBtn");
  if (btn) { btn.disabled = true; btn.textContent = "重排中..."; }

  var payload = { doctor_ids: ids, district: district };
  if (window._autoLocation) {
    payload.lat = window._autoLocation.lat;
    payload.lng = window._autoLocation.lng;
    payload.district = window._autoLocation.district || district;
  }

  fetch(API + "/recommend/rerank", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(function(res) { return res.json(); }).then(function(json) {
    if (btn) { btn.disabled = false; btn.textContent = "按距离重排优推医生"; }
    if (json.code !== 200) { toast(json.message); return; }
    var data = json.data;
    var ranked = data.ranked_doctors;
    if (ranked.length === 0) { toast("未找到匹配的医生"); return; }

    var html = '<div style="margin-bottom:12px;padding:10px 14px;background:#fef3c7;border-radius:8px;font-size:13px;">' +
      '<b>按距离重排结果</b> · 参考位置：' + esc(data.user_district) + ' · 共 ' + ranked.length + ' 位' +
      '</div><div class="doctor-grid doctor-grid-recommend">';

    ranked.forEach(function(item, i) {
      var d = item.doctor;
      var h = item.hospital;
      cacheDoctor(d, h);
      var dist = item.distance_km;
      var rk = i === 0 ? "gold" : (i === 1 ? "silver" : (i === 2 ? "bronze" : ""));
      var scNote = d.surgery_count_note || (d.surgery_count ? d.surgery_count + "例" : "");
      var papers = d.sci_papers ? "SCI " + d.sci_papers + "篇" : (d.total_papers ? "论文" + d.total_papers + "篇" : "");
      var fund = d.national_funding ? " · 国自然" : "";
      var patent = d.patents ? " · 专利" + d.patents + "项" : "";
      var acadParts = [papers, fund, patent].filter(function(v) { return v; });
      var acad = acadParts.length ? acadParts.join(" · ") : "";
      var kws = (d.keywords || d.specialties || []).slice(0, 8).map(function(k) { return '<span class="float-tag">' + esc(k) + '</span>'; }).join("");

      html += '<div class="doctor-card-enhanced doctor-card-clickable doctor-grid-card" onclick="openDoctorProfile(' + d.id + ')" tabindex="0" role="button" style="border-left:3px solid ' + (i === 0 ? '#22c55e' : '#3b82f6') + ';">' +
        '<div class="dc-rank"><span class="rank-badge ' + rk + '">' + (i + 1) + '</span></div>' +
        '<div class="dc-avatar">' + doctorAvatarHtml(d) + '</div>' +
        '<div class="dc-info">' +
          '<div class="dc-header">' +
            '<span class="dc-name">' + esc(d.name) + '</span>' +
            '<span class="dc-title">' + esc(d.title + " " + (d.academic_title || "")) + '</span>' +
            (d.position ? '<span class="tag tag-blue" style="font-size:10px;">' + esc(d.position) + '</span>' : "") +
          '</div>' +
          '<div class="dc-dept">' + esc(h.name + " · " + (d._department_group || normalizeDepartmentName(d.department))) + ' <span style="color:var(--primary);font-weight:600;">距离 ' + dist + 'km</span></div>' +
          '<div class="dc-keywords">' + kws + '</div>' +
          '<div class="dc-stats">' +
            (scNote ? '<span class="dc-stat-item">' + uiIcon("surgery", "icon-inline") + esc(scNote) + '</span>' : "") +
            (acad ? '<span class="dc-stat-item">' + uiIcon("doc", "icon-inline") + esc(acad) + '</span>' : "") +
          '</div>' +
        '</div>' +
      '</div>';
    });
    html += '</div>';

    window._lastRecommendResultHtml = html;
    openRecommendResultModal("优推医生距离重排", html);
  }).catch(function() {
    if (btn) { btn.disabled = false; btn.textContent = "按距离重排优推医生"; }
    toast("请求失败，请稍后重试");
  });
}

// ========== 医院卡片构建 ==========
function buildHospitalCards(hospitals) {
  if (!hospitals || hospitals.length === 0) return "";
  var html = "";
  var rankLabels = ["gold", "silver", "bronze"];
  hospitals.forEach(function(item, i) {
    var h = cacheHospital(item.hospital);
    var rk = i < 3 ? rankLabels[i] : "";
    var explanations = item.explanations || [];
    var traffic = item.traffic_access || {};
    var trafficSummary = traffic.used_in_ranking === false ? "" : (traffic.summary || "");
    html += '<div class="result-card rank-' + (i + 1) + '" onclick="navigate(\'hospital-detail\', {hid:' + h.id + '})" style="cursor:pointer;">' +
      '<div class="result-header">' +
        '<div class="result-hospital-title"><span class="rank-badge ' + rk + '">' + (i + 1) + '</span><span class="result-hospital-logo ' + hospitalIconType(h) + '">' + hospitalLogoHtml(h, "result-logo") + '</span><span class="result-name">' + esc(h.name) + '</span><span class="tag tag-blue" style="margin-left:6px;">' + esc(h.level) + '</span></div>' +
        '<div style="text-align:right;"><div class="highlight-num">' + item.composite_score + '</div><div style="font-size:11px;color:var(--text-secondary);">推荐指数</div></div>' +
      '</div>' +
      '<div class="result-meta">' +
        '<span>距离 ' + item.distance + 'km</span><span>' + esc(h.type) + '</span>' +
        '<span>' + (item.matched_department || "") + ': ' + item.strength_score + '分</span>' +
        (h.emergency ? '<span style="color:#ef4444;">急诊</span>' : "") +
      '</div>' +
      (explanations.length ? '<div class="result-meta" style="margin-top:8px;">' + explanations.map(function(r) { return '<span>' + esc(r) + '</span>'; }).join("") + '</div>' : '') +
      (trafficSummary ? '<div class="traffic-access-line"><strong>交通融合</strong><span>' + esc(trafficSummary) + '</span></div>' : '') +
      '<div class="hospital-card-actions">' +
        '<button class="btn btn-primary btn-sm" onclick="event.stopPropagation();openHospitalNavigation(' + h.id + ')">立即导航</button>' +
        '<button class="btn btn-outline btn-sm" onclick="event.stopPropagation();navigate(\'hospital-detail\',{hid:' + h.id + '})">查看详情</button>' +
      '</div>' +
      '<div class="score-bar"><div class="score-bar-fill" style="width:' + item.composite_score + '%;"></div></div>' +
    '</div>';
  });
  return html;
}

// ========== 简单医生卡片 ==========
function buildSimpleDoctorCard(d) {
  var scNote = d.surgery_count_note || (d.surgery_count ? d.surgery_count + "例" : "");
  var papers = d.sci_papers ? "SCI " + d.sci_papers + "篇" : (d.total_papers ? "论文" + d.total_papers + "篇" : "");
  var fund = d.national_funding ? "国自然" : "";
  var patent = d.patents ? "专利" + d.patents + "项" : "";
  var acadParts = [papers, fund, patent].filter(function(v) { return v; });
  var acad = acadParts.length ? acadParts.join(" · ") : "";
  var kws = (d.keywords || d.specialties || []).slice(0, 8).map(function(k) { return '<span class="float-tag">' + esc(k) + '</span>'; }).join("");
  cacheDoctor(d);
  return '<div class="doctor-card-enhanced doctor-card-clickable doctor-grid-card" onclick="openDoctorProfile(' + d.id + ')" tabindex="0" role="button">' +
    '<div class="dc-avatar">' + doctorAvatarHtml(d) + '</div>' +
    '<div class="dc-info">' +
      '<div class="dc-header">' +
        '<span class="dc-name">' + esc(d.name) + '</span>' +
        '<span class="dc-title">' + esc(d.title + " " + (d.academic_title || "")) + '</span>' +
        (d.position ? '<span class="tag tag-blue" style="font-size:10px;">' + esc(d.position) + '</span>' : "") +
        '<button class="btn btn-sm star-toggle' + (starredDoctors[d.id] ? ' starred' : '') + '" data-doctor-id="' + d.id + '" onclick="event.stopPropagation();toggleStar(' + d.id + ',\'' + esc(d.name).replace(/'/g, "\\'") + '\')" style="margin-left:auto;flex-shrink:0;font-size:11px;padding:3px 8px;">' + uiIcon("star", "icon-inline") + (starredDoctors[d.id] ? '已优推' : '优推') + '</button>' +
      '</div>' +
      '<div class="dc-dept">' + esc(getDoctorHospitalName(d) + " · " + (d._department_group || normalizeDepartmentName(d.department))) + '</div>' +
      '<div class="dc-keywords">' + kws + '</div>' +
      '<div class="dc-stats">' +
        (scNote ? '<span class="dc-stat-item">' + uiIcon("surgery", "icon-inline") + esc(scNote) + '</span>' : "") +
        (acad ? '<span class="dc-stat-item">' + uiIcon("doc", "icon-inline") + esc(acad) + '</span>' : "") +
      '</div>' +
      (d.achievements && d.achievements.length ? '<div class="dc-achievements">' + uiIcon("award", "icon-inline") + esc(d.achievements.slice(0, 3).join(" · ")) + '</div>' : "") +
    '</div>' +
  '</div>';
}

// ========== 医院列表 ==========
function renderHospitals() {
  $("#mainContent").innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  fetch(API + "/hospitals").then(function(res) { return res.json(); }).then(function(json) {
    var hospitals = json.data;
    window._hospitals = hospitals;
    var levelSeen = {};
    var typeSeen = {};
    var levels = [];
    var types = [];
    for (var i = 0; i < hospitals.length; i++) {
      if (hospitals[i].level && !levelSeen[hospitals[i].level]) {
        levelSeen[hospitals[i].level] = true;
        levels.push(hospitals[i].level);
      }
      if (hospitals[i].type && !typeSeen[hospitals[i].type]) {
        typeSeen[hospitals[i].type] = true;
        types.push(hospitals[i].type);
      }
    }
    var deptOpts = '<option value="">全部等级</option>' + levels.map(function(v) { return '<option value="' + esc(v) + '">' + esc(v) + '</option>'; }).join("");
    var typeOpts = '<option value="">全部类型</option>' + types.map(function(v) { return '<option value="' + esc(v) + '">' + esc(v) + '</option>'; }).join("");
    $("#mainContent").innerHTML =
      '<h2 class="page-title">医院列表</h2>' +
      '<p class="page-subtitle">常州市 ' + hospitals.length + ' 家医院</p>' +
      '<div class="list-viz-grid">' +
        '<div class="card viz-card"><div class="card-title">医院等级分布</div>' + buildPieChart(countByValue(hospitals, "level")) + '</div>' +
        '<div class="card viz-card"><div class="card-title">分区床位分布</div>' + buildHorizontalBarChart(sumByGroup(hospitals, getHospitalDistrict, function(h) { return h.beds; }), "") + '</div>' +
      '</div>' +
      '<div class="form-row" style="margin-bottom:16px;">' +
        '<div class="form-group"><select class="form-select" id="hospFilterLevel" onchange="filterHospitals()">' + deptOpts + '</select></div>' +
        '<div class="form-group"><select class="form-select" id="hospFilterType" onchange="filterHospitals()">' + typeOpts + '</select></div>' +
      '</div>' +
      '<div class="table-wrap card" style="padding:0;"><table><thead><tr><th>排名</th><th>医院名称</th><th>等级</th><th>类型</th><th>床位数</th><th>重点专科</th><th>操作</th></tr></thead><tbody id="hospTableBody"></tbody></table></div>';
    renderHospitalTable(hospitals);
  });
}

function renderHospitalTable(list) {
  var tbody = $("#hospTableBody");
  if (!tbody) return;
  var rankLabels = ["gold", "silver", "bronze"];
  var rows = [];
  for (var i = 0; i < list.length; i++) {
    var h = cacheHospital(list[i]);
    var rk = i < 3 ? rankLabels[i] : "";
    var strengths = (h.strengths || []).slice(0, 3).map(function(s) { return '<span class="float-tag">' + esc(s) + '</span>'; }).join("");
    rows.push('<tr>' +
      '<td><span class="rank-badge ' + rk + '" style="' + (i >= 3 ? 'background:#94a3b8' : '') + '">' + (i + 1) + '</span></td>' +
      '<td><div class="hospital-table-name"><span class="hospital-table-logo ' + hospitalIconType(h) + '">' + hospitalLogoHtml(h, "table-logo") + '<span class="hospital-logo-initial">' + esc(hospitalIconInitial(h.name)) + '</span></span><div><strong>' + esc(h.name) + '</strong><br><small style="color:var(--text-secondary);">' + esc(h.address) + '</small></div></div></td>' +
      '<td><span class="tag ' + (h.level === "三级甲等" ? "tag-red" : "tag-orange") + '">' + esc(h.level) + '</span></td>' +
      '<td>' + esc(h.type) + '</td>' +
      '<td>' + h.beds + '</td>' +
      '<td>' + strengths + '</td>' +
      '<td><div class="hospital-table-actions"><button class="btn btn-primary btn-sm" onclick="openHospitalNavigation(' + h.id + ')">立即导航</button><button class="btn btn-outline btn-sm" onclick="navigate(\'hospital-detail\',{hid:' + h.id + '})">查看详情</button></div></td>' +
      '</tr>');
  }
  tbody.innerHTML = rows.join("");
}

function filterHospitals() {
  var levelEl = $("#hospFilterLevel");
  var typeEl = $("#hospFilterType");
  var level = levelEl ? levelEl.value : "";
  var type = typeEl ? typeEl.value : "";
  var list = window._hospitals || [];
  if (level) { list = []; for (var i = 0; i < (window._hospitals || []).length; i++) { if (window._hospitals[i].level === level) list.push(window._hospitals[i]); } }
  if (type) { var filtered = []; for (var j = 0; j < list.length; j++) { if (list[j].type === type) filtered.push(list[j]); } list = filtered; }
  renderHospitalTable(list);
}

// ========== 医院详情全屏页 ==========
function renderHospitalDetailPage(params) {
  var hid = params ? params.hid : (window._hospitalDetailParams ? window._hospitalDetailParams.hid : null);
  if (!hid) { navigate("hospitals"); return; }
  var main = $("#mainContent");
  main.innerHTML = '<div class="loading"><div class="spinner"></div><p>加载医院详情...</p></div>';

  var p1 = fetch(API + "/hospitals/" + hid).then(function(r) { return r.json(); });
  var p2 = fetch(API + "/hospitals/" + hid + "/doctors").then(function(r) { return r.json(); });
  Promise.all([p1, p2]).then(function(results) {
    var hJson = results[0], dJson = results[1];
    if (hJson.code !== 200) { main.innerHTML = '<div class="empty-state"><p>加载失败</p></div>'; return; }
    var h = cacheHospital(hJson.data.hospital);
    setAssistantContext("hospital", h);
    var doctors = dJson.data.doctors || [];
    var dSource = dJson.data.source || "mock";
    for (var di = 0; di < doctors.length; di++) {
      doctors[di]._hospital_name = h.name;
      doctors[di]._hospital_level = h.level;
      doctors[di]._hospital_type = h.type;
      doctors[di]._hospital_address = h.address;
      doctors[di]._department_group = normalizeDepartmentName(doctors[di].department);
      cacheDoctor(doctors[di], h);
    }
    window._hospitalDetailDoctors = doctors;
    window._hospitalDetailHospital = h;

    var strengthsHtml = (h.strengths || []).map(function(s) {
      var score = (h.strength_scores || {})[s] || 0;
      return '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">' +
        '<span style="width:120px;font-size:13px;">' + esc(s) + '</span>' +
        '<div class="score-bar" style="flex:1;"><div class="score-bar-fill" style="width:' + score + '%;"></div></div>' +
        '<span style="font-size:12px;color:var(--text-secondary);min-width:30px;">' + score + '</span>' +
        '</div>';
    }).join("");

    var deptTags = (h.departments || []).map(function(d) { return '<span class="float-tag">' + esc(d) + '</span>'; }).join(" ");
    var strengthCounts = h.strength_scores || {};
    var deptFamilyCounts = {};
    (h.departments || []).forEach(function(d) {
      var group = "其他";
      if (d.indexOf("内") >= 0 || d.indexOf("心") >= 0 || d.indexOf("呼吸") >= 0 || d.indexOf("消化") >= 0 || d.indexOf("神经") >= 0) group = "内科系统";
      else if (d.indexOf("外") >= 0 || d.indexOf("骨") >= 0 || d.indexOf("泌尿") >= 0 || d.indexOf("肝胆") >= 0) group = "外科系统";
      else if (d.indexOf("妇") >= 0 || d.indexOf("产") >= 0 || d.indexOf("儿") >= 0 || d.indexOf("新生儿") >= 0) group = "妇儿系统";
      else if (d.indexOf("中医") >= 0 || d.indexOf("针灸") >= 0 || d.indexOf("康复") >= 0) group = "中医康复";
      deptFamilyCounts[group] = (deptFamilyCounts[group] || 0) + 1;
    });
    var capacityCounts = { "床位": h.beds || 0, "日均门诊": h.daily_outpatients || 0, "科室数": (h.departments || []).length * 100 };

    var hospDeptOpts = buildDoctorOptionSet(doctors, function(d) { return d._department_group || normalizeDepartmentName(d.department); }, "全部科室");
    var docCards = buildHospitalDoctorGrid(doctors);

    main.innerHTML =
      '<div class="detail-page">' +
        '<div class="detail-breadcrumb"><a onclick="navigate(\'hospitals\')" style="cursor:pointer;color:var(--primary);">← 返回医院列表</a></div>' +
        '<div class="detail-header hospital-detail-header">' +
          '<div class="hospital-detail-logo ' + hospitalIconType(h) + '">' +
            hospitalLogoHtml(h, "detail-logo") +
            '<span class="hospital-logo-initial">' + esc(hospitalIconInitial(h.name)) + '</span>' +
          '</div>' +
          '<div class="hospital-detail-heading">' +
            '<h2 class="page-title">' + esc(h.name) + '</h2>' +
            '<div class="hospital-detail-tags">' +
              '<span class="tag tag-blue">' + esc(h.level) + '</span>' +
              '<span class="tag tag-green">' + esc(h.type) + '</span>' +
              (h.emergency ? '<span class="tag tag-red">急诊</span>' : "") +
            '</div>' +
            '<button class="btn btn-primary btn-sm hospital-detail-nav-btn" onclick="openHospitalNavigation(' + h.id + ')">立即导航</button>' +
          '</div>' +
        '</div>' +
        '<div class="detail-grid">' +
          '<div class="card"><div class="card-title">基本信息</div>' +
            '<div class="detail-info-grid">' +
              '<div><strong>地址：</strong>' + esc(h.address) + '</div>' +
              '<div><strong>电话：</strong>' + esc(h.phone) + '</div>' +
              '<div><strong>床位数：</strong>' + h.beds + ' 张</div>' +
              '<div><strong>日均门诊：</strong>' + h.daily_outpatients + ' 人次</div>' +
              '<div><strong>科室数：</strong>' + (h.departments || []).length + ' 个</div>' +
            '</div>' +
            '<p style="margin-top:12px;color:var(--text-secondary);">' + esc(h.description || "") + '</p>' +
          '</div>' +
          '<div class="card"><div class="card-title">重点专科实力</div>' + strengthsHtml + '</div>' +
        '</div>' +
        '<div class="hospital-detail-viz">' +
          '<div class="card"><div class="card-title">重点专科实力横向图</div>' + buildHorizontalBarChart(strengthCounts, "分") + '</div>' +
          '<div class="card"><div class="card-title">科室系统构成</div>' + buildHorizontalBarChart(deptFamilyCounts, "个") + '</div>' +
          '<div class="card"><div class="card-title">服务能力指数</div>' + buildHorizontalBarChart(capacityCounts, "") + '</div>' +
        '</div>' +
        '<div class="card" style="margin-top:20px;"><div class="card-title">全部科室</div><div>' + deptTags + '</div></div>' +
        '<div class="card" style="margin-top:20px;">' +
          '<div class="card-header">' +
            '<span class="card-title">本院专家 (' + doctors.length + '位) ' + (dSource === "real" ? '<span class="tag tag-green" style="font-size:10px;">真实数据</span>' : '<span class="tag tag-orange" style="font-size:10px;">模拟数据</span>') + '</span>' +
            '<span style="font-size:12px;color:var(--text-secondary);">数据来源：公开信息采集</span>' +
          '</div>' +
          (doctors.length === 0 ? '<p style="color:var(--text-secondary);">暂无专家信息</p>' :
            '<div class="hospital-doctor-filter">' +
              '<div class="form-group"><label class="form-label">科室筛选</label><select class="form-select" id="hospitalDocDept" onchange="filterHospitalDoctors()">' + hospDeptOpts + '</select></div>' +
              '<div class="form-group"><label class="form-label">搜索医生</label><input class="form-input" id="hospitalDocSearch" placeholder="搜索姓名、职称或擅长..." oninput="filterHospitalDoctors()"></div>' +
            '</div>' +
            '<div id="hospitalDoctorSummary" class="filter-summary">当前筛选结果：' + doctors.length + ' 位医生</div>' +
            '<div id="hospitalDoctorList">' + docCards + '</div>') +
        '</div>' +
      '</div>';
  }).catch(function() {
    main.innerHTML = '<div class="empty-state"><p>加载失败，请稍后重试</p></div>';
  });
}

function buildHospitalDoctorGrid(doctors) {
  if (!doctors || doctors.length === 0) return '<div class="empty-state"><p>未找到匹配的医生</p></div>';
  doctors = sortDoctorsPhotoFirst(doctors);
  var html = "";
  for (var i = 0; i < doctors.length; i++) html += buildSimpleDoctorCard(doctors[i]);
  return '<div class="doctor-grid">' + html + '</div>';
}

function filterHospitalDoctors() {
  var deptEl = $("#hospitalDocDept");
  var searchEl = $("#hospitalDocSearch");
  var dept = deptEl ? deptEl.value : "";
  var search = (searchEl ? (searchEl.value || "") : "").toLowerCase();
  var list = window._hospitalDetailDoctors || [];
  if (dept) {
    var deptFiltered = [];
    for (var i = 0; i < list.length; i++) {
      if ((list[i]._department_group || normalizeDepartmentName(list[i].department)) === dept) deptFiltered.push(list[i]);
    }
    list = deptFiltered;
  }
  if (search) {
    var searchFiltered = [];
    for (var j = 0; j < list.length; j++) {
      var d = list[j];
      var haystack = [d.name, d.title, d.academic_title, d.department, d._department_group].join(" ").toLowerCase();
      var matched = haystack.indexOf(search) >= 0;
      var kws = d.keywords || d.specialties || [];
      for (var k = 0; !matched && k < kws.length; k++) {
        if (String(kws[k]).toLowerCase().indexOf(search) >= 0) matched = true;
      }
      if (matched) searchFiltered.push(d);
    }
    list = searchFiltered;
  }
  var summary = $("#hospitalDoctorSummary");
  if (summary) summary.textContent = "当前筛选结果：" + list.length + " 位医生";
  var container = $("#hospitalDoctorList");
  if (container) container.innerHTML = buildHospitalDoctorGrid(list);
}

// ========== 医生列表 ==========
function renderDoctors() {
  $("#mainContent").innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  Promise.all([
    fetch(API + "/doctors").then(function(res) { return res.json(); }),
    fetch(API + "/hospitals").then(function(res) { return res.json(); })
  ]).then(function(results) {
    var doctors = results[0].data || [];
    var hospitals = results[1].data || [];
    var hospitalMap = {};
    for (var i = 0; i < hospitals.length; i++) hospitalMap[hospitals[i].id] = hospitals[i];
    for (var j = 0; j < doctors.length; j++) {
      var h = hospitalMap[doctors[j].hospital_id];
      doctors[j]._hospital_name = h ? h.name : (doctors[j].hospital_name || "未知医院");
      doctors[j]._hospital_level = h ? h.level : "未分级";
      doctors[j]._hospital_type = h ? h.type : "";
      doctors[j]._hospital_address = h ? h.address : "";
      doctors[j]._department_group = normalizeDepartmentName(doctors[j].department);
      cacheDoctor(doctors[j], h);
    }
    window._doctors = doctors;
    window._hospitalsById = hospitalMap;

    var levelOpts = buildDoctorOptionSet(doctors, function(d) { return d._hospital_level; }, "全部医院层级");
    var hospitalOpts = buildDoctorHospitalOptions(doctors, "");
    var deptOpts = buildDoctorOptionSet(doctors, function(d) { return d._department_group || normalizeDepartmentName(d.department); }, "全部科室");
    var titleOpts = buildDoctorOptionSet(doctors, function(d) { return d.title; }, "全部职称");

    $("#mainContent").innerHTML =
      '<h2 class="page-title">医生列表</h2>' +
      '<p class="page-subtitle">在册专家 ' + doctors.length + ' 位 · 支持按医院层级、医院、科室和职称逐层筛选</p>' +
      '<div class="list-viz-grid">' +
        '<div class="card viz-card"><div class="card-title">医生职称结构</div>' + buildPieChart(buildDoctorTypeCounts(doctors)) + '</div>' +
        '<div class="card viz-card"><div class="card-title">热门科室医生分布</div>' + buildHorizontalBarChart(countByValue(doctors.slice(0, 260), function(d) { return d._department_group || normalizeDepartmentName(d.department); }), "位") + '</div>' +
      '</div>' +
      '<div class="doctor-filter-panel">' +
        '<div class="form-group"><label class="form-label">医院层级</label><select class="form-select" id="docFilterLevel" onchange="filterDoctors(true)">' + levelOpts + '</select></div>' +
        '<div class="form-group"><label class="form-label">医院</label><select class="form-select" id="docFilterHospital" onchange="filterDoctors()">' + hospitalOpts + '</select></div>' +
        '<div class="form-group"><select class="form-select" id="docFilterDept" onchange="filterDoctors()">' + deptOpts + '</select></div>' +
        '<div class="form-group"><select class="form-select" id="docFilterTitle" onchange="filterDoctors()">' + titleOpts + '</select></div>' +
        '<div class="form-group doctor-search"><input class="form-input" id="docSearch" placeholder="搜索医生姓名、科室或擅长..." oninput="filterDoctors()"></div>' +
      '</div>' +
      '<div id="docFilterSummary" class="filter-summary"></div>' +
      '<div id="docList"></div>';
    renderDoctorList(doctors);
  }).catch(function() {
    $("#mainContent").innerHTML = '<div class="empty-state"><p>医生数据加载失败，请稍后重试</p></div>';
  });
}

function buildDoctorOptionSet(doctors, getter, label) {
  var counts = {};
  for (var i = 0; i < doctors.length; i++) {
    var value = getter(doctors[i]) || "";
    if (!value) continue;
    counts[value] = (counts[value] || 0) + 1;
  }
  var values = Object.keys(counts).sort(function(a, b) { return a.localeCompare(b, "zh-CN"); });
  var html = '<option value="">' + esc(label) + ' (' + values.length + '项)</option>';
  for (var j = 0; j < values.length; j++) {
    html += '<option value="' + esc(values[j]) + '">' + esc(values[j]) + ' · ' + counts[values[j]] + '位</option>';
  }
  return html;
}

function buildDoctorHospitalOptions(doctors, level) {
  var counts = {};
  var names = {};
  for (var i = 0; i < doctors.length; i++) {
    var d = doctors[i];
    if (level && d._hospital_level !== level) continue;
    var id = String(d.hospital_id || "");
    if (!id) continue;
    counts[id] = (counts[id] || 0) + 1;
    names[id] = d._hospital_name || d.hospital_name || "未知医院";
  }
  var ids = Object.keys(counts).sort(function(a, b) { return names[a].localeCompare(names[b], "zh-CN"); });
  var html = '<option value="">全部医院 (' + ids.length + '家)</option>';
  for (var j = 0; j < ids.length; j++) {
    html += '<option value="' + esc(ids[j]) + '">' + esc(names[ids[j]]) + ' · ' + counts[ids[j]] + '位</option>';
  }
  return html;
}

function renderDoctorList(list) {
  var container = $("#docList");
  if (!container) return;
  list = sortDoctorsPhotoFirst(list || []);
  var summary = $("#docFilterSummary");
  if (summary) summary.textContent = "当前筛选结果：" + list.length + " 位医生";
  if (list.length === 0) { container.innerHTML = '<div class="empty-state"><p>未找到匹配的医生</p></div>'; return; }
  var html = "";
  for (var i = 0; i < list.length; i++) { html += buildSimpleDoctorCard(list[i]); }
  container.innerHTML = '<div class="doctor-grid">' + html + '</div>';
}

function filterDoctors(levelChanged) {
  var levelEl = $("#docFilterLevel");
  var hospitalEl = $("#docFilterHospital");
  var deptEl = $("#docFilterDept");
  var titleEl = $("#docFilterTitle");
  var searchEl = $("#docSearch");
  var level = levelEl ? levelEl.value : "";
  if (hospitalEl && levelChanged) {
    var current = hospitalEl.value;
    hospitalEl.innerHTML = buildDoctorHospitalOptions(window._doctors || [], level);
    var hasCurrent = current && Array.prototype.some.call(hospitalEl.options, function(opt) { return opt.value === current; });
    hospitalEl.value = hasCurrent ? current : "";
  }
  var hospitalId = hospitalEl ? hospitalEl.value : "";
  var dept = deptEl ? deptEl.value : "";
  var title = titleEl ? titleEl.value : "";
  var search = (searchEl ? (searchEl.value || "") : "").toLowerCase();
  var list = window._doctors || [];
  if (level) { var levelFiltered = []; for (var a = 0; a < list.length; a++) { if (list[a]._hospital_level === level) levelFiltered.push(list[a]); } list = levelFiltered; }
  if (hospitalId) { var hFiltered = []; for (var b = 0; b < list.length; b++) { if (String(list[b].hospital_id) === hospitalId) hFiltered.push(list[b]); } list = hFiltered; }
  if (dept) { var dFiltered = []; for (var i = 0; i < list.length; i++) { if ((list[i]._department_group || normalizeDepartmentName(list[i].department)) === dept) dFiltered.push(list[i]); } list = dFiltered; }
  if (title) { var titleFiltered = []; for (var t = 0; t < list.length; t++) { if (list[t].title === title) titleFiltered.push(list[t]); } list = titleFiltered; }
  if (search) {
    var sFiltered = [];
    for (var j = 0; j < list.length; j++) {
      var d = list[j];
      var haystack = [d.name, d.department, d._department_group, d.title, d._hospital_name].join(" ").toLowerCase();
      var match = haystack.indexOf(search) >= 0;
      if (!match && (d.keywords || d.specialties || []).length) {
        var kws = d.keywords || d.specialties || [];
        for (var k = 0; k < kws.length; k++) { if (String(kws[k]).toLowerCase().indexOf(search) >= 0) { match = true; break; } }
      }
      if (match) sFiltered.push(d);
    }
    list = sFiltered;
  }
  renderDoctorList(list);
}

// ========== 哈弗辛距离公式 ==========
function haversineKm(lat1, lng1, lat2, lng2) {
  var R = 6371;
  var dLat = (lat2 - lat1) * Math.PI / 180;
  var dLng = (lng2 - lng1) * Math.PI / 180;
  var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ========== 地图视图 ==========
function renderMap() {
  $("#mainContent").innerHTML =
    '<h2 class="page-title">地图视图</h2>' +
    '<p class="page-subtitle">常州市医院分布地图 · 支持定位与图层切换</p>' +
    '<div class="card" style="padding:0;overflow:hidden;">' +
      '<div class="map-toolbar">' +
        '<div class="map-legend">' +
          '<span><i style="background:#ef4444;"></i>三级甲等</span>' +
          '<span><i style="background:#f59e0b;"></i>三级乙等</span>' +
          '<span><i style="background:#3b82f6;"></i>综合医院</span>' +
          '<span><i style="background:#8b5cf6;"></i>专科医院</span>' +
        '</div>' +
        '<button class="btn btn-sm btn-outline" id="mapLocateBtn" onclick="locateUser()" title="定位到我的位置">' + uiIcon("location", "icon-inline") + '我的位置</button>' +
      '</div>' +
      '<div id="mapContainer" class="map-container-enhanced"></div>' +
    '</div>';

  setTimeout(function() { renderMapInto("mapContainer", true); }, 300);
}

function renderMapInto(containerId, enableLocate) {
    var container = document.getElementById(containerId);
    if (!container || typeof L === "undefined") return;
    if (container._leaflet_id) container.innerHTML = "";

    var map = L.map(container, { zoomControl: true }).setView([31.70, 119.80], 12);
    window._leafletMap = map;

    // 高德地图瓦片（中文标注，无需API Key）
    var gaodeTile = L.tileLayer("https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}", {
      subdomains: ["1", "2", "3", "4"],
      maxZoom: 18,
      attribution: "&copy; 高德地图 | 数据来源: 公开信息"
    }).addTo(map);

    // OpenStreetMap 备用图层
    var osmTile = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors"
    });

    // 图层切换控件
    var baseLayers = { "高德地图（中文）": gaodeTile, "OpenStreetMap": osmTile };
    var busStationLayer = L.layerGroup().addTo(map);
    var bikeStationLayer = L.layerGroup().addTo(map);
    var bikeVehicleLayer = L.layerGroup();
    var overlayLayers = {
      "公交站点分布": busStationLayer,
      "共享骑行站点": bikeStationLayer,
      "共享车辆分布": bikeVehicleLayer
    };
    L.control.layers(baseLayers, overlayLayers, { position: "topright", collapsed: true }).addTo(map);
    addTransitMapLegend(map);

    // 用户位置标记层
    var userMarker = null;
    var userCircle = null;
    window._userLatLng = null;
    window._updateUserMarker = function(lat, lng) {
      if (userMarker) { map.removeLayer(userMarker); map.removeLayer(userCircle); }
      userMarker = L.marker([lat, lng], {
        icon: L.divIcon({
          className: "user-location-marker",
          html: '<div class="user-dot"></div><div class="user-pulse"></div>',
          iconSize: [24, 24], iconAnchor: [12, 12]
        })
      }).addTo(map).bindPopup("<b>我的位置</b>").openPopup();
      userCircle = L.circle([lat, lng], { radius: 500, color: "#3b82f6", weight: 1, opacity: 0.3, fillOpacity: 0.1 }).addTo(map);
      window._userLatLng = [lat, lng];
      map.setView([lat, lng], 13);
      updateHospitalDistances();
    };

    // 加载医院数据
    fetch(API + "/hospitals").then(function(res) { return res.json(); }).then(function(json) {
      window._hospitalData = json.data;
      for (var i = 0; i < json.data.length; i++) {
        var h = json.data[i];
        var color = h.level === "三级甲等" ? "#ef4444" : "#f59e0b";
        if (h.type === "专科医院") color = "#8b5cf6";
        var marker = L.marker([h.lat, h.lng], {
          icon: L.divIcon({
            className: "custom-marker",
            html: '<div class="map-name-pin" style="--pin-color:' + color + ';"><span>' + esc(shortHospitalName(h.name)) + '</span></div>',
            iconSize: [112, 34], iconAnchor: [56, 17]
          })
        }).addTo(map);
        marker._hospitalData = h;
        marker.bindPopup(buildMapPopup(h, null));
        marker.on("click", function(e) {
          var popup = e.target.getPopup();
          var hd = e.target._hospitalData;
          var dist = null;
          if (window._userLatLng) {
            dist = haversineKm(window._userLatLng[0], window._userLatLng[1], hd.lat, hd.lng).toFixed(1);
          }
          var ctxHospital = Object.assign({}, hd);
          ctxHospital._distanceText = dist ? "距您约 " + dist + " km" : "已在地图中选中";
          setAssistantContext("map_hospital", ctxHospital);
          popup.setContent(buildMapPopup(hd, dist));
        });
      }
      if (json.data.length) {
        var bounds = L.latLngBounds(json.data.map(function(h) { return [h.lat, h.lng]; }));
        map.fitBounds(bounds, { padding: [30, 30], maxZoom: 12 });
      }
    });

    loadTransitStationLayers(map, busStationLayer, bikeStationLayer, bikeVehicleLayer);
}

function addTransitMapLegend(map) {
  if (!map || typeof L === "undefined" || map._transitLegendAdded) return;
  map._transitLegendAdded = true;
  var legend = L.control({ position: "bottomright" });
  legend.onAdd = function() {
    var div = L.DomUtil.create("div", "map-transit-legend");
    div.innerHTML =
      '<strong>地图图层</strong>' +
      '<span><i class="legend-dot legend-hospital"></i>医院</span>' +
      '<span><i class="legend-transit-icon legend-bus-icon">巴</i>公交站点</span>' +
      '<span><i class="legend-transit-icon legend-bike-icon">骑</i>骑行站点</span>' +
      '<span><i class="legend-transit-icon legend-vehicle-icon">车</i>共享车辆</span>';
    return div;
  };
  legend.addTo(map);
}

function loadTransitStationLayers(map, busLayer, bikeLayer, vehicleLayer) {
  Promise.all([
    fetch(API + "/transit/stations").then(function(res) { return res.json(); }).catch(function() { return { data: [] }; }),
    fetch(API + "/transit/bike-stations").then(function(res) { return res.json(); }).catch(function() { return { data: [] }; }),
    fetch(API + "/transit/bike-vehicles").then(function(res) { return res.json(); }).catch(function() { return { data: [] }; })
  ]).then(function(results) {
    var busStations = results[0].data || [];
    var bikeStations = results[1].data || [];
    var bikeVehicles = results[2].data || [];

    busStations.forEach(function(station) {
      if (station.latitude == null || station.longitude == null) return;
      L.marker([station.latitude, station.longitude], {
        icon: buildTransitStationIcon("bus"),
        riseOnHover: true
      }).bindPopup(
        '<div class="map-popup station-popup">' +
          '<h4>' + esc(station.station_name || "公交站点") + '</h4>' +
          '<p>道路：' + esc(station.road_name || "未标注") + '</p>' +
          '<p>站台形式：' + esc(station.platform_shape || "未知") + '</p>' +
        '</div>'
      ).addTo(busLayer);
    });

    bikeStations.forEach(function(station) {
      if (station.latitude == null || station.longitude == null) return;
      L.marker([station.latitude, station.longitude], {
        icon: buildTransitStationIcon("bike"),
        riseOnHover: true
      }).bindPopup(
        '<div class="map-popup station-popup">' +
          '<h4>' + esc(station.station_name || "共享骑行站点") + '</h4>' +
          '<p>地址：' + esc(station.station_addr || "未标注") + '</p>' +
          '<p>可租车辆：' + (station.bike_num || 0) + ' 辆 · 助力车 ' + (station.e_bike_num || 0) + ' 辆</p>' +
          '<p>锁车桩：' + (station.lock_num || 0) + ' 个</p>' +
        '</div>'
      ).addTo(bikeLayer);
    });

    bikeVehicles.forEach(function(vehicle) {
      if (!vehicleLayer || vehicle.latitude == null || vehicle.longitude == null) return;
      L.marker([vehicle.latitude, vehicle.longitude], {
        icon: buildTransitStationIcon("vehicle"),
        riseOnHover: true
      }).bindPopup(
        '<div class="map-popup station-popup">' +
          '<h4>共享车辆</h4>' +
          '<p>类型：' + esc(vehicle.bike_type || "未知") + '</p>' +
          '<p>状态：' + esc(vehicle.bike_state || "未知") + '</p>' +
          '<p>更新时间：' + esc(vehicle.update_time || "未标注") + '</p>' +
        '</div>'
      ).addTo(vehicleLayer);
    });
  });
}

function buildTransitStationIcon(type) {
  var isBike = type === "bike";
  var isVehicle = type === "vehicle";
  var className = isVehicle ? "transit-station-marker bike-vehicle-marker" : (isBike ? "transit-station-marker bike-station-marker" : "transit-station-marker bus-station-marker");
  var svg = (isBike || isVehicle)
    ? '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="17" r="3.2"></circle><circle cx="18" cy="17" r="3.2"></circle><path d="M8.4 17l3.1-7h3.2l-2.6 7m-.6-7l4.2 7M9.8 12.2h5.7M13.6 8.2h2.8"></path></svg>'
    : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h12c1.2 0 2 .8 2 2v8.2c0 .8-.5 1.4-1.2 1.7"></path><path d="M5.2 16.9c-.7-.3-1.2-.9-1.2-1.7V7c0-1.2.8-2 2-2"></path><path d="M5 10h14M7 7.4h10M7 13h3m4 0h3"></path><circle cx="7.5" cy="18" r="1.7"></circle><circle cx="16.5" cy="18" r="1.7"></circle></svg>';
  return L.divIcon({
    className: className,
    html: '<div class="station-icon-badge">' + svg + '</div>',
    iconSize: isVehicle ? [24, 24] : [30, 30],
    iconAnchor: isVehicle ? [12, 12] : [15, 15],
    popupAnchor: [0, -15]
  });
}

function buildMapPopup(h, distKm) {
  cacheHospital(h);
  var html = '<div class="map-popup">' +
    '<h4 style="margin:0 0 6px;font-size:15px;">' + esc(h.name) + '</h4>' +
    '<span class="tag tag-blue" style="margin-right:4px;">' + esc(h.level) + '</span>' +
    '<span class="tag tag-green">' + esc(h.type) + '</span>';
  if (h.emergency) html += '<span class="tag tag-red" style="margin-left:4px;">急诊</span>';
  html += '<div class="map-popup-info">' +
    '<p>地址：' + esc(h.address) + '</p>' +
    '<p>电话：' + esc(h.phone) + '</p>' +
    '<p>床位：' + h.beds + ' 张 · 日门诊 ' + h.daily_outpatients + ' 人次</p>';
  if (distKm) html += '<p style="color:var(--primary);font-weight:600;">距您约 ' + distKm + ' km</p>';
  html += '</div>' +
    '<div class="map-popup-actions">' +
      '<button class="btn btn-primary btn-sm" onclick="openHospitalNavigation(' + h.id + ')">立即导航</button>' +
      '<button class="btn btn-outline btn-sm" onclick="navigate(\'hospital-detail\',{hid:' + h.id + '})">查看详情</button>' +
    '</div>' +
    '</div>';
  return html;
}

function locateUser() {
  if (!navigator.geolocation) { toast("您的浏览器不支持地理定位"); return; }
  var btn = document.getElementById("mapLocateBtn");
  if (btn) { btn.textContent = "定位中..."; btn.disabled = true; }
  var finished = false;
  function applyMapPos(pos, precise) {
    if (window._updateUserMarker) {
      window._updateUserMarker(pos.coords.latitude, pos.coords.longitude);
    }
    var near = nearestDistrict(pos.coords.latitude, pos.coords.longitude);
    saveAutoLocation({
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
      district: near.name,
      accuracy: Math.round(pos.coords.accuracy || 0)
    });
    if (btn) { btn.innerHTML = uiIcon("location", "icon-inline") + "我的位置"; btn.disabled = false; }
    toast(precise ? "定位已校准" : "定位成功，正在校准");
    finished = true;
  }
  function failMapPos(err) {
    if (finished) return;
    toast("定位失败: " + autoLocationErrorText(err));
    if (btn) { btn.innerHTML = uiIcon("location", "icon-inline") + "我的位置"; btn.disabled = false; }
  }
  navigator.geolocation.getCurrentPosition(function(pos) { applyMapPos(pos, false); }, failMapPos, { enableHighAccuracy: false, timeout: 4500, maximumAge: 600000 });
  navigator.geolocation.getCurrentPosition(function(pos) { applyMapPos(pos, true); }, failMapPos, { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 });
}

function updateHospitalDistances() {
  if (!window._userLatLng || !window._leafletMap) return;
  // 定位后自动缩放至城市级别，方便查看所有医院与自身位置的关系
  var map = window._leafletMap;
  var bounds = L.latLngBounds([window._userLatLng]);
  var hospitals = window._hospitalData || [];
  for (var i = 0; i < hospitals.length; i++) {
    bounds.extend([hospitals[i].lat, hospitals[i].lng]);
  }
  map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
}

// ========== 我的 ==========
function getCurrentUserProfile() {
  return {
    loggedIn: sessionStorage.getItem("medicalAuth") === "1",
    name: sessionStorage.getItem("medicalUser") || "未登录用户",
    role: sessionStorage.getItem("medicalRole") || "普通用户",
    loginAt: sessionStorage.getItem("medicalLoginAt") || "尚未登录"
  };
}

function buildMineRecordCards(records) {
  if (!records || !records.length) {
    return '<div class="mine-empty">暂无推荐记录，去智能推荐完成一次问诊后会自动保存。</div>';
  }
  return records.slice(0, 5).map(function(item, index) {
    return '<button class="mine-record-card" onclick="navigate(\'recommend\');setTimeout(function(){restoreRecommendRecord(' + index + ')},120)">' +
      '<div><strong>' + esc(item.condition || "问诊记录") + '</strong><span>' + esc(item.time || "") + ' · ' + esc(item.source || "智能推荐") + '</span></div>' +
      '<em>' + esc(item.department || "科室待确认") + '</em>' +
      '<b>' + (item.doctorCount || 0) + ' 位专家 / ' + (item.hospitalCount || 0) + ' 家医院</b>' +
    '</button>';
  }).join("");
}

function buildMineStarredDoctors() {
  var ids = getStarredIds();
  if (!ids.length) return '<div class="mine-empty">暂无优推医生。你可以在医生卡片或推荐结果里点击“优推”。</div>';
  return ids.slice(0, 8).map(function(id) {
    var name = starredDoctors[id] || "医生";
    return '<button class="mine-doctor-chip" onclick="openDoctorProfile(' + id + ')">' +
      uiIcon("doctor", "icon-inline") + '<span>' + esc(name) + '</span>' +
    '</button>';
  }).join("");
}

function renderMine() {
  var user = getCurrentUserProfile();
  var records = getRecommendRecords();
  var starred = getStarredIds();
  var currentLocation = getStoredAutoLocation();
  var locationText = formatAutoLocation(currentLocation);
  $("#mainContent").innerHTML =
    '<div class="mine-hero">' +
      '<div class="mine-user-card">' +
        '<div class="mine-avatar">' + esc((user.name || "U").slice(0, 1).toUpperCase()) + '</div>' +
        '<div class="mine-user-main">' +
          '<span class="tag ' + (user.loggedIn ? "tag-green" : "tag-orange") + '">' + (user.loggedIn ? "已登录" : "未登录") + '</span>' +
          '<h2>' + esc(user.name) + '</h2>' +
          '<p>' + esc(user.role) + ' · 最近登录：' + esc(user.loginAt) + '</p>' +
        '</div>' +
        '<div class="mine-user-actions">' +
          (user.loggedIn ? '<button class="btn btn-outline btn-sm" onclick="logoutApp();navigate(\'dashboard\')">退出登录</button>' : '<button class="btn btn-primary btn-sm" onclick="openLoginModal()">立即登录</button>') +
          '<button class="btn btn-primary btn-sm" onclick="navigate(\'recommend\')">开始推荐</button>' +
        '</div>' +
      '</div>' +
      '<div class="mine-stat-grid">' +
        '<div class="mine-stat-card"><span>优推医生</span><strong>' + starred.length + '</strong><em>已收藏</em></div>' +
        '<div class="mine-stat-card"><span>推荐记录</span><strong>' + records.length + '</strong><em>本机保存</em></div>' +
        '<div class="mine-stat-card"><span>定位状态</span><strong>' + (currentLocation ? "已开启" : "未开启") + '</strong><em>' + esc(locationText) + '</em></div>' +
      '</div>' +
    '</div>' +
    '<div class="mine-layout">' +
      '<section class="mine-panel">' +
        '<div class="mine-panel-head"><div><span>Favorite Doctors</span><h3>我的优推医生</h3></div><button class="btn btn-outline btn-sm" onclick="navigate(\'doctors\')">去选择</button></div>' +
        '<div class="mine-chip-grid">' + buildMineStarredDoctors() + '</div>' +
      '</section>' +
      '<section class="mine-panel">' +
        '<div class="mine-panel-head"><div><span>Location Preference</span><h3>定位与推荐偏好</h3></div><button class="btn btn-outline btn-sm" onclick="requestAutoLocation()">重新定位</button></div>' +
        '<div class="mine-preference-grid">' +
          '<div><span>当前位置</span><strong>' + esc(locationText) + '</strong></div>' +
          '<div><span>推荐策略</span><strong>危急优先急诊，普通病综合距离/科室/医生画像</strong></div>' +
          '<div><span>数据保存</span><strong>记录保存在当前浏览器本地，演示环境不上传账号数据</strong></div>' +
        '</div>' +
      '</section>' +
      '<section class="mine-panel mine-record-panel">' +
        '<div class="mine-panel-head"><div><span>Recent Recommendations</span><h3>最近推荐记录</h3></div><button class="btn btn-outline btn-sm" onclick="clearRecommendRecords();renderMine()">清空</button></div>' +
        '<div class="mine-record-list">' + buildMineRecordCards(records) + '</div>' +
      '</section>' +
    '</div>';
}

// ========== API文档 ==========
function renderApiDocs() {
  $("#mainContent").innerHTML =
    '<h2 class="page-title">数据接口文档</h2>' +
    '<p class="page-subtitle">已接入爬取的1892位真实医生数据</p>' +
    '<div class="api-endpoint"><span class="api-method method-post">POST</span><span class="api-path">/api/recommend</span><p class="api-desc"><strong>核心推荐接口。</strong>参数: {condition, scenario: surgery|common|complex|first_visit, district}。使用动态权重算法，返回推荐医院+医生。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/hospitals/:id/doctors</span><p class="api-desc">获取某医院所有医生（真实数据）。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/doctors</span><p class="api-desc">获取医生列表，支持department和hospital_id筛选。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/doctors/detail/:id</span><p class="api-desc">获取医生详情（含手术量、论文、科研成果）。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/stats</span><p class="api-desc">系统统计数据。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/transit/stats</span><p class="api-desc">公共交通融合统计：公交线路、站点覆盖、出租车运营样本、到院成本、医院交通可达性，以及共享骑行绿色出行展示。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/transit/routes</span><p class="api-desc">常武地区公交线路脱敏明细数据，来源于可信数据空间样例库。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/transit/stations</span><p class="api-desc">常武地区公交站点脱敏明细数据，含站点经纬度、站点名称、道路、站台形式。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/transit/taxi-operations</span><p class="api-desc">出租车/网约车运营脱敏样本数据，前端仅展示里程、费用、区域、时间段和经纬度统计。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/transit/bike-stations</span><p class="api-desc">公共自行车/助力车站点脱敏数据，含站点经纬度、可租车辆、助力车辆、锁车桩和围栏范围。</p></div>' +
    '<div class="api-endpoint"><span class="api-method method-get">GET</span><span class="api-path">/api/transit/bike-vehicles</span><p class="api-desc">共享单车/助力车车辆状态脱敏数据，仅用于绿色出行展示和地图车辆分布，不参与医疗推荐排序。</p></div>';
}

// ================================================================
// 医疗小助手 - 初次就诊 Q&A 模式
// ================================================================
var ASSISTANT_STEPS = [
  { id: "type", type: "buttons", question: "您好，我是您的医疗小助手。请先选择您要描述的病情类型：", options: ["手术/重症", "常见病症", "疑难/罕见病", "初次就诊/不确定"] },
  { id: "symptoms", type: "text", question: "请描述这类病情的具体症状、持续时间、疼痛位置或想咨询的疾病/手术。", placeholder: "例如：胸痛胸闷 2 天，活动后加重，想咨询冠脉支架相关医生...", btnLabel: "发送" },
  { id: "duration", type: "buttons", question: "这个症状大概持续多久了？", options: ["1周以内", "1-4周", "1-6个月", "半年以上"] },
  { id: "severity", type: "buttons", question: "症状的严重程度如何？", options: ["轻微，不影响日常生活", "中等，有些影响", "较严重，明显影响生活"] },
  { id: "extra", type: "text_skip", question: "除了以上症状，还有其他不适吗？", placeholder: "请输入其他症状（没有可跳过）", btnLabel: "发送", skipLabel: "没有其他症状" }
];
var AS_TOTAL = ASSISTANT_STEPS.length;

var asState = { active: false, step: 0, msgs: [], answers: {}, waiting: false, dynamicSteps: [], followupChecked: false, currentDynamicStep: null };
var asSpeechRecognition = null;
var asSpeechActiveButton = null;
var recommendVoiceRecognition = null;
var recommendVoiceTranscriptText = "";
var recommendVoiceStopRequested = false;
var autoLocationRequestSeq = 0;
window._assistantBubbleCollapsed = false;
window._assistantContext = { type: "page", title: "首页总览", desc: "可查看医疗资源概览、医院分布和智能推荐入口。", data: { page: "dashboard" } };

function setAssistantContext(type, data) {
  data = data || {};
  var ctx = { type: type || "page", title: "", desc: "", data: data, updatedAt: new Date().toISOString() };
  if (ctx.type === "hospital") {
    ctx.title = data.name || "医院";
    ctx.desc = [data.level, data.type, data.address].filter(function(v) { return v; }).join(" · ");
  } else if (ctx.type === "doctor") {
    ctx.title = data.name || "医生";
    ctx.desc = [data.title, getDoctorHospitalName(data), data._department_group || normalizeDepartmentName(data.department)].filter(function(v) { return v; }).join(" · ");
  } else if (ctx.type === "map_hospital") {
    ctx.title = data.name || "地图医院";
    ctx.desc = [data.level, data.type, data._distanceText || data.address].filter(function(v) { return v; }).join(" · ");
  } else {
    var pageNames = { dashboard: "首页总览", recommend: "智能推荐", hospitals: "医院列表", doctors: "医生列表", map: "地图视图", "api-docs": "接口文档", "hospital-detail": "医院详情" };
    ctx.title = data.title || pageNames[data.page] || "当前页面";
    ctx.desc = data.desc || "我会根据当前页面和您点击的内容给出下一步建议。";
  }
  window._assistantContext = ctx;
  updateAssistantBubble();
  renderAssistantContextPanel();
}

function updateAssistantBubble() {
  var bubble = document.querySelector(".assistant-speech-bubble");
  if (!bubble) return;
  var ctx = window._assistantContext || {};
  if (window._assistantBubbleCollapsed) {
    bubble.classList.remove("has-action");
    bubble.classList.remove("has-intro");
    bubble.classList.add("is-collapsed");
    bubble.innerHTML = '<span class="assistant-bubble-text">小助手待命</span><span class="assistant-bubble-minimize" onclick="expandAssistantBubble(event)">展开</span>';
    return;
  }
  bubble.classList.remove("is-collapsed");
  if (ctx.type === "hospital" || ctx.type === "map_hospital") {
    bubble.classList.remove("has-action");
    bubble.classList.add("has-intro");
    bubble.innerHTML = buildHospitalBubbleIntro(ctx.data || {}) + buildAssistantBubbleMinimize();
  } else if (ctx.type === "doctor") {
    bubble.classList.remove("has-action");
    bubble.classList.add("has-intro");
    bubble.innerHTML = buildDoctorBubbleIntro(ctx.data || {}) + buildAssistantBubbleMinimize();
  } else {
    bubble.classList.remove("has-action");
    bubble.classList.remove("has-intro");
    bubble.innerHTML = '<span class="assistant-bubble-text">' + esc(ctx.type === "recommend" ? "我可以帮你继续问诊" : "你好，有什么问题问我吧") + '</span>' + buildAssistantBubbleMinimize();
  }
}

function buildAssistantBubbleMinimize() {
  return '<span class="assistant-bubble-minimize" onclick="minimizeAssistantBubble(event)">收起</span>';
}

function minimizeAssistantBubble(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  window._assistantBubbleCollapsed = true;
  updateAssistantBubble();
}

function expandAssistantBubble(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  window._assistantBubbleCollapsed = false;
  updateAssistantBubble();
}

function buildAssistantContextActions(ctx) {
  if (!ctx) return "";
  var d = ctx.data || {};
  if ((ctx.type === "hospital" || ctx.type === "map_hospital") && d.id != null) {
    return '<button onclick="handleAssistantContextAction(\'hospital_intro\')">介绍一下</button>' +
      '<button onclick="handleAssistantContextAction(\'hospital_detail\')">看详情</button>' +
      '<button onclick="handleAssistantContextAction(\'hospital_nav\')">立即导航</button>' +
      '<button onclick="handleAssistantContextAction(\'hospital_recommend\')">按这家医院推荐</button>';
  }
  if (ctx.type === "doctor" && d.id != null) {
    return '<button onclick="handleAssistantContextAction(\'doctor_intro\')">介绍一下</button>' +
      '<button onclick="handleAssistantContextAction(\'doctor_profile\')">看名片</button>' +
      '<button onclick="handleAssistantContextAction(\'doctor_star\')">优推医生</button>' +
      '<button onclick="handleAssistantContextAction(\'doctor_recommend\')">按这个科室推荐</button>';
  }
  if (ctx.data && ctx.data.page === "recommend") {
    return '<button onclick="handleAssistantContextAction(\'start_triage\')">开始问诊</button>' +
      '<button onclick="handleAssistantContextAction(\'show_records\')">看聊天记录</button>';
  }
  if (ctx.data && ctx.data.page === "map") {
    return '<button onclick="handleAssistantContextAction(\'locate_me\')">自动定位</button>' +
      '<button onclick="handleAssistantContextAction(\'go_hospitals\')">看医院列表</button>';
  }
  return '<button onclick="handleAssistantContextAction(\'go_recommend\')">开始智能推荐</button>' +
    '<button onclick="handleAssistantContextAction(\'go_hospitals\')">查看医院</button>';
}

function renderAssistantContextPanel() {
  var panel = document.getElementById("assistantContextPanel");
  if (!panel) return;
  var ctx = window._assistantContext || {};
  var typeLabel = { page: "页面感知", hospital: "医院感知", map_hospital: "地图选择", doctor: "医生感知", recommend: "问诊上下文" }[ctx.type] || "当前上下文";
  panel.innerHTML =
    '<div class="assistant-context-card">' +
      '<div class="assistant-context-kicker">' + esc(typeLabel) + '</div>' +
      '<div class="assistant-context-title">' + esc(ctx.title || "当前页面") + '</div>' +
      '<div class="assistant-context-desc">' + esc(ctx.desc || "我会根据您当前点击的位置给出下一步建议。") + '</div>' +
      '<div class="assistant-context-actions">' + buildAssistantContextActions(ctx) + '</div>' +
    '</div>';
}

function buildHospitalBubbleIntro(h) {
  h = h || {};
  var meta = [h.level, h.type].filter(function(v) { return v; }).join(" · ") || "医院资源";
  return '<span class="assistant-bubble-title">' + esc(h.name || "这家医院") + '</span>' +
    '<span class="assistant-bubble-meta">' + esc(meta) + '</span>' +
    '<span class="assistant-bubble-desc">' + esc(buildHospitalIntro(h)) + '</span>';
}

function buildDoctorBubbleIntro(d) {
  d = d || {};
  var dept = d._department_group || normalizeDepartmentName(d.department);
  var meta = [d.title, getDoctorHospitalName(d), dept].filter(function(v) { return v; }).join(" · ") || "医生资源";
  return '<span class="assistant-bubble-title">' + esc(d.name || "这位医生") + '</span>' +
    '<span class="assistant-bubble-meta">' + esc(meta) + '</span>' +
    '<span class="assistant-bubble-desc">' + esc(buildDoctorIntro(d)) + '</span>';
}

function buildHospitalIntro(h) {
  h = h || {};
  var parts = [];
  parts.push((h.name || "这家医院") + "是" + [h.level, h.type].filter(function(v) { return v; }).join("、") + "。");
  if (h.address) parts.push("地址在" + h.address + "。");
  var capacity = [];
  if (h.beds) capacity.push("床位约" + h.beds + "张");
  if (h.daily_outpatients) capacity.push("日均门诊约" + h.daily_outpatients + "人次");
  if (capacity.length) parts.push("服务能力方面，" + capacity.join("，") + "。");
  var strengths = (h.strengths || []).slice(0, 5);
  if (strengths.length) parts.push("重点专科包括：" + strengths.join("、") + "。");
  parts.push(h.emergency ? "这家医院支持急诊，急症仍建议优先拨打120或就近急诊。" : "如果是胸痛、呼吸困难、意识障碍等急症，仍建议优先120或就近急诊。");
  return parts.join("");
}

function buildDoctorIntro(d) {
  d = d || {};
  var dept = d._department_group || normalizeDepartmentName(d.department);
  var parts = [];
  parts.push((d.name || "这位医生") + "，" + [d.title, d.academic_title].filter(function(v) { return v; }).join("、") + "，来自" + [getDoctorHospitalName(d), dept].filter(function(v) { return v; }).join(" · ") + "。");
  var kws = (d.keywords || d.specialties || []).slice(0, 6);
  if (kws.length) parts.push("擅长方向主要包括：" + kws.join("、") + "。");
  var metrics = [];
  if (d.surgery_count_note || d.surgery_count) metrics.push("经验量" + (d.surgery_count_note || d.surgery_count + "例"));
  if (metrics.length) parts.push("公开画像指标显示：" + metrics.join("，") + "。");
  parts.push("如果您的症状和" + (dept || "该科室") + "相关，可以继续用智能推荐结合病情、距离和医院层级综合判断。");
  return parts.join("");
}

function assistantIntroduceContext(kind) {
  ensureAssistantWidget();
  openAssistantWidget();
  var ctx = window._assistantContext || {};
  var d = ctx.data || {};
  var text = kind === "doctor" ? buildDoctorIntro(d) : buildHospitalIntro(d);
  addMsg("assistant", text);
}

function handleAssistantContextAction(action) {
  var ctx = window._assistantContext || {};
  var d = ctx.data || {};
  if (action === "hospital_intro") { assistantIntroduceContext("hospital"); return; }
  if (action === "hospital_detail" && d.id != null) { navigate("hospital-detail", { hid: d.id }); return; }
  if (action === "hospital_nav" && d.id != null) { openHospitalNavigation(d.id); return; }
  if (action === "hospital_recommend" && d.id != null) {
    window._recommendPrefill = { condition: "我想优先考虑" + (d.name || "这家医院") + "，请结合我的症状推荐合适科室和医生", scenario: "first_visit" };
    navigate("recommend");
    return;
  }
  if (action === "doctor_intro") { assistantIntroduceContext("doctor"); return; }
  if (action === "doctor_profile" && d.id != null) { openDoctorProfile(d.id); return; }
  if (action === "doctor_star" && d.id != null) { toggleStar(d.id, d.name || "医生"); return; }
  if (action === "doctor_recommend") {
    var dept = d._department_group || normalizeDepartmentName(d.department);
    window._recommendPrefill = { condition: "我想咨询" + (dept || "相关科室") + "问题，希望参考" + (d.name || "这位医生") + "的专长进行推荐", scenario: "first_visit" };
    navigate("recommend");
    return;
  }
  if (action === "start_triage") { resetAS(); return; }
  if (action === "show_records") { openRecommendRecordModal(); return; }
  if (action === "locate_me") { locateUser(); return; }
  if (action === "go_hospitals") { navigate("hospitals"); return; }
  if (action === "go_recommend") { navigate("recommend"); return; }
}

function initAS() { asState = { active: true, step: 0, msgs: [], answers: {}, waiting: false, dynamicSteps: [], followupChecked: false, currentDynamicStep: null }; }

function ensureAssistantWidget() {
  if (document.getElementById("assistantWidget")) return;
  var widget = document.createElement("div");
  widget.id = "assistantWidget";
  widget.className = "assistant-widget";
  widget.innerHTML =
    '<button class="assistant-fab" onclick="toggleAssistantWidget()" aria-label="打开医疗小助手">' +
      '<span class="assistant-speech-bubble">你好，有什么问题问我吧</span>' +
      '<span class="assistant-dog-stage" aria-hidden="true">' +
        '<span class="assistant-dog-shadow"></span>' +
        '<img class="assistant-dog-img" src="/static/images/assistant/assistant_doctor_male_cutout.png?v=1" alt="医疗小助手">' +
      '</span>' +
      '<span class="assistant-fab-pulse"></span>' +
    '</button>' +
    '<div class="assistant-panel" id="assistantPanel">' +
      '<div class="chat-header assistant-panel-head">' +
        '<div class="chat-header-icon">' + uiIcon("api", "icon-lg") + '</div>' +
        '<div class="chat-header-text"><div class="chat-header-title">医疗小助手</div><div class="chat-header-subtitle">全局问诊 · 推荐医生和医院</div></div>' +
        '<button class="btn btn-outline btn-sm chat-reset-btn" onclick="resetAS()">重置</button>' +
        '<button class="assistant-close" onclick="closeAssistantWidget()" aria-label="收起">&times;</button>' +
      '</div>' +
      '<div id="assistantContextPanel" class="assistant-context-panel"></div>' +
      '<div class="chat-messages" id="chatMessages"></div>' +
      '<div class="chat-input-area" id="chatInputArea"></div>' +
    '</div>';
  document.body.appendChild(widget);
  renderAssistantContextPanel();
  updateAssistantBubble();
}

function openAssistantWidget() {
  ensureAssistantWidget();
  var widget = document.getElementById("assistantWidget");
  if (widget) widget.classList.add("open");
  renderAssistantContextPanel();
}

function closeAssistantWidget() {
  var widget = document.getElementById("assistantWidget");
  if (widget) widget.classList.remove("open");
}

function toggleAssistantWidget() {
  ensureAssistantWidget();
  var widget = document.getElementById("assistantWidget");
  if (!widget) return;
  if (widget.classList.contains("open")) closeAssistantWidget();
  else if (asState.active && asState.msgs.length) openAssistantWidget();
  else startAssistant();
}

function startAssistant() {
  ensureAssistantWidget();
  openAssistantWidget();
  renderAssistantContextPanel();
  initAS();
  // 保存当前区域选择，供后续距离重排使用
  var districtEl = document.getElementById("recDistrict");
  window._savedDistrict = districtEl ? districtEl.value : "天宁区";
  var md = document.getElementById("chatMessages");
  if (md) md.innerHTML = "";
  var ia = document.getElementById("chatInputArea");
  if (ia) ia.innerHTML = "";
  var rd = document.getElementById("recResults");
  if (rd) rd.innerHTML = '<div class="recommend-empty-panel"><div class="recommend-empty-head"><strong>医疗小助手已打开</strong><p>完成右下角悬浮问诊后，推荐结果会以弹窗形式展示，并同步保存到下方记录。</p></div></div>';
  setTimeout(function() { showStep(); }, 300);
}

function showStep() {
  if (asState.dynamicSteps && asState.dynamicSteps.length) {
    var dynamicStep = asState.dynamicSteps.shift();
    asState.currentDynamicStep = dynamicStep;
    addMsg("assistant", dynamicStep.question);
    renderASInput(dynamicStep);
    asState.waiting = true;
    return;
  }
  if (asState.step >= AS_TOTAL) { runASRec(); return; }
  var step = ASSISTANT_STEPS[asState.step];
  addMsg("assistant", step.question);
  renderASInput(step);
  asState.waiting = true;
}

function addMsg(role, text) {
  asState.msgs.push({ role: role, text: text });
  var md = document.getElementById("chatMessages");
  if (!md) return;
  var el = document.createElement("div");
  el.className = "chat-message chat-msg-" + role;
  if (role === "assistant") {
    el.innerHTML = '<div class="chat-avatar">' + uiIcon("api") + '</div><div class="chat-bubble chat-bubble-assistant">' + esc(text) + '</div>';
  } else {
    el.innerHTML = '<div class="chat-bubble chat-bubble-user">' + esc(text) + '</div><div class="chat-avatar chat-avatar-user">' + uiIcon("doctor") + '</div>';
  }
  md.appendChild(el);
  md.scrollTop = md.scrollHeight;
  renderRecommendRecords();
}

function renderASInput(step) {
  var ia = document.getElementById("chatInputArea");
  if (!ia) return;
  stopASVoice();
  ia.innerHTML = "";
  if (step.type === "buttons" || (step.options && step.options.length)) {
    var bc = document.createElement("div");
    bc.className = "chat-quick-replies";
    for (var i = 0; i < (step.options || []).length; i++) {
      (function(opt) {
        var btn = document.createElement("button");
        btn.className = "chat-reply-btn";
        btn.textContent = opt;
        btn.addEventListener("click", function() { handleAS(opt); });
        bc.appendChild(btn);
      })(step.options[i]);
    }
    ia.appendChild(bc);
  } else {
    var row = document.createElement("div");
    row.className = "chat-text-input-row";
    var input = document.createElement("input");
    input.type = "text"; input.className = "chat-text-input";
    input.placeholder = step.placeholder || "";
    input.addEventListener("keydown", function(e) { if (e.key === "Enter") handleAS(input.value); });
    row.appendChild(input);
    var vbtn = document.createElement("button");
    vbtn.type = "button";
    vbtn.className = "chat-voice-btn";
    vbtn.title = "语音输入";
    vbtn.setAttribute("aria-label", "语音输入");
    vbtn.innerHTML = '<span class="voice-icon"></span>';
    vbtn.addEventListener("click", function() { toggleASVoice(input, vbtn); });
    row.appendChild(vbtn);
    var sbtn = document.createElement("button");
    sbtn.className = "chat-send-btn"; sbtn.textContent = step.btnLabel || "发送";
    sbtn.addEventListener("click", function() { handleAS(input.value); });
    row.appendChild(sbtn);
    ia.appendChild(row);
    if (step.type === "text_skip") {
      var sr = document.createElement("div"); sr.className = "chat-skip-row";
      var skb = document.createElement("button"); skb.className = "chat-skip-btn";
      skb.textContent = step.skipLabel || "跳过";
      skb.addEventListener("click", function() { handleAS(step.skipLabel || "没有其他症状"); });
      sr.appendChild(skb); ia.appendChild(sr);
    }
    setTimeout(function() { input.focus(); }, 100);
  }
}

function getSpeechRecognitionCtor() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function toggleASVoice(input, button) {
  if (asSpeechRecognition) {
    stopASVoice();
    return;
  }
  var SpeechRecognition = getSpeechRecognitionCtor();
  if (!SpeechRecognition) {
    toast("当前浏览器不支持语音识别，请使用 Chrome 或 Edge");
    return;
  }
  try {
    var recognition = new SpeechRecognition();
    asSpeechRecognition = recognition;
    asSpeechActiveButton = button;
    recognition.lang = "zh-CN";
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;
    var baseText = (input.value || "").trim();
    if (button) button.classList.add("listening");
    toast("正在识别语音，请开始说话");
    recognition.onresult = function(event) {
      var finalText = "";
      var interimText = "";
      for (var i = event.resultIndex; i < event.results.length; i++) {
        var text = event.results[i][0].transcript || "";
        if (event.results[i].isFinal) finalText += text;
        else interimText += text;
      }
      var merged = [baseText, finalText || interimText].filter(function(v) { return v; }).join(baseText ? "，" : "");
      input.value = merged;
      input.focus();
    };
    recognition.onerror = function(event) {
      var type = event && event.error ? event.error : "";
      if (type === "not-allowed") toast("浏览器未授权麦克风，请允许后再试");
      else if (type === "no-speech") toast("没有识别到语音，请再试一次");
      else toast("语音识别失败，请手动输入");
    };
    recognition.onend = function() {
      if (asSpeechActiveButton) asSpeechActiveButton.classList.remove("listening");
      asSpeechRecognition = null;
      asSpeechActiveButton = null;
    };
    recognition.start();
  } catch (e) {
    stopASVoice();
    toast("语音识别启动失败，请检查浏览器权限");
  }
}

function stopASVoice() {
  if (asSpeechActiveButton) asSpeechActiveButton.classList.remove("listening");
  if (asSpeechRecognition) {
    try { asSpeechRecognition.stop(); } catch (e) {}
  }
  asSpeechRecognition = null;
  asSpeechActiveButton = null;
}

function scenarioFromAssistantType(text) {
  var t = String(text || "");
  if (t.indexOf("手术") >= 0 || t.indexOf("重症") >= 0) return "surgery";
  if (t.indexOf("常见") >= 0) return "common";
  if (t.indexOf("疑难") >= 0 || t.indexOf("罕见") >= 0) return "complex";
  return "first_visit";
}

function requestAssistantFollowup(condition, scenario, done) {
  var ia = document.getElementById("chatInputArea");
  if (ia) ia.innerHTML = '<div class="chat-loading"><div class="spinner"></div><span>判断是否需要追问...</span></div>';
  fetch(API + "/followup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ condition: condition, scenario: scenario || "common" })
  }).then(function(res) { return res.json(); }).then(function(json) {
    if (ia) ia.innerHTML = "";
    if (json.code === 200 && json.data && json.data.htriage_analysis) {
      asState.answers.htriage_preview = json.data.htriage_analysis;
      var followup = json.data.followup || {};
      var questions = followup.questions || [];
      if (questions.length) {
        asState.dynamicSteps = questions.map(function(q) {
          return {
            id: "followup_" + q.id,
            type: q.options && q.options.length ? "buttons" : "text",
            question: q.question,
            options: q.options || [],
            placeholder: "请补充说明",
            btnLabel: "发送"
          };
        });
        addMsg("assistant", "为了让推荐更准确，我需要再确认 " + questions.length + " 个关键信息。");
      }
    }
    if (typeof done === "function") done();
  }).catch(function() {
    if (ia) ia.innerHTML = "";
    if (typeof done === "function") done();
  });
}

function handleAS(text) {
  text = (text || "").trim();
  if (!text) { toast("请输入您的回答"); return; }
  stopASVoice();
  addMsg("user", text);
  var step = (asState.currentDynamicStep || null) || ASSISTANT_STEPS[asState.step];
  asState.answers[step.id] = text;
  if (asState.currentDynamicStep) {
    if (!asState.answers.followup_answers) asState.answers.followup_answers = {};
    asState.answers.followup_answers[step.id] = text;
    asState.currentDynamicStep = null;
    var iaDyn = document.getElementById("chatInputArea");
    if (iaDyn) iaDyn.innerHTML = "";
    asState.waiting = false;
    setTimeout(function() { showStep(); }, 500);
    return;
  }
  if (step.id === "type") {
    asState.answers.scenario = scenarioFromAssistantType(text);
    setRecommendScenario(asState.answers.scenario);
    addMsg("assistant", "已切换到“" + esc(SCENARIO_LABELS[asState.answers.scenario] || text) + "”，接下来请描述具体病情。");
  }
  var ia = document.getElementById("chatInputArea");
  if (ia) ia.innerHTML = "";
  asState.step++;
  asState.waiting = false;
  if (step.id === "symptoms" && !asState.followupChecked) {
    asState.followupChecked = true;
    requestAssistantFollowup(text, asState.answers.scenario || scenarioFromAssistantType(asState.answers.type), function() {
      setTimeout(function() { showStep(); }, 500);
    });
    return;
  }
  setTimeout(function() { showStep(); }, 500);
}

function runASRec() {
  addMsg("assistant", "好的，我已经了解了您的情况。正在为您分析并推荐最合适的医生...");
  var ia = document.getElementById("chatInputArea");
  if (ia) ia.innerHTML = '<div class="chat-loading"><div class="spinner"></div><span>分析中...</span></div>';

  var parts = [];
  var ans = asState.answers;
  if (ans.symptoms) parts.push(ans.symptoms);
  if (ans.followup_answers) {
    Object.keys(ans.followup_answers).forEach(function(key) {
      var val = ans.followup_answers[key];
      if (val) parts.push(val);
    });
  }
  if (ans.severity && ans.severity.indexOf("较严重") >= 0 && parts.length > 0) parts[0] = "严重 " + parts[0];
  if (ans.extra && ans.extra !== "没有其他症状") parts.push(ans.extra);
  var condition = parts.join("，");
  var scenario = ans.scenario || scenarioFromAssistantType(ans.type);

  var districtEl = document.getElementById("recDistrict");
  var district = districtEl ? districtEl.value : "天宁区";

  var payload = { condition: condition, scenario: scenario, district: district };
  if (window._autoLocation) {
    payload.lat = window._autoLocation.lat;
    payload.lng = window._autoLocation.lng;
    payload.district = window._autoLocation.district || district;
  }

  fetch(API + "/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(function(res) { return res.json(); }).then(function(json) {
    if (json.code !== 200) { addMsg("assistant", "抱歉，推荐过程中出现问题：" + esc(json.message) + '。请点击右上角"重置"按钮重新开始。'); if (ia) ia.innerHTML = ""; return; }
    renderChatResults(json.data);
    renderSidePanel(json.data);
  }).catch(function() {
    addMsg("assistant", '抱歉，网络请求失败，请稍后重试。您可以点击右上角"重置"按钮重新开始。');
    if (ia) ia.innerHTML = "";
  });
}

function renderChatResults(data) {
  var ia = document.getElementById("chatInputArea");
  if (ia) ia.innerHTML = "";
  var displayDoctors = sortDoctorItemsPhotoFirst(data.recommended_doctors || []);

  var summary = "分析完成。";
  if (data.triage) summary += " 分诊提示：" + esc(data.triage.label || "") + "，" + esc(data.triage.care_level || "") + "。";
  if (data.matched_department) summary += " 根据您的描述，建议就诊科室：<b>" + esc(data.matched_department) + "</b>。";
  summary += " 为您推荐 " + data.recommended_doctors.length + " 位专家和 " + data.recommended_hospitals.length + " 家医院。";
  addMsg("assistant", summary);

  var md = document.getElementById("chatMessages");
  if (!md) return;

  var rc = document.createElement("div");
  rc.className = "chat-results-container";

  if (displayDoctors.length > 0) {
    var ds = document.createElement("div");
    ds.className = "chat-results-section";
    ds.innerHTML = '<h4 class="chat-results-title">推荐专家</h4>';
    var rkl = ["gold", "silver", "bronze"];
    var maxD = Math.min(5, displayDoctors.length);
    for (var i = 0; i < maxD; i++) {
      var item = displayDoctors[i];
      var d = item.doctor;
      cacheDoctor(d);
      var rk = i < 3 ? rkl[i] : "";
      var card = document.createElement("div");
      card.className = "chat-doctor-card";
      card.setAttribute("onclick", "openDoctorProfile(" + d.id + ")");
      card.innerHTML = '<span class="rank-badge ' + rk + '" style="flex-shrink:0;">' + (i + 1) + '</span>' +
        '<div style="flex:1;min-width:0;">' +
          '<div class="chat-doc-name">' + esc(d.name) + ' <span style="font-weight:400;font-size:11px;color:var(--text-secondary);">' + esc(d.title) + '</span></div>' +
          '<div class="chat-doc-dept">' + esc(d.hospital_name + " · " + (d._department_group || normalizeDepartmentName(d.department))) + '</div>' +
          '<div style="font-size:11px;color:var(--text-secondary);">匹配度: ' + (item.match_score * 100).toFixed(1) + '</div>' +
        '</div>' +
        '<button class="btn btn-sm star-toggle' + (starredDoctors[d.id] ? ' starred' : '') + '" data-doctor-id="' + d.id + '" onclick="event.stopPropagation();toggleStar(' + d.id + ',\'' + esc(d.name).replace(/'/g, "\\'") + '\')" style="flex-shrink:0;font-size:11px;padding:3px 8px;">' + uiIcon("star", "icon-inline") + (starredDoctors[d.id] ? '已优推' : '优推') + '</button>';
      ds.appendChild(card);
    }
    rc.appendChild(ds);
  }

  if (data.recommended_hospitals.length > 0) {
    var hs = document.createElement("div");
    hs.className = "chat-results-section";
    hs.innerHTML = '<h4 class="chat-results-title">推荐医院</h4>';
    var rkl2 = ["gold", "silver", "bronze"];
    var maxH = Math.min(3, data.recommended_hospitals.length);
    for (var j = 0; j < maxH; j++) {
      var hItem = data.recommended_hospitals[j];
      var h = cacheHospital(hItem.hospital);
      var hrk = j < 3 ? rkl2[j] : "";
      var hcard = document.createElement("div");
      hcard.className = "chat-doctor-card";
      hcard.setAttribute("onclick", "openHospitalProfile(" + h.id + ")");
      hcard.innerHTML = '<span class="rank-badge ' + hrk + '" style="flex-shrink:0;">' + (j + 1) + '</span>' +
        '<div style="flex:1;min-width:0;">' +
          '<div class="chat-doc-name">' + esc(h.name) + ' <span class="tag tag-blue" style="font-size:10px;">' + esc(h.level) + '</span></div>' +
          '<div style="font-size:11px;color:var(--text-secondary);">距离 ' + hItem.distance + 'km · 推荐指数 ' + hItem.composite_score + '</div>' +
        '</div>';
      hs.appendChild(hcard);
    }
    rc.appendChild(hs);
  }

  md.appendChild(rc);
  md.scrollTop = md.scrollHeight;
  addMsg("assistant", '以上就是为您推荐的专家和医院。如需重新问诊，请点击右上角"重置"按钮。祝您早日康复。');
}

function renderSidePanel(data) {
  var rd = document.getElementById("recResults");
  var html = buildEmergencyPriorityPanel(data);
  html += buildTriageBanner(data.triage);
  html += buildRadarVisual(data.condition || (asState.answers.symptoms || ""));
  if (data.matched_department) {
    html += '<div style="margin-bottom:16px;font-size:14px;">匹配科室：<span class="tag tag-blue" style="font-size:13px;">' + esc(data.matched_department) + '</span><span style="margin-left:8px;font-size:11px;color:var(--text-secondary);">场景: ' + esc(SCENARIO_LABELS[data.effective_scenario] || "初次就诊") + '</span>' + (data.data_source === "real" ? '<span class="tag tag-green" style="margin-left:4px;">真实数据</span>' : "") + '</div>';
  }
  html += '<h4 style="margin-bottom:12px;">推荐专家 (' + data.recommended_doctors.length + '位)</h4>';
  html += '<div class="doctor-grid doctor-grid-recommend">' + buildDoctorCards(data.recommended_doctors) + '</div>';
  html += '<div id="rerankToolbar" style="display:none;align-items:center;gap:10px;padding:10px 14px;margin-top:16px;background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;font-size:13px;">' +
    '<span id="rerankCount" style="font-weight:600;color:#92400e;">已优推 0 位医生</span>' +
    '<button id="rerankBtn" class="btn btn-sm" onclick="rerankByDistance()" style="background:#f59e0b;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-weight:600;">按距离重排优推医生</button>' +
    '</div>' +
    '<div id="rerankResults"></div>';
  html += '<h4 style="margin:24px 0 12px;">推荐医院 (' + data.recommended_hospitals.length + ')</h4>';
  html += buildHospitalCards(data.recommended_hospitals);
  window._lastRecommendResultHtml = html;
  if (rd) rd.innerHTML = buildRecommendSummaryPanel(data, data.condition || (asState.answers.symptoms || "问诊结果"));
  saveRecommendRecord(makeRecommendRecord(data, data.condition || (asState.answers.symptoms || "问诊结果"), "小助手问诊"));
  openRecommendResultModal("小助手问诊推荐", html);
}

function resetAS() {
  ensureAssistantWidget();
  openAssistantWidget();
  initAS();
  var md = document.getElementById("chatMessages");
  if (md) md.innerHTML = "";
  var ia = document.getElementById("chatInputArea");
  if (ia) ia.innerHTML = "";
  var rd = document.getElementById("recResults");
  if (rd) rd.innerHTML = '<div class="recommend-empty-panel"><div class="recommend-empty-head"><strong>医疗小助手已重置</strong><p>请在右下角继续回答，小助手会在完成后弹出推荐结果。</p></div></div>';
  setTimeout(function() { showStep(); }, 300);
}

function restoreForm() {
  asState.active = false;
  var inner = document.getElementById("recommendFormInner");
  if (!inner) return;
  inner.innerHTML =
    buildPatientProfileForm() +
    buildRecommendVoiceControl() +
    '<div class="form-group"><label class="form-label">病情 / 症状描述 *</label><textarea class="form-input recommend-condition-input" id="recCondition" rows="5" placeholder="请尽量完整描述症状、持续时间、疼痛位置、既往病史或想咨询的疾病/手术。"></textarea></div>' +
    '<div class="quick-examples">' +
      '<button class="quick-chip" onclick="setRecommendExample(\'胸痛胸闷需要做冠脉支架\')">胸痛胸闷</button>' +
      '<button class="quick-chip" onclick="setRecommendExample(\'反复咳嗽三个月\')">反复咳嗽</button>' +
      '<button class="quick-chip" onclick="setRecommendExample(\'腰痛半年，怀疑腰椎间盘突出\')">腰痛半年</button>' +
      '<button class="quick-chip" onclick="setRecommendExample(\'小儿发热咳嗽\')">小儿发热</button>' +
    '</div>' +
          buildDistrictControl() +
    '<button class="btn btn-primary" onclick="doRecommend()" style="width:100%;justify-content:center;padding:12px;">立即推荐</button>' +
    '<div style="margin-top:14px;font-size:12px;color:var(--text-secondary);"><p style="margin-bottom:4px;">可输入疾病名、症状、科室名或手术名称。</p></div>';
}

function initTesterFeedback() {
  var btn = document.getElementById("testerFeedbackBtn");
  if (btn) btn.remove();
  var modal = document.getElementById("testerFeedbackModal");
  if (modal) modal.remove();
  return;
}

function openTesterFeedback() {
  var modal = document.getElementById("testerFeedbackModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "testerFeedbackModal";
    modal.className = "tester-feedback-modal";
    modal.onclick = function(e) { if (e.target === modal) closeTesterFeedback(); };
    document.body.appendChild(modal);
  }
  var records = getRecommendRecords();
  var last = records && records.length ? records[0] : null;
  modal.innerHTML =
    '<div class="tester-feedback-card" role="dialog" aria-modal="true">' +
      '<button class="profile-close" onclick="closeTesterFeedback()" aria-label="关闭">&times;</button>' +
      '<div class="tester-feedback-head">' +
        '<span class="tag tag-blue">Beta Test</span>' +
        '<h3>提交测试反馈</h3>' +
        '<p>请写下推荐是否准确、页面是否有 bug、定位/语音/弹窗哪里不顺手。反馈会保存到主机电脑。</p>' +
      '</div>' +
      '<div class="tester-feedback-grid">' +
        '<label><span>整体评分</span><select id="testerFeedbackScore" class="form-input"><option value="5">5 很好</option><option value="4">4 基本可用</option><option value="3">3 一般</option><option value="2">2 问题较多</option><option value="1">1 不可用</option></select></label>' +
        '<label><span>问题类型</span><select id="testerFeedbackType" class="form-input"><option>推荐准确性</option><option>页面交互</option><option>定位/导航</option><option>语音识别</option><option>数据显示</option><option>其他建议</option></select></label>' +
      '</div>' +
      '<textarea id="testerFeedbackText" class="form-input tester-feedback-text" rows="6" placeholder="例如：我输入“发烧咳嗽”，系统推荐到了某某科室，我觉得……"></textarea>' +
      (last ? '<div class="tester-feedback-last">最近一次推荐：<b>' + esc(last.department || "科室待确认") + '</b> · ' + esc(last.triage || "常规") + '</div>' : '<div class="tester-feedback-last">还没有推荐记录，也可以先反馈页面问题。</div>') +
      '<button class="btn btn-primary tester-feedback-submit" onclick="submitTesterFeedback()">提交反馈</button>' +
    '</div>';
  modal.classList.add("show");
}

function closeTesterFeedback() {
  var modal = document.getElementById("testerFeedbackModal");
  if (modal) modal.classList.remove("show");
}

function submitTesterFeedback() {
  var textEl = document.getElementById("testerFeedbackText");
  var scoreEl = document.getElementById("testerFeedbackScore");
  var typeEl = document.getElementById("testerFeedbackType");
  var feedback = textEl ? textEl.value.trim() : "";
  if (!feedback) {
    toast("请先填写反馈内容");
    return;
  }
  var records = getRecommendRecords();
  var payload = {
    tester_session: getTesterSessionId(),
    score: scoreEl ? scoreEl.value : "",
    type: typeEl ? typeEl.value : "",
    feedback: feedback,
    current_page: location.hash || location.pathname,
    last_record: records && records.length ? records[0] : null,
    user: sessionStorage.getItem("medicalUser") || "",
    role: sessionStorage.getItem("medicalRole") || "",
    screen: { width: window.innerWidth, height: window.innerHeight }
  };
  fetch(API + "/test-feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(function(res) { return res.json(); }).then(function(json) {
    if (json.code === 200) {
      toast("反馈已提交，谢谢测试");
      closeTesterFeedback();
    } else {
      toast(json.message || "反馈提交失败");
    }
  }).catch(function() {
    toast("反馈提交失败，请确认主机服务还在运行");
  });
}

// ========== 启动 ==========
initAuth();
initTesterFeedback();
