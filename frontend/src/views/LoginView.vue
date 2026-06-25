<template>
  <div class="login-page">
    <div class="bg-layer" />
    <div class="color-wash" />

    <div class="login-shell">
      <section class="column left-col">
        <div class="hero-panel glass-panel secondary-glass">
          <div class="hero-copy">
            <div class="eyebrow">课程项目展示</div>
            <h1>宠物医院信息系统</h1>
            <div class="project-signature">管信2301 · 张默涵</div>
            <p>
              集成临床诊疗、实验室检验、影像管理及药房自动化。通过数字化流程减少人工误差，提升医疗质量，为每一份生命的托付提供最坚实的技术保障。
            </p>
          </div>

          <div class="hero-metrics">
            <div v-for="item in heroMetrics" :key="item.label" class="metric-card">
              <span class="metric-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <span class="metric-note">{{ item.note }}</span>
            </div>
          </div>
        </div>

        <div class="news-panel glass-panel secondary-glass scroll-card">
          <div class="panel-header">
            <div>
              <div class="card-title">院内公告与行业资讯</div>
              <div class="card-subtitle">实时更新的临床病例分享与行政通知</div>
            </div>
            <el-button text class="refresh-btn" @click="loadNews">刷新</el-button>
          </div>

          <div class="news-scroll custom-scrollbar">
            <div class="news-list">
              <button
                v-for="item in newsItems"
                :key="item.id"
                class="news-item"
                @click="openNews(item)"
              >
                <div v-if="item.cover_image" class="news-thumb-wrap">
                  <img class="news-thumb" :src="item.cover_image" :alt="item.title" />
                </div>
                <div class="news-top">
                  <span class="news-tag" :class="getTagClass(item.category)">
                    {{ item.category || "医疗动态" }}
                  </span>
                  <span class="news-date">{{ formatDate(item.published_at || item.created_at) }}</span>
                </div>

                <div class="news-title">{{ item.title }}</div>
                <div class="news-summary">{{ item.summary }}</div>

                <div class="news-meta">
                  <span class="meta-source">{{ item.source_name || "行政办公室" }}</span>
                  <span class="view-detail">阅读全文 →</span>
                </div>
              </button>
            </div>
          </div>
          <el-carousel class="tips-carousel" :interval="4200" indicator-position="outside" height="160px">
            <el-carousel-item v-for="tip in petTips" :key="tip.id">
              <div class="tip-slide">
                <img class="tip-image" :src="tip.image" :alt="tip.title" />
                <div class="tip-content">
                  <div class="tip-title">{{ tip.title }}</div>
                  <div class="tip-text">{{ tip.text }}</div>
                </div>
              </div>
            </el-carousel-item>
          </el-carousel>
        </div>
      </section>

      <section class="column right-col">
        <div class="login-panel glass-panel primary-glass">
          <div class="panel-header">
            <div>
              <div class="card-title">工作站登录</div>
              <div class="card-subtitle">白之助宠物医院员工请由此进入</div>
            </div>
            <div class="header-chip">Secure Access</div>
          </div>

          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            class="login-form"
          >
            <el-form-item label="工号/账号" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入员工工号" />
            </el-form-item>

            <el-form-item label="安全密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="所属岗位" prop="role">
              <el-select
                v-model="loginForm.role"
                placeholder="请选择您的工作岗位"
                style="width: 100%"
                :teleported="false"
              >
                <el-option label="前台接诊" value="receptionist" />
                <el-option label="执业兽医师" value="doctor" />
                <el-option label="护理人员" value="nurse" />
                <el-option label="药房人员" value="pharmacist" />
                <el-option label="检验人员" value="lab_tech" />
                <el-option label="院区主任" value="manager" />
                <el-option label="系统管理员" value="admin" />
              </el-select>
            </el-form-item>

            <el-button
              type="primary"
              class="submit-btn"
              :loading="loading"
              @click="handleLogin"
            >
              进入系统
            </el-button>
          </el-form>
        </div>

        <div class="quick-panel glass-panel secondary-glass scroll-card">
          <div class="panel-header">
            <div>
              <div class="card-title">沙盒演示入口</div>
              <div class="card-subtitle">快速切换至各岗位预览业务闭环</div>
            </div>
          </div>

          <div class="quick-grid custom-scrollbar">
            <button
              v-for="item in demoRoles"
              :key="item.role"
              class="quick-item"
              @click="quickLogin(item.role)"
            >
              <div class="quick-item-header">
                <span class="quick-badge" :class="`badge-${item.dept}`">{{ item.short }}</span>
                <span class="quick-name">{{ item.name }}</span>
              </div>
              <span class="quick-desc">{{ item.desc }}</span>
            </button>
          </div>
        </div>
      </section>
    </div>

    <el-drawer v-model="newsDrawerVisible" :title="activeNews?.title || '公告详情'" size="44%">
      <div v-if="activeNews" class="news-detail">
        <div class="detail-meta">
          <span class="news-tag" :class="getTagClass(activeNews.category)">
            {{ activeNews.category || "医疗动态" }}
          </span>
          <span>{{ activeNews.source_name || "发布人" }}</span>
          <span>{{ formatDate(activeNews.published_at || activeNews.created_at) }}</span>
        </div>

        <div class="detail-content" v-html="renderMarkdown(activeNews.markdown_content || '')" />

        <el-button
          v-if="activeNews.source_url"
          plain
          class="source-btn"
          @click="openSource(activeNews.source_url)"
        >
          查阅详细文档
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../store";
import { loginWithPassword } from "../api/auth";
import { fetchNewsPosts } from "../api/news";
import { getStaticDemoUser } from "../api/staticDemo";

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const loginFormRef = ref(null);
const newsDrawerVisible = ref(false);
const activeNews = ref(null);
let newsRotateTimer = null;

