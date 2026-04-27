<template>
  <div class="page layout-bg">
    <el-card class="glass-card main-card">
      <template #header>
        <div class="header-row">
          <span class="page-title">🗂️ 档案管理中心</span>
          <el-space>
            <el-button class="agile-btn btn-ghost" :loading="tableLoading" :disabled="tableLoading" @click="initializePage">
              <span class="btn-text">🔄 刷新</span>
            </el-button>
            <el-button class="agile-btn btn-primary" :disabled="tableLoading" @click="openCreateOwner">
              <span class="btn-text">👤 新建主人</span>
            </el-button>
            <el-button class="agile-btn btn-success" :disabled="tableLoading" @click="openCreatePet">
              <span class="btn-text">🐾 新建宠物</span>
            </el-button>
          </el-space>
        </div>
      </template>
      
      <el-breadcrumb separator="/" class="cute-breadcrumb">
        <el-breadcrumb-item @click="router.push('/home')">🏠 首页</el-breadcrumb-item>
        <el-breadcrumb-item>档案管理</el-breadcrumb-item>
      </el-breadcrumb>

      <el-skeleton :loading="tableLoading" :rows="6" animated class="cute-skeleton">
        <template #default>
          <transition name="slide-fade">
            <el-alert v-if="loadError" type="error" :title="loadError" show-icon :closable="false" class="agile-alert mb16">
              <template #default>
                <el-button size="small" class="agile-btn-small" @click="initializePage">重试</el-button>
              </template>
            </el-alert>
          </transition>

          <div class="search-bar-container">
            <el-input
              v-model="petSearchKeyword"
              placeholder="🔍 搜索宠物名称 / 编码..."
              clearable
              class="agile-input search-input"
            />
            <transition name="bounce">
              <el-space v-if="petSearchKeyword" class="filter-tags">
                <el-tag closable round effect="light" type="primary" class="cute-tag" @close="petSearchKeyword = ''">
                  关键词：<strong>{{ petSearchKeyword }}</strong>
                </el-tag>
                <el-button text class="agile-text-btn" @click="petSearchKeyword = ''">清空筛选</el-button>
              </el-space>
            </transition>
          </div>

          <div class="view-mode-bar">
            <el-radio-group v-model="petViewMode" size="small">
              <el-radio-button label="table">表格视图</el-radio-button>
              <el-radio-button label="card">卡片视图</el-radio-button>
            </el-radio-group>
          </div>
          <el-tabs v-model="activeTab" class="cute-tabs">
            
            <el-tab-pane label="👤 主人档案" name="owners">
              <el-table :data="owners" class="cute-table" :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: '800' }">
                <el-table-column prop="id" label="ID" width="80">
                  <template #default="{ row }"><span class="fw-bold text-sub">#{{ row.id }}</span></template>
                </el-table-column>
                <el-table-column prop="owner_code" label="主人编码" min-width="200">
                  <template #default="{ row }">
                    <div class="code-cell">
                      <el-input :model-value="row.owner_code" readonly class="code-input" />
                      <el-button size="small" class="agile-btn-small btn-copy" @click="copyText(row.owner_code)">复制</el-button>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="姓名">
                  <template #default="{ row }"><span class="fw-bold">{{ row.name }}</span></template>
                </el-table-column>
                <el-table-column prop="phone" label="手机号" />
                <el-table-column prop="member_level" label="会员等级">
                  <template #default="{ row }">
                    <el-tag round :type="row.member_level === 'diamond' ? 'danger' : row.member_level === 'gold' ? 'warning' : 'info'" effect="light" class="vip-tag">
                      {{ row.member_level === 'diamond' ? '💎 钻石' : row.member_level === 'gold' ? '👑 黄金' : '普通' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="180" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" class="agile-btn-small btn-ghost" :disabled="actionLoading" @click="openEditOwner(row)">编辑</el-button>
                    <el-button size="small" class="agile-btn-small btn-danger" :loading="deletingOwnerId === row.id" :disabled="actionLoading" @click="removeOwner(row.id)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="list-meta">
                共 <span class="meta-highlight">{{ owners.length }}</span> 条主人记录，最后更新于 {{ lastUpdated || "--:--" }}
              </div>
            </el-tab-pane>

            <el-tab-pane label="🐾 宠物档案" name="pets">
              <el-empty v-if="filteredPets.length === 0" description="呜呜，未检索到该宠物的档案" :image-size="120">
                <el-button class="agile-btn btn-primary" @click="openCreatePet">✨ 立即新建档案</el-button>
              </el-empty>
              <el-table
                v-else-if="petViewMode === 'table'"
                :data="filteredPets"
                class="cute-table"
                :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: '800' }"
              >
                <el-table-column prop="id" label="ID" width="80">
                  <template #default="{ row }"><span class="fw-bold text-sub">#{{ row.id }}</span></template>
                </el-table-column>
                <el-table-column prop="pet_code" label="宠物编码" min-width="200">
                  <template #default="{ row }">
                    <div class="code-cell">
                      <el-input :model-value="row.pet_code" readonly class="code-input" />
                      <el-button size="small" class="agile-btn-small btn-copy" @click="copyText(row.pet_code)">复制</el-button>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="宠物名称" min-width="180">
                  <template #default="{ row }">
                    <div class="pet-name-cell">
                      <span class="fw-bold text-primary">{{ row.name }}</span>
                      <el-tag v-if="(row.allergy_history || []).length > 0" type="danger" effect="dark" round size="small" class="allergy-badge">
                        🚨 过敏史
                      </el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="species" label="物种" width="90">
                  <template #default="{ row }">
                    <span class="species-icon">{{ row.species === '犬' ? '🐶' : row.species === '猫' ? '🐱' : row.species === '兔' ? '🐰' : row.species === '鸟' ? '🦜' : '🦎' }}</span> {{ row.species }}
                  </template>
                </el-table-column>
                <el-table-column prop="clinic_id" label="院区" width="100">
                  <template #default="{ row }"><el-tag effect="light" type="info" round class="clinic-tag">{{ row.clinic_id }}</el-tag></template>
                </el-table-column>
                <el-table-column label="体重(kg)" width="100">
                  <template #default="{ row }">
                    <span :class="['weight-text', getWeightTextType(row.weight)]">{{ row.weight ?? "-" }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="过敏史" min-width="150">
                  <template #default="{ row }">
                    <span class="allergy-text">{{ (row.allergy_history || []).join("、") || "-" }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="220" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" class="agile-btn-small btn-primary-light" :disabled="actionLoading" @click="openPetDetail(row)">详情</el-button>
                    <el-button size="small" class="agile-btn-small btn-ghost" :disabled="actionLoading" @click="openEditPet(row)">编辑</el-button>
                    <el-button size="small" class="agile-btn-small btn-danger" :loading="deletingPetId === row.id" :disabled="actionLoading" @click="removePet(row.id)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div v-else class="pet-card-grid">
                <div v-for="row in filteredPets" :key="row.id" class="pet-card-item">
                  <div class="pet-card-head">
                    <div class="fw-bold text-primary">{{ row.name }}</div>
                    <el-tag size="small" type="info">{{ row.clinic_id }}</el-tag>
                  </div>
                  <div class="pet-card-meta">{{ row.species }} / {{ row.breed || "-" }} / {{ row.birth_date || "-" }}</div>
                  <div class="pet-card-meta">主人ID #{{ row.owner_id }} · 体重 {{ row.weight ?? "-" }}kg</div>
                  <div class="pet-card-actions">
                    <el-button size="small" class="agile-btn-small btn-primary-light" @click="openPetDetail(row)">详情</el-button>
                    <el-button size="small" class="agile-btn-small btn-ghost" @click="openEditPet(row)">编辑</el-button>
                  </div>
                </div>
              </div>
              <div class="list-meta">共 <span class="meta-highlight">{{ filteredPets.length }}</span> 条宠物记录，最后更新于 {{ lastUpdated || "--:--" }}</div>
            </el-tab-pane>
          </el-tabs>
        </template>
      </el-skeleton>
    </el-card>

    <transition name="slide-up">
      <el-alert v-if="undoBar.visible" class="agile-alert undo-bar" :title="undoBar.title" type="warning" show-icon :closable="false">
        <template #default><el-button class="agile-btn-small" style="margin-left: 16px" @click="undoAction">↩️ 立即撤销</el-button></template>
      </el-alert>
    </transition>

    <el-dialog v-model="ownerDialogVisible" :title="ownerEditingId ? '📝 编辑主人档案' : '👤 新建主人档案'" width="600px" class="glass-dialog">
      <el-form ref="ownerFormRef" :model="ownerForm" :rules="ownerRules" label-width="100px" label-position="left" class="modern-form">
        <el-form-item label="主人编码" prop="owner_code">
          <el-input v-model="ownerForm.owner_code" :readonly="Boolean(ownerEditingId)" class="agile-input code-font" />
        </el-form-item>
        <el-form-item label="姓名" prop="name"><el-input v-model="ownerForm.name" class="agile-input" placeholder="请输入姓名" /></el-form-item>
        <el-form-item label="手机号" prop="phone"><el-input v-model="ownerForm.phone" class="agile-input" placeholder="请输入联系电话" /></el-form-item>
        <el-form-item label="证件号"><el-input v-model="ownerForm.id_card" class="agile-input" placeholder="选填" /></el-form-item>
        <el-form-item label="居住地址"><el-input v-model="ownerForm.address" class="agile-input" placeholder="选填" /></el-form-item>
        <el-form-item label="会员等级" prop="member_level">
          <el-select v-model="ownerForm.member_level" class="agile-input fluid-select">
            <el-option label="普通会员" value="normal" />
            <el-option label="👑 黄金会员" value="gold" />
            <el-option label="💎 钻石会员" value="diamond" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="agile-btn btn-ghost" :disabled="ownerSubmitting" @click="ownerDialogVisible = false">取消</el-button>
          <el-button class="agile-btn btn-primary" :loading="ownerSubmitting" :disabled="ownerSubmitting" @click="submitOwner">💾 保存档案</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="petDialogVisible" :title="petEditingId ? '📝 编辑宠物档案' : '🐾 新建宠物档案'" width="680px" class="glass-dialog">
      <el-form ref="petFormRef" :model="petForm" :rules="petRules" label-width="110px" label-position="left" class="modern-form">
        <el-form-item label="宠物名称" prop="name"><el-input v-model="petForm.name" class="agile-input" placeholder="例如：白之助" /></el-form-item>
        <div class="form-row-2">
          <el-form-item label="物种" prop="species" style="flex: 1">
            <el-select v-model="petForm.species" placeholder="请选择" class="agile-input fluid-select">
              <el-option v-for="item in PET_SPECIES_OPTIONS" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="性别" style="flex: 1">
            <el-select v-model="petForm.gender" class="agile-input fluid-select">
              <el-option label="♂️ 公" value="公" />
              <el-option label="♀️ 母" value="母" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="品种"><el-input v-model="petForm.breed" class="agile-input" placeholder="例如：拉布拉多" /></el-form-item>
        <div class="form-row-2">
          <el-form-item label="出生日期" prop="birth_date" style="flex: 1">
            <el-date-picker v-model="petForm.birth_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" class="agile-input fluid-select" :editable="false" />
          </el-form-item>
          <el-form-item prop="weight" style="flex: 1">
            <template #label>
              <div class="label-help">体重(kg)
                <el-tooltip content="常见范围：0.2 - 120kg" placement="top"><span class="help-icon">?</span></el-tooltip>
              </div>
            </template>
            <el-input-number v-model="petForm.weight" :min="0.1" :max="200" :step="0.1" class="agile-input fluid-select" />
          </el-form-item>
        </div>
        <transition name="bounce">
          <el-alert v-if="showWeightWarning" type="warning" :closable="false" title="⚠️ 当前体重超出常见范围，请确认输入是否正确。" class="agile-alert mb16" />
        </transition>
        <el-form-item label="所属主人" prop="owner_id">
          <el-select v-model="petForm.owner_id" filterable placeholder="搜索或选择主人" class="agile-input fluid-select">
            <el-option v-for="owner in owners" :key="owner.id" :label="`${owner.name} (#${owner.id})`" :value="owner.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属院区" prop="clinic_id">
          <el-select v-model="petForm.clinic_id" placeholder="请选择" class="agile-input fluid-select">
            <el-option label="C001 沙河口" value="C001" />
            <el-option label="C002 甘井子" value="C002" />
            <el-option label="C003 高新园区" value="C003" />
          </el-select>
        </el-form-item>
        <el-form-item label="过敏史">
          <el-input v-model="petAllergyText" type="textarea" :rows="2" placeholder="无过敏史可留空；多个过敏项请用英文逗号分隔，如：青霉素,牛肉" class="agile-input" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="agile-btn btn-ghost" :disabled="petSubmitting" @click="petDialogVisible = false">取消</el-button>
          <el-button class="agile-btn btn-success" :loading="petSubmitting" :disabled="petSubmitting" @click="submitPet">💾 保存档案</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="petDetailVisible" title="🏥 宠物综合详情" width="760px" class="glass-dialog">
      <el-tabs v-model="petDetailTab" class="cute-tabs detail-tabs">
        <el-tab-pane label="📋 基础信息" name="base">
          <el-descriptions :column="2" border class="cute-descriptions">
            <el-descriptions-item label="宠物编码"><span class="code-font">{{ selectedPet?.pet_code || "-" }}</span></el-descriptions-item>
            <el-descriptions-item label="名称">
              <div class="pet-name-cell">
                <span class="fw-bold text-primary">{{ selectedPet?.name || "-" }}</span>
                <el-tag v-if="(selectedPet?.allergy_history || []).length > 0" type="danger" effect="dark" round size="small" class="allergy-badge">
                  🚨 过敏史
                </el-tag>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="物种">{{ selectedPet?.species || "-" }}</el-descriptions-item>
            <el-descriptions-item label="品种">{{ selectedPet?.breed || "-" }}</el-descriptions-item>
            <el-descriptions-item label="出生日期">{{ selectedPet?.birth_date || "-" }}</el-descriptions-item>
            <el-descriptions-item label="过敏史"><span class="allergy-text fw-bold">{{ (selectedPet?.allergy_history || []).join("、") || "无" }}</span></el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        
        <el-tab-pane label="📖 历史就诊记录" name="history">
          <el-skeleton :loading="petDetailLoading" :rows="4" animated class="cute-skeleton">
            <template #default>
              <el-timeline class="cute-timeline">
                <el-timeline-item
                  v-for="item in petTimeline"
                  :key="item.key"
                  :timestamp="item.time"
                  :type="item.type"
                  placement="top"
                  hollow
                >
                  <el-card shadow="hover" class="timeline-card">
                    <div class="timeline-title">{{ item.title }}</div>
                    <div class="timeline-desc">{{ item.description }}</div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-if="petTimeline.length === 0" description="非常健康，暂无历史就诊记录" :image-size="80" />
            </template>
          </el-skeleton>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
// ==========================================
// 逻辑代码层 (完全保持不变)
// ==========================================
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";

import { fetchAppointments } from "../api/appointments";
import { createOwner, deleteOwner, fetchOwners, updateOwner } from "../api/owners";
import { createPet, deletePet, fetchPets, updatePet } from "../api/pets";
import { fetchMedicalRecords } from "../api/vetWorkbench";
import { PET_SPECIES_OPTIONS } from "../constants/petSpecies";
import { getErrorMessage } from "../utils/status";

const activeTab = ref("owners");
const petViewMode = ref("table");
const router = useRouter();
const owners = ref([]);
const pets = ref([]);
const petSearchKeyword = ref("");
const tableLoading = ref(false);
const actionLoading = ref(false);
const loadError = ref("");
const deletingOwnerId = ref(null);
const deletingPetId = ref(null);
const lastUpdated = ref("");
const undoBar = ref({ visible: false, title: "", payload: null });
let undoTimer = null;

const ownerDialogVisible = ref(false);
const ownerSubmitting = ref(false);
const ownerEditingId = ref(null);
const ownerFormRef = ref(null);
const ownerForm = ref({ owner_code: "", name: "", phone: "", id_card: "", address: "", member_level: "normal" });

const petDialogVisible = ref(false);
const petDetailVisible = ref(false);
const petDetailLoading = ref(false);
const petDetailTab = ref("base");
const selectedPet = ref(null);
const petTimeline = ref([]);
const petSubmitting = ref(false);
const petEditingId = ref(null);
const petAllergyText = ref("");
const petFormRef = ref(null);
const petForm = ref({ name: "", species: "犬", breed: "", gender: "公", birth_date: "", weight: null, owner_id: null, clinic_id: "C001", allergy_history: [] });

const ownerRules = {
  owner_code: [{ required: true, message: "请填写主人编码", trigger: "blur" }],
  name: [{ required: true, message: "请填写姓名", trigger: "blur" }],
  phone: [{ required: true, message: "请填写手机号", trigger: "blur" }],
  member_level: [{ required: true, message: "请选择会员等级", trigger: "change" }]
};

const petRules = {
  name: [{ required: true, message: "请填写宠物名称", trigger: "blur" }],
  species: [{ required: true, message: "请选择物种", trigger: "change" }],
  owner_id: [{ required: true, message: "请选择主人", trigger: "change" }],
  clinic_id: [{ required: true, message: "请选择院区", trigger: "change" }],
  birth_date: [{ required: true, message: "请选择出生日期", trigger: "change" }]
};

const showWeightWarning = computed(() => { const w = petForm.value.weight; if (w === null || w === undefined) return false; return w > 120 || w < 0.2; });
const filteredPets = computed(() => { const key = petSearchKeyword.value.trim(); if (!key) return pets.value; return (pets.value || []).filter((item) => { const name = item.name || ""; const code = item.pet_code || ""; return name.includes(key) || code.includes(key); }); });

function getWeightTextType(weight) { if (weight === null || weight === undefined) return ""; if (weight > 120 || weight < 0.2) return "warning"; return ""; }
async function copyText(value) { try { await navigator.clipboard.writeText(value); ElMessage.success("已复制"); } catch { ElMessage.warning("复制失败，请手动复制"); } }

async function loadOwners() { const result = await fetchOwners(); owners.value = result.data || []; }
async function loadPets() { const result = await fetchPets(); pets.value = result.data || []; }

async function initializePage() {
  tableLoading.value = true; loadError.value = "";
  try { await Promise.all([loadOwners(), loadPets()]); lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }); }
  catch (error) { const message = getErrorMessage(error, "档案数据加载失败"); loadError.value = message; ElMessage.error(message); }
  finally { tableLoading.value = false; }
}

function showUndo(title, payload) { if (undoTimer) window.clearTimeout(undoTimer); undoBar.value = { visible: true, title, payload }; undoTimer = window.setTimeout(() => { undoBar.value.visible = false; }, 5000); }

function openCreateOwner() { ownerEditingId.value = null; ownerForm.value = { owner_code: "", name: "", phone: "", id_card: "", address: "", member_level: "normal" }; ownerDialogVisible.value = true; }
function openEditOwner(row) { ownerEditingId.value = row.id; ownerForm.value = { owner_code: row.owner_code, name: row.name, phone: row.phone, id_card: row.id_card || "", address: row.address || "", member_level: row.member_level || "normal" }; ownerDialogVisible.value = true; }

async function submitOwner() {
  if (!ownerFormRef.value) return; await ownerFormRef.value.validate(); ownerSubmitting.value = true; actionLoading.value = true;
  try {
    if (ownerEditingId.value) { await updateOwner(ownerEditingId.value, { name: ownerForm.value.name, phone: ownerForm.value.phone, id_card: ownerForm.value.id_card, address: ownerForm.value.address, member_level: ownerForm.value.member_level }); ElMessage.success("主人档案更新成功"); }
    else { await createOwner(ownerForm.value); ElMessage.success("主人档案创建成功"); }
    ownerDialogVisible.value = false; await loadOwners();
  } catch (error) { ElMessage.error(getErrorMessage(error, "主人档案保存失败")); }
  finally { ownerSubmitting.value = false; actionLoading.value = false; }
}

async function removeOwner(id) {
  try { await ElMessageBox.confirm("删除后不可恢复，确认删除该主人档案？", "删除确认", { type: "warning", confirmButtonText: "确认删除", confirmButtonClass: "el-button--danger", cancelButtonText: "取消" }); } catch { return; }
  deletingOwnerId.value = id; actionLoading.value = true;
  try { await deleteOwner(id); ElMessage.success("主人档案已删除"); showUndo("主人档案已删除，可在5秒内撤销", { type: "owner_delete", backup: owners.value.find((x) => x.id === id) }); await loadOwners(); }
  catch (error) { ElMessage.error(getErrorMessage(error, "删除主人失败")); }
  finally { deletingOwnerId.value = null; actionLoading.value = false; }
}

function openCreatePet() { petEditingId.value = null; petAllergyText.value = ""; petForm.value = { name: "", species: "犬", breed: "", gender: "公", birth_date: "", weight: null, owner_id: owners.value[0]?.id ?? null, clinic_id: "C001", allergy_history: [] }; petDialogVisible.value = true; }
function openEditPet(row) { petEditingId.value = row.id; petForm.value = { name: row.name, species: row.species, breed: row.breed || "", gender: row.gender || "公", birth_date: row.birth_date || "", weight: row.weight, owner_id: row.owner_id, clinic_id: row.clinic_id, allergy_history: row.allergy_history || [] }; petAllergyText.value = (row.allergy_history || []).join(","); petDialogVisible.value = true; }
function buildAllergyHistory() { return petAllergyText.value.split(",").map((item) => item.trim()).filter((item) => item.length > 0); }

async function submitPet() {
  if (!petFormRef.value) return; await petFormRef.value.validate(); petSubmitting.value = true; actionLoading.value = true;
  try {
    const payload = { ...petForm.value, allergy_history: buildAllergyHistory() };
    if (petEditingId.value) { await updatePet(petEditingId.value, payload); ElMessage.success("宠物档案更新成功"); }
    else { await createPet(payload); ElMessage.success("宠物档案创建成功"); }
    petDialogVisible.value = false; await loadPets();
  } catch (error) { ElMessage.error(getErrorMessage(error, "宠物档案保存失败")); }
  finally { petSubmitting.value = false; actionLoading.value = false; }
}

async function removePet(id) {
  try { await ElMessageBox.confirm("删除后不可恢复，确认删除该宠物档案？", "删除确认", { type: "warning", confirmButtonText: "确认删除", confirmButtonClass: "el-button--danger", cancelButtonText: "取消" }); } catch { return; }
  deletingPetId.value = id; actionLoading.value = true;
  try { await deletePet(id); ElMessage.success("宠物档案已删除"); showUndo("宠物档案已删除，可在5秒内撤销", { type: "pet_delete", backup: pets.value.find((x) => x.id === id) }); await loadPets(); }
  catch (error) { ElMessage.error(getErrorMessage(error, "删除宠物失败")); }
  finally { deletingPetId.value = null; actionLoading.value = false; }
}

async function undoAction() {
  const payload = undoBar.value.payload; if (!payload?.backup) return;
  try {
    if (payload.type === "owner_delete") {
      const b = payload.backup; await createOwner({ owner_code: b.owner_code, name: b.name, phone: b.phone, id_card: b.id_card, address: b.address, member_level: b.member_level });
      await loadOwners(); ElMessage.success("主人档案已恢复");
    }
    if (payload.type === "pet_delete") {
      const b = payload.backup; await createPet({ name: b.name, species: b.species, breed: b.breed, gender: b.gender, birth_date: b.birth_date, weight: b.weight, allergy_history: b.allergy_history || [], owner_id: b.owner_id, clinic_id: b.clinic_id });
      await loadPets(); ElMessage.success("宠物档案已恢复");
    }
  } catch (error) { ElMessage.error(getErrorMessage(error, "撤销失败")); }
  finally { undoBar.value.visible = false; }
}

async function openPetDetail(row) {
  selectedPet.value = row; petDetailVisible.value = true; petDetailTab.value = "base"; petDetailLoading.value = true;
  try {
    const [appointmentRes, medicalRes] = await Promise.all([fetchAppointments({ petId: row.id }), fetchMedicalRecords(row.id)]);
    const appointmentTimeline = (appointmentRes.data || []).map((item) => ({
      key: `ap-${item.id}`, time: (item.scheduled_time || "").replace("T", " ").slice(0, 19), type: item.urgency_level === "急诊" ? "danger" : "primary", title: `挂号 ${item.record_code}`, description: `紧急程度：${item.urgency_level}；状态：${item.status}`
    }));
    const medicalTimeline = (medicalRes.data || []).map((item) => ({
      key: `mr-${item.id}`, time: (item.created_at || "").replace("T", " ").slice(0, 19), type: "success", title: `病历 ${item.record_no}`, description: `${item.chief_complaint || "无主诉"}；${item.exam_notes || "无检查记录"}`
    }));
    petTimeline.value = [...appointmentTimeline, ...medicalTimeline].sort((a, b) => String(b.time).localeCompare(String(a.time)));
  } catch (error) { ElMessage.error(getErrorMessage(error, "历史记录加载失败")); petTimeline.value = []; }
  finally { petDetailLoading.value = false; }
}

onMounted(async () => { await initializePage(); });
</script>

<style scoped>
/* ====================================================
   全局变量与基础设定 (Spring 物理曲线)
   ==================================================== */
:root {
  --primary: #3B82F6;
  --primary-hover: #2563EB;
  --success: #10B981;
  --warning: #F59E0B;
  --danger: #EF4444;
  --bg-page: #F8FAFC;
  --surface: #FFFFFF;
  --text-main: #1E293B;
  --text-sub: #64748B;
  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --smooth: cubic-bezier(0.4, 0, 0.2, 1);
}

.layout-bg {
  background-color: var(--bg-page);
  min-height: 100vh;
  padding: 24px;
  font-family: 'Nunito', ui-rounded, 'Hiragino Maru Gothic ProN', 'PingFang SC', sans-serif;
}

.fw-bold { font-weight: 800; }
.text-primary { color: var(--primary); }
.text-sub { color: #94A3B8; }
.mb16 { margin-bottom: 16px; }

/* ====================================================
   玻璃态主卡片 & 标题栏
   ==================================================== */
:deep(.glass-card) {
  border-radius: 20px !important; border: 1px solid rgba(226, 232, 240, 0.8) !important;
  box-shadow: 0 20px 40px -10px rgba(15, 23, 42, 0.05), 0 10px 15px -5px rgba(15, 23, 42, 0.02) !important;
  background: var(--surface); overflow: visible;
}
:deep(.glass-card > .el-card__header) {
  background: linear-gradient(to right, #FFFFFF, #F8FAFC); border-bottom: 1px solid #F1F5F9;
  padding: 20px 24px; border-radius: 20px 20px 0 0;
}
.header-row { display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 22px; font-weight: 800; color: var(--text-main); letter-spacing: 0.5px; }

.cute-breadcrumb { margin-bottom: 20px; font-weight: 700; padding: 0 4px; }

/* ====================================================
   搜索栏与过滤器
   ==================================================== */
.search-bar-container { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.view-mode-bar { display: flex; justify-content: flex-end; margin-bottom: 8px; }
.search-input { max-width: 340px; }
.filter-tags { display: flex; align-items: center; }
.cute-tag { border-radius: 12px; padding: 0 12px; height: 32px; line-height: 30px; font-weight: 600; border: none; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.1); }
.agile-text-btn { font-weight: 700; color: #64748B; transition: color 0.2s; }
.agile-text-btn:hover { color: var(--danger); background: transparent; }

/* ====================================================
   灵动选项卡 (Floating Tabs)
   ==================================================== */
:deep(.cute-tabs .el-tabs__nav-wrap::after) { height: 0; /* 隐藏底部硬边框 */ }
:deep(.cute-tabs .el-tabs__active-bar) { display: none; /* 隐藏默认底部蓝条 */ }
:deep(.cute-tabs .el-tabs__item) {
  font-size: 15px; font-weight: 800; color: #64748B; padding: 0 20px !important; height: 44px; line-height: 44px;
  border-radius: 12px; margin-right: 8px; transition: all 0.3s var(--spring);
}
:deep(.cute-tabs .el-tabs__item:hover) { color: var(--primary); background-color: #F8FAFC; }
:deep(.cute-tabs .el-tabs__item.is-active) { color: var(--primary); background-color: #EFF6FF; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15); }

/* ====================================================
   可爱的数据表格
   ==================================================== */
:deep(.cute-table) { border-radius: 16px; overflow: hidden; border: 1px solid #F1F5F9; --el-table-border-color: #F1F5F9; margin-top: 12px; }
:deep(.cute-table .el-table__row) { transition: background-color 0.3s var(--smooth); }
:deep(.cute-table .el-table__row:hover > td) { background-color: #F8FAFC !important; }

/* 表格内元素深度定制 */
.code-cell { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center; }
:deep(.code-input .el-input__wrapper) { border-radius: 8px !important; box-shadow: none !important; background: transparent; padding: 0; }
:deep(.code-input .el-input__inner) { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #64748B; }

.pet-name-cell { display: inline-flex; align-items: center; gap: 8px; }
.allergy-badge { font-weight: 800; box-shadow: 0 2px 6px rgba(239, 68, 68, 0.3); border: none; }
.vip-tag { font-weight: 800; padding: 0 12px; border: none; }
.clinic-tag { font-weight: 800; border: none; background: #F1F5F9; color: #475569;}
.species-icon { font-size: 16px; margin-right: 4px; }
.weight-text { font-weight: 700; color: #475569; }
.weight-text.warning { color: var(--danger); }
.allergy-text { color: #DC2626; font-weight: 600; }
.pet-card-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.pet-card-item { border: 1px solid #e5e7eb; border-radius: 12px; padding: 10px; background: #fff; }
.pet-card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.pet-card-meta { margin-top: 6px; font-size: 12px; color: #64748b; }
.pet-card-actions { margin-top: 10px; display: flex; gap: 8px; }

.list-meta { margin-top: 16px; color: #94A3B8; font-size: 13px; font-weight: 600; text-align: right; }
.meta-highlight { color: var(--primary); font-weight: 800; font-size: 15px; }

/* ====================================================
   果冻态弹窗与表单 (Jelly Dialogs)
   ==================================================== */
:deep(.glass-dialog) { border-radius: 24px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); }
:deep(.glass-dialog .el-dialog__header) { background-color: #F8FAFC; margin-right: 0; padding: 20px 24px; border-bottom: 1px solid #F1F5F9; font-weight: 800; }
:deep(.glass-dialog .el-dialog__title) { font-weight: 800; font-size: 18px; color: var(--text-main); }
.dialog-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 10px 0; }

.modern-form { padding: 10px 0; }
:deep(.el-form-item__label) { font-weight: 800; color: var(--text-main); }
.form-row-2 { display: flex; gap: 16px; width: 100%; }

.label-help { display: inline-flex; align-items: center; gap: 6px; }
.help-icon { width: 16px; height: 16px; border-radius: 50%; background-color: #CBD5E1; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; cursor: pointer; transition: background 0.2s; }
.help-icon:hover { background-color: var(--primary); }

/* ====================================================
   深度定制下拉与输入框
   ==================================================== */
:deep(.agile-input .el-input__wrapper), :deep(.agile-input .el-textarea__inner) {
  border-radius: 12px !important; background-color: #F8FAFC; box-shadow: 0 0 0 1px #E2E8F0 inset !important; transition: all 0.3s var(--spring) !important;
}
:deep(.agile-input .el-input__wrapper.is-focus), :deep(.agile-input .el-textarea__inner:focus) {
  background-color: #FFFFFF; box-shadow: 0 0 0 2px var(--primary) inset, 0 4px 12px rgba(59, 130, 246, 0.1) !important;
}
.fluid-select { width: 100%; }
:deep(.code-font .el-input__inner) { font-family: 'JetBrains Mono', monospace; color: #64748B; }

/* ====================================================
   Q弹交互按钮
   ==================================================== */
.agile-btn {
  border-radius: 100px !important; height: 40px !important; font-weight: 800 !important; padding: 0 20px !important;
  transition: all 0.3s var(--spring) !important; border: none !important;
}
.btn-primary { background-color: #3B82F6 !important; color: #FFF !important; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3) !important; }
.btn-primary:hover:not(:disabled) { transform: translateY(-2px) scale(1.02) !important; box-shadow: 0 6px 14px rgba(59, 130, 246, 0.4) !important; background-color: #2563EB !important; }
.btn-primary:disabled { background-color: #E2E8F0 !important; color: #94A3B8 !important; box-shadow: none !important; cursor: not-allowed !important; }

.btn-success { background-color: #10B981 !important; color: #FFF !important; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3) !important; }
.btn-success:hover:not(:disabled) { transform: translateY(-2px) scale(1.02) !important; background-color: #059669 !important; box-shadow: 0 6px 14px rgba(16, 185, 129, 0.4) !important; }
.btn-success:disabled { background-color: #E2E8F0 !important; color: #94A3B8 !important; box-shadow: none !important; cursor: not-allowed !important; }

.btn-ghost { background-color: #FFFFFF !important; color: #64748B !important; border: 2px solid #E2E8F0 !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; }
.btn-ghost:hover:not(:disabled) { border-color: #CBD5E1 !important; color: #1E293B !important; transform: translateY(-2px) !important; }
.btn-ghost:disabled { background-color: #F8FAFC !important; color: #CBD5E1 !important; border-color: #F1F5F9 !important; box-shadow: none !important; cursor: not-allowed !important; }

.agile-btn-small { border-radius: 8px !important; font-weight: 700 !important; transition: all 0.2s var(--spring) !important; }
.btn-primary-light { background-color: #EFF6FF !important; color: var(--primary) !important; border: none !important; }
.btn-primary-light:hover { background-color: #DBEAFE !important; transform: scale(1.05) !important; }
.btn-copy { background-color: #F1F5F9 !important; color: #475569 !important; border: none !important; }
.btn-copy:hover { background-color: #E2E8F0 !important; transform: scale(1.05) !important; }
.btn-danger { background-color: #FEF2F2 !important; color: #DC2626 !important; border: none !important; }
.btn-danger:hover:not(:disabled) { background-color: #DC2626 !important; color: #FFF !important; transform: scale(1.05) !important; }

/* ====================================================
   详情面板描述与时间轴
   ==================================================== */
:deep(.cute-descriptions) { border-radius: 12px; overflow: hidden; border: 1px solid #F1F5F9; }
:deep(.cute-descriptions .el-descriptions__label) { background-color: #F8FAFC !important; font-weight: 800; color: #475569; width: 120px; }
:deep(.cute-descriptions .el-descriptions__content) { color: #1E293B; }

:deep(.cute-timeline .el-timeline-item__node) { background-color: var(--primary) !important; }
.timeline-card { border-radius: 12px; border: none; background: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important; transition: transform 0.3s var(--spring); }
.timeline-card:hover { transform: translateX(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important; }
.timeline-title { font-weight: 800; margin-bottom: 6px; color: #1E293B; font-size: 15px;}
.timeline-desc { color: #64748B; font-size: 13px; line-height: 1.5;}

/* ====================================================
   动画与撤销条
   ==================================================== */
.undo-bar { position: fixed; left: 50%; transform: translateX(-50%); bottom: 24px; width: auto; min-width: 400px; z-index: 3000; border-radius: 16px !important; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.3) !important; font-weight: 800 !important; }

.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-enter-from { transform: translateY(-10px); opacity: 0; }
.bounce-enter-active { animation: bounce-in 0.5s var(--spring); }
.bounce-leave-active { animation: bounce-in 0.3s var(--spring) reverse; }
@keyframes bounce-in { 0% { transform: scale(0.8); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.4s var(--spring); }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translate(-50%, 40px); }
@media (max-width: 860px) {
  .pet-card-grid { grid-template-columns: 1fr; }
}
</style>
