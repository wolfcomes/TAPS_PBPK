# DXM：主方法验证案例

目标反应是右美沙芬 dextromethorphan（DXM）经**人 CYP2D6 O-去甲基化**形成右啡烷 dextrorphan（DXO）。主终点先选匹配条件下的母体 PK；定义匹配、原模型实际含有的 DXO 曲线作为辅助终点。案例选择的证据与数值解释见[主报告](../docs/reports/research_report.md)。

## 文件与使用口径

| 路径 | 内容 | 使用要求 |
|---|---|---|
| `data/observations/observations.csv` | 唯一活动观测长表，732 行，包含主列与辅助误差列 | 先按 `dataset_id` 筛选；`role=primary` 才是主测量；逐行读取单位，未统一换算 |
| `data/observations/dataset_index.csv` | 41 个数据集的分析物、部位和时间点数 | `data_file` 指向同一个长表；共 393 个时间点，不是 393 位受试者 |
| `data/observations/simulation_mappings.csv` | 模拟—观测输出对应 | 原映射引用 37 个不同观测名称，不能假定 41 组全部已映射 |
| `data/kinetics/compound_parameters.csv` | 快照参数与 Publication / ParameterIdentification / Unknown 来源 | 保存字段与实际生效参数分开解释 |
| `models/osp/dxm_snapshot.json` | 本地冻结的官方完整快照，3 compounds、29 simulations、41 observed datasets | 全部原始观测也嵌在其中；不是每次联网追踪最新版 |
| `models/osp/simulation_index.csv` | 29 场景的给药、过程、输出等索引 | 正式评价前回原论文确认研究用途 |
| `models/baselines/` | PO_EM、IV_EM、PO_AS2 的三套选定快照与 PKML.gz | 敏感性基线延长到 120 h；超原观测窗部分属于外推 |
| `models/paper_projects/` | 论文个体、群体原生 `.pksim5` 项目 ZIP | 保留原包；未证明与冻结官方快照逐项等同 |
| `structures/` | 两个 PubChem 3D SDF、2F9Q 原件及含 HEM/水的 chain A | 未准备成反应复合物；2F9Q 非 DXM 共晶 |
| `results/sensitivity/` | DXM/DES 六场景、102 主运行的联合指标与三张图 | 这是参数响应分析，不是 TAPS 或临床准确性验收 |
| `results/baselines/` | DXM 三场景的原始浓度、单位及运行时参数审计 | 时间通常为 min、浓度 µmol/L，以 `units.json` 为准 |
| `comparators/desipramine/` | DES 三套基线输入与结果 | 量化与 DXM 的响应差异，非第二主案例 |
| `comparators/mm_examples/` | 阿普唑仑/地高辛原设置、运行时参数及 original/formula_restored 效应表 | 必须按 `arm` 区分两组；只改保存 Vmax 可能未改变固定 kcat |
| `references/` | PBPK 全文 XML/补充 PDF，Oláh 2011 与 McCarty 2021 全文 HTML | 原始 HTML 保留来源；其网页资源可能仍需联网加载 |

`observations.csv` 的 `point_index` 从 0 开始；同一时间点的主列、SD 等辅助列分别占行。辅助列单位有时与主列不同；缺失值或空单位保持原样。未结合 DXO、经去结合测得的总 DXO、蛋白未结合 DXO 不是同一种测量定义。

## 模型解释与当前缺口

目标默认过程保存 Km=4.65 µM、体外 Vmax=0.134 nmol/min/mg、CYP content=10 pmol/mg；酶含量来源标为 Unknown。实际生效 kcat=90.89 min⁻¹，以及 AS=2 分支的 242.45 min⁻¹，属于优化参数。它们可作 OSP 参考，不能直接作为独立实验 G1。

PO_EM 有显式 DXO；IV_EM 和 PO_AS2 的选定基线只有母药及目标代谢汇。没有产物输出不等于产物浓度为零。PO_EM 对应 Capon 场景，其观测映射只有母药，也不能把所选 DXO 模型输出当成已匹配的实测 DXO 曲线。

2F9Q 含工程突变 L230D/L231R 和 N 端截短，分辨率 3.00 Å。当前中性 PubChem DXM 输入需按实验条件处理质子化；还需确定目标序列、底物位姿、膜/溶剂、heme/Compound I、配位、电荷、自旋与平衡。下载来源、身份核查与各文件哈希见[结构来源表](structures/sources.json)。

**下一步：**核对独立的反应特异 assay、活性 CYP2D6 量与 `fu,inc`；按研究审计临床数据是否已用于原模型开发；冻结共享背景和 G2-control 规则，再开始体系准备。TAPS/QM/MM 与完整网络均尚未执行。

## 运行

在项目根目录、激活 conda `ospsuite-r` 后：

```bash
Rscript scripts/run_pbpk.R DXM /tmp/taps_dxm_new
Rscript scripts/run_pbpk.R DES /tmp/taps_des_new
```

这会重算各自三套已存基线。要从选定 JSON 重建，末尾增加 `snapshot`；库版本可能造成差异。完整历史敏感性脚本、102 组运行和诊断保留在归档中；活动区以联合摘要为准，当前入口不重新生成旧专题报告。