const heroMetrics = Object.freeze([
  { label: "协作岗位", value: "7 大类", note: "全角色无缝业务流转" },
  { label: "行业前沿", value: "指南库", note: "同步最新兽医临床规范" },
  { label: "系统状态", value: "SSL 加密", note: "金融级数据安全保障" }
]);

const defaultNewsItems = [
  {
    id: 1,
    category: "行业动态",
    published_at: "2026-03-12",
    created_at: "2026-03-12",
    title: "WSAVA 更新犬猫营养与慢病管理建议",
    summary: "国际小动物兽医协会近期更新临床建议，强调慢病宠物应建立长期营养与复诊追踪档案，减少并发症风险。",
    source_name: "WSAVA",
    source_url: "https://wsava.org/",
    cover_image: "https://images.unsplash.com/photo-1516734212186-a967f81ad0d7?auto=format&fit=crop&w=800&q=80",
    markdown_content: "国际小动物兽医协会（WSAVA）近期更新临床建议，强调慢病宠物应建立**长期营养与复诊追踪档案**，减少并发症风险。"
  },
  {
    id: 2,
    category: "院内通知",
    published_at: "2026-04-10",
    created_at: "2026-04-10",
    title: "白之助春季义诊周开放预约（疫苗+体检）",
    summary: "本周开放犬猫基础体检与免疫评估绿色通道，建议幼宠、老年宠与慢病宠优先登记，前台可直接创建义诊预约。",
    source_name: "白之助运营中心",
    source_url: "",
    cover_image: "https://images.unsplash.com/photo-1601758174114-e711c0cbaa69?auto=format&fit=crop&w=800&q=80",
    markdown_content: "本周开放犬猫基础体检与免疫评估绿色通道，建议**幼宠、老年宠与慢病宠**优先登记。"
  },
  {
    id: 3,
    category: "安全预警",
    published_at: "2026-01-23",
    created_at: "2026-01-23",
    title: "Raaw Energy 生食犬粮细菌污染警示",
    summary: "FDA 在 2026 年 1 月 23 日发布公告，并于 2 月 6 日更新信息，提醒不要喂食受影响批次的 Raaw Energy 犬粮，原因涉及李斯特菌、沙门氏菌和弯曲杆菌风险。",
    source_name: "FDA",
    source_url: "https://www.fda.gov/animal-veterinary",
    cover_image: "https://images.unsplash.com/photo-1581888227599-779811939961?auto=format&fit=crop&w=800&q=80",
    markdown_content: "FDA 在 2026 年 1 月 23 日发布公告，并于 2 月 6 日更新信息，提醒不要喂食受影响批次的 Raaw Energy 犬粮，原因涉及 **李斯特菌、沙门氏菌和弯曲杆菌** 风险。"
  },
  {
    id: 4,
    category: "养宠妙招",
    published_at: "2026-04-08",
    created_at: "2026-04-08",
    title: "猫咪应激期 72 小时观察法",
    summary: "新环境前3天建议固定喂食、隐藏处和猫砂位置，减少频繁抱猫和追逐互动，可明显降低应激性厌食。",
    source_name: "白之助猫科门诊",
    source_url: "",
    cover_image: "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?auto=format&fit=crop&w=800&q=80",
    markdown_content: "新环境前3天建议固定喂食、隐藏处和猫砂位置，减少频繁抱猫和追逐互动，可明显降低应激性厌食。"
  }
];

