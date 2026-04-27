import { computed } from "vue";
import { useRoute } from "vue-router";

const helpMap = {
  "/appointments": {
    title: "挂号管理指引",
    steps: ["选择院区和宠物", "选择医生与就诊时段", "确认紧急程度并提交"]
  },
  "/vet-workbench": {
    title: "兽医工作台指引",
    steps: ["查看待诊队列", "开始接诊并录入病历", "如需开方可进入处方开具"]
  },
  "/inpatient": {
    title: "住院管理指引",
    steps: ["查看笼舍可视化地图", "点击空闲笼快速办理入院", "占用笼可查看体征记录"]
  },
  "/pharmacy": {
    title: "药房工作台指引",
    steps: ["查看待缴费处方倒计时", "必要时催缴或作废", "关注低库存预警并补货"]
  },
  "/archives": {
    title: "档案管理指引",
    steps: ["先建主人档案", "再建宠物档案并维护过敏史", "可在详情页查看历史就诊"]
  },
  "/schedule-management": {
    title: "排班管理指引",
    steps: ["按院区查看医生排班网格", "点击时段调整排班", "系统会自动校验冲突"]
  },
  "/inventory-eoq": {
    title: "EOQ补货指引",
    steps: ["查看库存/安全库存对比", "根据EOQ建议调整补货量", "生成采购任务并跟踪审批"]
  },
  "/home": {
    title: "系统使用手册（全屏）",
    steps: [
      "点击右下角“系统手册”按钮进入全屏手册",
      "按角色查看权限边界、操作步骤与流程关联",
      "在底层数据字典页查看表结构、主键外键与SQL关系"
    ]
  },
  "/followup-tasks": {
    title: "回访任务步骤指引",
    steps: [
      "步骤1：核实宠物现状并记录关键症状变化",
      "步骤2：反馈护理建议并填写执行情况",
      "步骤3：根据风险等级预约复诊时间",
      "步骤4：完成归档并标记回访完成"
    ]
  }
};

export function useHelpCenter() {
  const route = useRoute();
  const help = computed(() => helpMap[route.path] || {
    title: "页面操作指引",
    steps: ["查看页面数据", "按提示完成操作", "遇到错误可点重试或联系管理员"]
  });
  return { help };
}
