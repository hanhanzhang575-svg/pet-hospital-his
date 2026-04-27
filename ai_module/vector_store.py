"""ChromaDB向量检索模块（含DeepSeek embedding降级策略）。"""

from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass

try:
    import chromadb
except Exception:  # pragma: no cover - 允许无chromadb环境降级
    chromadb = None

try:
    import httpx
except Exception:  # pragma: no cover - 允许无httpx环境降级
    httpx = None


KNOWLEDGE_BASE: list[str] = [
    "反复呕吐+腹泻+精神萎靡+未接种疫苗→犬细小病毒→输液支持治疗→禁用糖皮质激素",
    "高热+咳嗽+鼻分泌物+疫苗不全→犬瘟热→抗感染+雾化→禁用免疫抑制剂",
    "频繁抓挠+耳道异味+甩耳→外耳炎→耳道清洗+抗炎滴耳→禁用刺激性酒精冲洗",
    "多饮多尿+体重下降+高血糖→犬糖尿病→胰岛素治疗→禁用高糖输液",
    "食欲减退+黄疸+ALT显著升高→肝炎→保肝+抗炎→禁用对乙酰氨基酚",
    "后肢无力+腰痛+跳跃困难→椎间盘疾病→镇痛+限动→禁用剧烈运动训练",
    "跛行+关节肿胀+晨僵→骨关节炎→NSAIDs+关节营养→禁用超负荷跑跳",
    "持续咳嗽+运动不耐受+心杂音→二尖瓣退行性病变→心衰管理→禁用高钠饮食",
    "腹胀+呼吸急促+突发虚弱→胃扭转→紧急减压手术→禁用延迟观察",
    "发热+尿频尿痛+尿液浑浊→尿路感染→抗菌治疗→禁用随意停药",
    "血尿+排尿困难+影像结石→膀胱结石→溶石或手术→禁用高矿物饮食",
    "突然癫痫+意识障碍+间歇恢复→癫痫发作→抗惊厥治疗→禁用自行停药",
    "皮肤红斑+丘疹+剧痒+跳蚤史→跳蚤过敏性皮炎→驱虫+抗炎→禁用单纯止痒不驱虫",
    "脱毛+皮屑+瘙痒+真菌镜检阳性→皮肤癣菌病→抗真菌治疗→禁用共用梳具",
    "咳嗽+气促+胸片纹理增强→支气管炎→雾化+支气管扩张→禁用烟雾刺激",
    "持续腹泻+黏液便+里急后重→结肠炎→肠道调理+抗炎→禁用高脂零食",
    "口臭+牙龈红肿+牙石明显→牙周炎→洁牙+抗菌→禁用硬物啃咬",
    "眼红+流泪+畏光+角膜染色阳性→角膜溃疡→角膜修复+抗感染→禁用激素滴眼",
    "泪痕重+眯眼+角膜干燥→干眼症→人工泪液+免疫调节→禁用长期含防腐剂滴眼",
    "便秘+排便困难+腹部触痛→便秘/巨结肠倾向→补液+促动力→禁用长期仅灌肠",
    "体重快速增加+皮肤变薄+多食→库欣综合征→内分泌管理→禁用随意激素补充",
    "嗜睡+怕冷+脱毛+体重增加→甲减→甲状腺素替代→禁用盲目减量",
    "多尿+多饮+瘙痒+血象异常→子宫蓄脓→手术+抗感染→禁用拖延保守治疗",
    "乳房肿块+年龄偏大+未绝育→乳腺肿瘤→外科评估→禁用仅外敷处理",
    "食欲废绝+腹痛+胰酶升高→胰腺炎→低脂饮食+镇痛→禁用高脂食物",
    "关节跛行+莱姆接触史+发热→蜱媒疾病→抗感染+驱蜱→禁用忽视再感染风险",
    "异食癖+呕吐+X光异物影→胃肠异物→内镜或手术→禁用强行喂食",
    "慢性呕吐+体重下降+肠壁增厚→炎症性肠病→饮食管理+免疫调节→禁用随意换粮",
    "猫咪食欲下降+流涎+黄疸→猫脂肪肝风险→营养支持→禁用长期禁食",
    "猫咪打喷嚏+流涕+结膜炎→上呼吸道感染→抗感染+支持疗法→禁用应激环境",
    "猫咪多饮多尿+甲状腺结节→甲亢→甲巯咪唑/放疗评估→禁用碘摄入过量",
    "猫咪体重下降+食欲差+肌酐升高→慢性肾病→肾脏处方粮+补液→禁用高磷饮食",
    "猫咪尿闭+频繁进猫砂盆+痛苦叫→尿道阻塞→紧急导尿→禁用延迟就医",
    "猫咪下泌尿道反复症状+应激史→特发性膀胱炎→环境减压+镇痛→禁用单一抗生素依赖",
    "猫咪呼吸急促+张口呼吸+胸片哮喘征→猫哮喘→雾化激素+支扩→禁用粉尘香薰",
    "猫咪牙龈炎口炎+进食疼痛→口炎综合征→口腔综合治疗→禁用粗暴清洁",
    "兔食欲下降+粪球减少+腹胀→胃肠停滞→补液+促动力+强制喂食→禁用青霉素类抗生素",
    "兔流涎+牙齿过长+咀嚼困难→牙科问题→磨牙处理→禁用高糖软食",
    "兔呼吸困难+鼻分泌物→呼吸道感染→针对性抗感染→禁用青霉素类抗生素",
    "犬急性出血性腹泻+血便→急性肠胃炎→补液+止吐→禁用脱水状态下延迟治疗",
    "犬高龄咳嗽+夜间加重→慢性支气管病→雾化+体重控制→禁用肥胖放任",
    "犬皮肤脓疱+细菌培养阳性→脓皮症→抗菌+皮肤护理→禁用频繁洗浴刺激",
    "犬瘙痒季节性加重+趾间红肿→特应性皮炎→过敏管理→禁用长期无监测激素",
    "猫呕吐毛球+间歇便秘→毛球症→化毛+纤维补充→禁用连续高脂零食",
    "猫突然后肢瘫痪+叫声剧烈→动脉血栓→急救镇痛+抗凝评估→禁用延误止痛",
    "犬眼球突出+角膜暴露→眼科急症→润滑+复位手术→禁用挤压眼球",
    "犬持续瘙痒+耳炎复发+食物相关→食物过敏→排除饮食试验→禁用频繁换配方",
    "犬贫血+黄疸+网织红细胞增→免疫介导溶血→免疫抑制+支持→禁用未监测减药",
    "猫贫血+FeLV阳性→病毒相关贫血→支持治疗→禁用盲目强免疫抑制",
    "犬发热+关节痛+血小板降低→埃里希体感染→抗感染+支持→禁用忽视蜱虫防控",
    "猫慢性腹泻+体重下降+超声肠壁异常→慢性肠病→分层诊断+饮食管理→禁用单次对症即停",
]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _hash_embedding(text: str, dim: int = 128) -> list[float]:
    vec = [0.0] * dim
    chunks = [text[i : i + 2] for i in range(0, len(text), 2)]
    for token in chunks:
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        idx = int(digest[:8], 16) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _deepseek_embedding(text: str) -> list[float] | None:
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key or httpx is None:
        return None
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                "https://api.deepseek.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "deepseek-embedding", "input": text},
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception:
        return None