const newsItems = ref(defaultNewsItems);
const petTips = Object.freeze([
  {
    id: 1,
    title: "妙招1：喂食定时定量",
    text: "成年犬猫建议每日2餐，固定时间可稳定肠胃节律，避免暴食与呕吐。",
    image: "https://images.unsplash.com/photo-1450778869180-41d0601e046e?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 2,
    title: "妙招2：每周体态打分",
    text: "通过肋骨触感与腰腹线条评估体况，超重宠物优先调整零食和运动计划。",
    image: "https://images.unsplash.com/photo-1530281700549-e82e7bf110d6?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 3,
    title: "妙招3：居家安全排查",
    text: "百合、巧克力、木糖醇、葡萄等高危物质请远离宠物可触达区域。",
    image: "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=900&q=80"
  }
]);

const loginForm = ref({ username: "", password: "", role: "" });

const demoRoles = [
  { role: "receptionist", short: "前台", name: "张悦(导诊)", desc: "分诊挂号、排队管理与收费结算", dept: "blue" },
  { role: "manager", short: "主任", name: "周院长(统筹)", desc: "多院区看板、员工绩效分析与财务对账", dept: "blue" },
  { role: "doctor", short: "医生", name: "李博(全科)", desc: "临床检查、开立处方与电子病历记录", dept: "teal" },
  { role: "lab_tech", short: "检验", name: "孙超(实验室)", desc: "化验队列管理、生化分析结果回传", dept: "amber" },
  { role: "nurse", short: "护理", name: "王佳(住院)", desc: "住院处置、生命体征监测与医嘱执行", dept: "teal" },
  { role: "pharmacist", short: "药房", name: "赵雪(药师)", desc: "处方复核、自动发药与GSP合规库存", dept: "amber" },
  { role: "admin", short: "管理", name: "运维系统组", desc: "主数据维护、工作流引擎配置与审计", dept: "blue" }
];

const loginRules = {
  username: [{ required: true, message: "请输入员工账号", trigger: "blur" }],
  password: [{ required: true, message: "请输入登录密码", trigger: "blur" }],
  role: [{ required: true, message: "请选择当前岗位", trigger: "change" }]
};

async function handleLogin() {
  const isValid = await loginFormRef.value?.validate().catch(() => false);
  if (!isValid) return;

  loading.value = true;
  try {
    const res = await loginWithPassword(loginForm.value.username, loginForm.value.password);
    const token = res?.access_token || res?.token || res?.data?.access_token || res?.data?.token;

    if (!token) {
      ElMessage.error("未获取到访问令牌");
      return;
    }

    authStore.setToken(token);
    authStore.setDemoRole("");
    await authStore.loadProfile().catch(() => null);
    ElMessage.success("白之助综合系统登录成功");
    router.push("/home");
  } catch (error) {
    ElMessage.error(error.message || "身份校验失败");
  } finally {
    loading.value = false;
  }
}

