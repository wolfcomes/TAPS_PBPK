# MCT：PA 生物活化探索案例

MCT 是 monocrotaline，野百合碱，是一类 PA 中的具体分子。目标候选支路为 **MCT → dehydromonocrotaline（脱氢野百合碱）／大鼠 CYP3A1**。CYP3A1 是当前研究范围选择，现有证据主要支持 CYP3A 家族，尚未证明其是该反应的唯一或主要大鼠亚型。

本例当前分开处理两件事：建立可信的母体暴露背景；补齐特异活化支路的酶、产物和动力学证据。母体总消耗、MNO 生成、脱氢活化三种终点不能互换。案例证据与局限见[主报告](../docs/reports/research_report.md)。

## 文件与使用口径

| 路径 | 内容 | 可支持的判断 |
|---|---|---|
| `references/Suparmi2020_MCT_PBK.pdf` | 混合微粒体母体耗竭、作者 PBK 和毒性外推 | 支持总消耗与缩放，不支持 CYP3A1 单酶活化参数 |
| `references/Suparmi2020_supplement1_model.docx` | 作者原始模型补充 | 已下载；无需再把“获取补充代码”列为待办 |
| `references/Suparmi2020_supplement2_radiotracer.docx` | 作者对既往放射性数据的二次提取 | 不是新的母体 LC–MS 原始数据 |
| `references/Lin2003_Clivorine_CYP3A1_CYP3A2.md` | 2003 年 CYP3A1/3A2 文章的题录、原摘要及链接；全文 PDF 尚未取得 | 底物为 Clivorine，不是 MCT 单酶证据 |
| `references/Lin2021_MCT_MNO_PK.pdf` | 完整 18 页接受稿，MCT/MNO 大鼠 PK | p16 Fig.3、p18 Table 3；无脱氢产物 PK |
| `data/kinetics_and_pk/` | 两篇论文的参数、条件与采血时间转录 | 原文单位和终点保留；不是原始 assay 重复数据 |
| `data/parent_pk/` | Lin 母体每途径 7 个近似数字化均值点及来源图/表 | 共 14 点、0–8 h；不是个体原始数据，无可靠 SD；24 h 近定量限点未赋零 |
| `data/radiotracer_secondary/` | Suparmi/Estep 放射性当量二次数据与作者预测 | 必须与低剂量母体 PK 分开使用；未取得 Estep 原始全文和原始表 |
| `data/context/PA_microsome_experiments.pptx` | 项目自测 Retrorsine / Clivorine 实验背景 | 不是 MCT 参数；大鼠混合微粒体也不等于单 CYP |
| `models/author_original/` | 提取的作者方程、关键值、生理/分配参数 | 文献七室 PBK，不等于当前 PK-Sim pilot |
| `models/pilot/` | MCT 基线 snapshot、PO/IV PKML.gz | 聚合肝代谢的未校准模型，没有显式 MNO 或脱氢产物 |
| `structures/ligands/`、`structures/protein/` | MCT 与脱氢野百合碱 PubChem 3D SDF、rat CYP3A1 P04800 AlphaFold v6 | 产物 CID 104764 身份/立体化学已核验；蛋白 504 aa、无 HEM，未准备催化体系 |
| `structures/branch_reference_MNO/` | MCT N-oxide 的 PubChem SDF | 仅另一代谢支路参考，不是脱氢产物 |
| `results/` | 历史 14 情景指标、基线曲线、图和 R 重跑核验 | `baseline_curves.csv` 为 R 的一对 PO/IV 基线，时间 h、浓度 ng/mL |
| `results/diagnostics/` | 四次 IV 极限诊断与吸收/质量分数审计 | 100× 是诊断，不是生理参数或成功校准 |

作者原代码使用 0.25 kg 大鼠、默认 IV 60 mg/kg；当前 pilot 为 0.20 kg、IV 1 mg/kg / PO 10 mg/kg。原代码肝 Km=9.22 µM，表格四舍五入为 9.2；肠分别为 13.39 和 13.4。区别保留，不随意统一精度。

结构的下载来源、历史身份核查与文件哈希见[结构来源表](structures/sources.json)。新增[脱氢野百合碱 SDF](structures/ligands/dehydromonocrotaline_CID104764_3D.sdf)为 PubChem CID 104764 原始 3D 构象，C16H21NO6；已核对完整 InChIKey 和四个 R 立体中心，反应原子映射与酶结合构象仍待准备。MNO 的 PubChem 记录未指定 N 立体化学，而下载 3D 构象指定了一种 N 构型；该差别已记录，不能把它当作已指定的目标活化产物。

## 为什么先修母体模型

现有基线 IV AUC0–24=5808.07 ng·h/mL，对照文献 516；PO AUC0–24=54.80，对照 4035。PO Cmax=4.43 ng/mL，对照 2102，Tmax 约 4.58 h，对照 0.40 h。24 h 进入黏膜比例仅 0.1380%。重跑确认了模型数值行为，没有修复这些偏差。

pilot 使用通用 Rat、UNKNOWN 性别、默认分配/通透性、假设 pKa/溶解度，仅配置归一化聚合肝代谢。`MCT_TotalMetabolism` 的 kcat=2.1/min 是组织容量实现中的归一化数值，**不是测得的 CYP3A1 分子周转数**；自动 `Metabolite` 是代谢记账汇。

**下一步：**先用 IV 核对分布、肝细胞交换与总清除缩放，再处理 PO 吸收接口；并行确认 CYP3A1 贡献、反应结构及特异产物生成 assay。未解决这些条件之前，不把分子活化参数直接替换总母体耗竭参数，也不以该例作为整条方法的首个成功判据。

## 运行

在项目根目录、激活 conda `ospsuite-r` 后：

```bash
Rscript scripts/run_pbpk.R MCT /tmp/taps_mct_new
Rscript scripts/run_pbpk.R MCT /tmp/taps_mct_snapshot_new snapshot
```

默认运行 PO/IV 两个已存 PKML；`snapshot` 从基线 JSON 重建两个模拟，不读取外部基础模板。输出新目录，不覆盖文献或历史结果。作者原模型与当前 pilot 的结构对照、缺失数据及进入门槛见主报告和计划。