def embed_text(text: str) -> list[float]:
    """优先DeepSeek embedding，失败后回退到本地hash embedding。"""
    return _deepseek_embedding(text) or _hash_embedding(text)


@dataclass
class SearchResult:
    text: str
    score: float


class VectorKnowledgeStore:
    """封装知识向量化与TopK检索。"""

    def __init__(self, path: str = ".chromadb", collection_name: str = "pet_disease_knowledge") -> None:
        self._path = path
        self._collection_name = collection_name
        self._memory_embeddings: list[list[float]] = [embed_text(item) for item in KNOWLEDGE_BASE]
        self._collection = None
        if chromadb is not None:
            client = chromadb.PersistentClient(path=self._path)
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._seed_collection()

    def _seed_collection(self) -> None:
        if self._collection is None:
            return
        existing = self._collection.count()
        if existing >= len(KNOWLEDGE_BASE):
            return
        ids = [f"kb-{i:03d}" for i in range(len(KNOWLEDGE_BASE))]
        embeds = [embed_text(item) for item in KNOWLEDGE_BASE]
        self._collection.upsert(ids=ids, documents=KNOWLEDGE_BASE, embeddings=embeds)

    def search(self, query_text: str, top_k: int = 5) -> list[SearchResult]:
        """检索最相似知识条目TopK。"""
        query_embedding = embed_text(query_text)
        if self._collection is not None:
            result = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)
            docs = result.get("documents", [[]])[0]
            distances = result.get("distances", [[]])[0]
            pairs = []
            for i, doc in enumerate(docs):
                distance = float(distances[i]) if i < len(distances) else 1.0
                pairs.append(SearchResult(text=doc, score=round(1.0 - distance, 4)))
            return pairs
        scored = [
            SearchResult(text=text, score=round(_cosine(query_embedding, emb), 4))
            for text, emb in zip(KNOWLEDGE_BASE, self._memory_embeddings)
        ]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]