async function quickLogin(role) {
  const demoAccountMap = {
    receptionist: [{ username: "receptionist1", password: "rec123" }],
    doctor: [{ username: "doctor1", password: "doc123" }],
    nurse: [{ username: "nurse1", password: "nurse123" }],
    pharmacist: [{ username: "pharmacist1", password: "pharm123" }],
    manager: [{ username: "manager1", password: "mgr123" }],
    lab_tech: [{ username: "labtech1", password: "lab123" }],
    admin: [{ username: "admin", password: "admin123" }]
  };

  const candidates = demoAccountMap[role] || [];
  if (!candidates.length) {
    ElMessage.error("该角色暂未配置演示权限");
    return;
  }

  loading.value = true;
  try {
    let token = "";
    let lastError = null;

    for (const account of candidates) {
      try {
        const res = await loginWithPassword(account.username, account.password);
        token = res?.access_token || res?.token || res?.data?.access_token || res?.data?.token || "";
        if (token) break;
      } catch (error) {
        lastError = error;
      }
    }

    if (!token) {
      if (canUseStaticDemo()) {
        enterStaticDemo(role);
        return;
      }
      ElMessage.error(lastError?.message || "演示环境登录超时");
      return;
    }

    authStore.setToken(token);
    authStore.setDemoRole(role);
    await authStore.loadProfile().catch(() => null);
    ElMessage.success("已载入对应岗位的临床模拟数据");
    router.push("/home");
  } finally {
    loading.value = false;
  }
}

function canUseStaticDemo() {
  return import.meta.env.VITE_STATIC_DEMO === "1" || !String(import.meta.env.VITE_BACKEND_URL || "").trim();
}

function enterStaticDemo(role) {
  const profile = getStaticDemoUser(role);
  window.sessionStorage.setItem("static_demo", "1");
  window.sessionStorage.setItem("static_demo_role", role);
  authStore.setToken(`static-demo-${role}-${Date.now()}`);
  authStore.setDemoRole(role);
  authStore.setProfile(profile);
  ElMessage.success("已进入静态演示模式");
  router.push("/home");
}

async function loadNews() {
  try {
    const res = await fetchNewsPosts(String(Date.now()));
    const list = Array.isArray(res?.data) ? res.data.slice(0, 6) : [];
    newsItems.value = list.length ? [...list, ...defaultNewsItems].slice(0, 8) : defaultNewsItems;
    ElMessage.success("资讯已刷新");
  } catch (error) {
    newsItems.value = defaultNewsItems;
    const text = String(error?.message || "").toLowerCase();
    if (text.includes("network")) {
      ElMessage.warning("网络异常，已回退到内置资讯");
    } else {
      ElMessage.warning("已回退到内置资讯");
    }
  }
}

function openNews(item) {
  activeNews.value = item;
  newsDrawerVisible.value = true;
}

function openSource(url) {
  window.open(url, "_blank", "noopener,noreferrer");
}

function getTagClass(category) {
  const text = String(category || "");
  return text.includes("安全") ? "tag-alert" : "tag-public";
}

