<template>
  <div class="kg-wrap">
    <div class="kg-toolbar">
      <el-space>
        <el-text type="info">物种过滤</el-text>
        <el-select v-model="selectedSpecies" style="width: 120px" @change="loadGraph">
          <el-option label="全部" value="" />
          <el-option v-for="item in speciesOptions" :key="item" :label="item" :value="item" />
        </el-select>
      </el-space>
      <el-button class="agile-btn-small" @click="loadGraph">刷新图谱</el-button>
    </div>
    <div ref="chartRef" class="kg-canvas" />
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { ElMessage } from "element-plus";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { fetchKnowledgeGraph } from "../api/ai";
import { PET_SPECIES_OPTIONS } from "../constants/petSpecies";
import { getErrorMessage } from "../utils/status";

const props = defineProps({
  species: { type: String, default: "" },
  highlightedPath: { type: Array, default: () => [] }
});

const emits = defineEmits(["update:species"]);

const chartRef = ref(null);
const speciesOptions = PET_SPECIES_OPTIONS;
const selectedSpecies = ref(props.species || "");
let chart = null;
let nodesCache = [];
let linksCache = [];

function nodeColor(type) {
  if (type === "SymptomNode") return "#2563eb";
  if (type === "DiseaseNode") return "#dc2626";
  if (type === "DrugNode") return "#16a34a";
  if (type === "TreatmentNode") return "#ea580c";
  if (type === "ExamNode") return "#7c3aed";
  if (type === "SpeciesNode") return "#0f766e";
  return "#475569";
}

function nodeSize(type, highlighted) {
  const base = {
    SymptomNode: 34,
    DiseaseNode: 38,
    DrugNode: 30,
    TreatmentNode: 28,
    ExamNode: 28,
    SpeciesNode: 26
  }[type] || 24;
  return highlighted ? base + 8 : base;
}

async function loadGraph() {
  emits("update:species", selectedSpecies.value);
  try {
    const res = await fetchKnowledgeGraph({
      species: selectedSpecies.value || null,
      highlighted_path: props.highlightedPath || []
    });
    const payload = res.data || { nodes: [], links: [] };
    nodesCache = payload.nodes || [];
    linksCache = payload.links || [];
    await renderGraph(nodesCache, linksCache);
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "图谱加载失败"));
  }
}

async function renderGraph(nodes, links) {
  await nextTick();
  if (!chartRef.value) return;
  if (!chart) {
    chart = echarts.init(chartRef.value);
  }
  const mappedNodes = nodes.map((n) => ({
    id: n.id,
    name: n.name,
    category: n.node_type,
    value: {
      zh_name: n.zh_name || n.name,
      en_name: n.en_name || "",
      severity_level: n.severity_level || "",
      applicable_species: n.applicable_species || []
    },
    symbolSize: nodeSize(n.node_type, Boolean(n.highlighted)),
    itemStyle: {
      color: nodeColor(n.node_type),
      borderColor: n.highlighted ? "#f59e0b" : "#ffffff",
      borderWidth: n.highlighted ? 3 : 1
    }
  }));

  const mappedLinks = links.map((l) => {
    const isForbidden = l.relation === "drug_contraindication" || l.relation === "species_drug_forbidden";
    return {
      source: l.source,
      target: l.target,
        value: l.relation,
        relation: l.relation,
        confidence: Number(l.confidence || 0),
        lineStyle: {
          width: l.highlighted ? 3 : 1.3,
          color: isForbidden ? "#ef4444" : "#64748b",
          opacity: 0.7,
          type: isForbidden ? "dashed" : "solid",
          curveness: 0.2
        },
        label: { show: true, formatter: l.relation }
      };
  });

  chart.setOption({
    animationDurationUpdate: 450,
    tooltip: {
      trigger: "item",
      formatter: (params) => {
        if (params.dataType === "node") {
          const val = params.data?.value || {};
          const species = Array.isArray(val.applicable_species) ? val.applicable_species.join(" / ") : "-";
          return `节点：${val.zh_name || params.data?.name || "-"}<br/>英文：${val.en_name || "-"}<br/>严重级别：${val.severity_level || "-"}<br/>适用物种：${species}`;
        }
        const relation = params.data?.relation || params.data?.value || "-";
        const weight = Number(params.data?.confidence || 0).toFixed(2);
        return `关系：${relation}<br/>权重：${weight}`;
      }
    },
    series: [
      {
        type: "graph",
        layout: "force",
        roam: true,
        data: mappedNodes,
        links: mappedLinks,
        force: { repulsion: [800, 1200], edgeLength: [60, 150], gravity: 0.1, friction: 0.6 },
        draggable: true,
        edgeSymbol: ["none", "arrow"],
        edgeSymbolSize: [4, 8],
        lineStyle: { curveness: 0.2, opacity: 0.7, width: 2 },
        label: { show: true, position: "right", color: "#1e293b", fontSize: 12 },
        edgeLabel: { show: true, fontSize: 10, color: "#475569" },
        emphasis: { focus: "adjacency", blurScope: "coordinateSystem" }
      }
    ]
  });
}

watch(
  () => props.highlightedPath,
  () => {
    loadGraph();
  },
  { deep: true }
);

watch(
  () => props.species,
  (value) => {
    selectedSpecies.value = value || "";
    loadGraph();
  }
);

onMounted(async () => {
  await loadGraph();
  window.addEventListener("resize", () => chart?.resize());
});

onBeforeUnmount(() => {
  if (chart) chart.dispose();
});
</script>

<style scoped>
.kg-wrap { min-height: 460px; }
.kg-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.kg-canvas {
  height: 430px;
  border-radius: 16px;
  background: linear-gradient(140deg, rgba(224, 231, 255, 0.4), rgba(240, 249, 255, 0.7));
  border: 1px solid rgba(148, 163, 184, 0.35);
}
.agile-btn-small {
  border-radius: 999px !important;
}
</style>