function formatDate(value) {
  if (!value) return "未知时间";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate()
  ).padStart(2, "0")}`;
}

function renderMarkdown(text) {
  return String(text || "")
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/^###\s+(.*)$/gm, "<h3>$1</h3>")
    .replace(/^##\s+(.*)$/gm, "<h2>$1</h2>")
    .replace(/^#\s+(.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.*)$/gm, "<li>$1</li>")
    .replace(/\n/g, "<br/>");
}

onMounted(loadNews);
onMounted(() => {
  newsRotateTimer = window.setInterval(() => {
    if (!Array.isArray(newsItems.value) || newsItems.value.length <= 1) return;
    const [first, ...rest] = newsItems.value;
    newsItems.value = [...rest, first];
  }, 4500);
});

onBeforeUnmount(() => {
  if (newsRotateTimer) {
    window.clearInterval(newsRotateTimer);
    newsRotateTimer = null;
  }
});
</script>

<style scoped>
.login-page {
  --teal-primary: #1d9e75;
  --teal-light: #9fe1cb;
  --teal-dark: #0f6e56;

  --teal-50: rgba(159, 225, 203, 0.18);
  --teal-100: rgba(159, 225, 203, 0.28);
  --teal-800: #125442;

  --blue-50: rgba(100, 149, 237, 0.14);
  --blue-800: #1d458c;

  --amber-50: rgba(245, 158, 11, 0.16);
  --amber-800: #8a4b00;

  --text-main: #11282c;
  --text-sub: rgba(17, 40, 44, 0.85);
  --text-muted: rgba(17, 40, 44, 0.6);

  /* 核心修复：绝对定位全屏覆盖 */
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  margin: 0;
  
  overflow: hidden;
  box-sizing: border-box;
  padding: 28px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.bg-layer,
.color-wash {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-layer {
  background:
    linear-gradient(rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.18)),
    url("/login-pet-bg.jpg") center center / cover no-repeat;
}

.color-wash {
  background:
    linear-gradient(115deg, rgba(255, 255, 255, 0.72), rgba(235, 250, 247, 0.54) 52%, rgba(239, 246, 255, 0.54)),
    repeating-linear-gradient(135deg, rgba(17, 40, 44, 0.026) 0 1px, transparent 1px 22px);
  backdrop-filter: blur(7px);
}

.login-shell {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1240px;
  min-height: 680px;
  height: min(860px, calc(100vh - 56px));
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(420px, 0.82fr);
  gap: 22px;
}

.column {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.left-col,
.right-col {
  display: grid;
  grid-template-rows: minmax(320px, auto) minmax(360px, 1fr);
}

.glass-panel {
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 24px 64px -44px rgba(17, 40, 44, 0.58), inset 0 1px 0 rgba(255, 255, 255, 0.86);
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.secondary-glass {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.primary-glass {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}

.scroll-card {
  flex: none;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.card-title {
  color: var(--text-main);
  font-size: 19px;
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.card-subtitle {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
}

.header-chip {
  flex-shrink: 0;
  height: 28px;
  padding: 0 14px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--teal-dark);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 1);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  font-size: 12px;
  font-weight: 600;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--teal-dark);
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.hero-copy h1 {
  margin: 18px 0 0;
  color: var(--text-main);
  font-size: 30px;
  line-height: 1.35;
  font-weight: 600;
  letter-spacing: 0;
}

.project-signature {
  margin-top: 10px;
  color: #0f766e;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0;
}

.hero-copy p {
  margin: 14px 0 0;
  color: var(--text-sub);
  font-size: 14px;
  line-height: 1.7;
}

.hero-metrics {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.metric-card {
  min-width: 0;
  padding: 16px 18px;
}

.metric-card + .metric-card {
  border-left: 1px solid rgba(255, 255, 255, 0.4);
}

.metric-label {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
}

.metric-card strong {
  display: block;
  margin-top: 6px;
  color: var(--teal-primary);
  font-size: 24px;
  font-weight: 600;
}

.metric-note {
  display: block;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 11px;
}

.news-panel,
.quick-panel {
  min-height: 0;
  height: 100%;
}

.news-scroll,
.quick-grid {
  min-height: 0;
  flex: none;
  overflow: auto;
  padding-right: 6px;
  max-height: 260px;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(29, 158, 117, 0.2);
  border-radius: 999px;
}

.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: rgba(29, 158, 117, 0.4);
}

.news-list {
  display: flex;
  flex-direction: column;
}

.news-item {
  appearance: none;
  border: none;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background: transparent;
  text-align: left;
  padding: 14px 10px;
  margin: 0 -10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.news-item:first-child {
  padding-top: 10px;
}

.news-item:hover {
  background: rgba(255, 255, 255, 0.56);
}

.news-top,
.news-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.news-title {
  margin-top: 8px;
  color: var(--text-main);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
}

.news-summary {
  margin-top: 6px;
  color: var(--text-sub);
  font-size: 13px;
  line-height: 1.6;
}

.news-meta {
  margin-top: 10px;
}

.news-date {
  color: var(--text-muted);
  font-size: 12px;
}

.meta-source {
  color: var(--text-muted);
  font-size: 12px;
}

.view-detail {
  color: var(--teal-primary);
  font-size: 12px;
  font-weight: 600;
}

.news-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 22px;
  padding: 0 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.tag-public {
  background: var(--teal-50);
  color: var(--teal-800);
}

.tag-alert {
  background: var(--amber-50);
  color: var(--amber-800);
}

.refresh-btn {
  padding: 0;
  color: var(--teal-primary);
  font-weight: 600;
  border: none !important;
  background: transparent !important;
}

.refresh-btn:hover {
  color: var(--teal-dark);
}

.login-form {
  margin-top: 16px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.login-form :deep(.el-form-item__label) {
  color: var(--text-main);
  font-size: 14px;
  font-weight: 600;
  padding-bottom: 6px;
}

.login-form :deep(.el-input__wrapper),
.login-form :deep(.el-select__wrapper) {
  min-height: 46px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72) !important;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
  transition: all 0.2s ease;
}

.login-form :deep(.el-input__wrapper:hover),
.login-form :deep(.el-select__wrapper:hover) {
  background: rgba(255, 255, 255, 0.8) !important;
  border-color: rgba(29, 158, 117, 0.4);
}

.login-form :deep(.el-input__wrapper.is-focus),
.login-form :deep(.el-select__wrapper.is-focused) {
  background: #ffffff !important;
  border-color: var(--teal-primary) !important;
  box-shadow: 0 0 0 3px rgba(29, 158, 117, 0.15) !important;
}

.login-form :deep(.el-input__inner),
.login-form :deep(.el-select__placeholder),
.login-form :deep(.el-select__selected-item) {
  color: var(--text-main);
  font-size: 14px;
}

.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 12px;
  border: none !important;
  border-radius: 8px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  background: var(--teal-primary) !important;
  box-shadow: 0 4px 14px rgba(29, 158, 117, 0.3) !important;
  transition: all 0.2s ease;
}

.submit-btn:hover {
  background: var(--teal-dark) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(29, 158, 117, 0.4) !important;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.quick-item {
  position: relative;
  text-align: left;
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-item::before {
  content: "";
  position: absolute;
  left: 0;
  top: 14px;
  bottom: 14px;
  width: 4px;
  border-radius: 0 4px 4px 0;
  background: transparent;
  transition: background 0.2s ease;
}

.quick-item:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(255, 255, 255, 1);
  box-shadow: 0 6px 16px rgba(0,0,0,0.05);
}

.quick-item:hover::before {
  background: var(--teal-primary);
}

.quick-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-badge {
  height: 20px;
  padding: 0 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
}

.badge-teal { background: var(--teal-50); color: var(--teal-800); }
.badge-blue { background: var(--blue-50); color: var(--blue-800); }
.badge-amber { background: var(--amber-50); color: var(--amber-800); }

.quick-name {
  color: var(--text-main);
  font-size: 14px;
  font-weight: 600;
}

.quick-desc {
  display: block;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.5;
}

.tips-carousel {
  margin-top: 16px;
}

.tip-slide {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 16px;
  height: 100%;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  overflow: hidden;
}

.tip-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tip-content {
  padding: 16px 16px 16px 0;
}

.tip-title {
  color: var(--text-main);
  font-size: 15px;
  font-weight: 600;
}

.tip-text {
  margin-top: 8px;
  color: var(--text-sub);
  font-size: 13px;
  line-height: 1.6;
}

.news-thumb-wrap { margin-bottom: 10px; }
.news-thumb {
  width: 100%;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
}

/* 响应式降级策略 */
@media (max-width: 1180px) {
  .login-page {
    position: relative; /* 解除 absolute 限制，允许小屏滚动 */
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
    padding: 24px;
  }

  .login-shell {
    height: auto;
    grid-template-columns: 1fr;
  }

  .column { min-height: auto; }
  .scroll-card { flex: none; }
  .news-scroll, .quick-grid {
    overflow: visible;
    max-height: none;
  }
}

@media (max-width: 768px) {
  .glass-panel {
    padding: 16px;
    border-radius: 12px;
  }
  .hero-copy h1 { font-size: 26px; }
  .hero-metrics { grid-template-columns: 1fr; }
  .metric-card + .metric-card {
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.4);
  }
  .quick-grid { grid-template-columns: 1fr; }
  .tip-slide {
    grid-template-columns: 1fr;
    height: auto;
  }
  .tip-image { display: none; }
  .tip-content { padding: 16px; }
}
</style>
