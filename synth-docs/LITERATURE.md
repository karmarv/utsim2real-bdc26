# Literature of the synth research line (R45-R124)

> Branch `synth-cv` only. Moved here on 2026-10-18 from `docs/07-LITERATURE.md` Section 8, so that `main` keeps the challenge references only (R1-R44, [`docs/07-LITERATURE.md`](../docs/07-LITERATURE.md) Sections 6-7, which this file cites as R1-R44). Status marks: "confirmed", "corrected", "unverified" (check before citing).

From a three-part survey (simulation and generation; detector robustness; evaluation, roadside data and venues) and a second pass on simulation-based inference and CVPR baselines (2026-10-17), for [`RESEARCH-AGENDA.md`](RESEARCH-AGENDA.md). The second pass confirmed or corrected the entries first marked "verify" (R46, R51, R52, R62, R63, R71, R77); "verify" or "unverified" still marks what could not be confirmed: check it before citing. Cite the organizers as Shahbaz and Agarwal ("Kharal" is only a GitHub handle).

| R | Work | Venue, year | Identifier | Use in the agenda |
|---|---|---|---|---|
| R45 | BayesSim: likelihood-free posteriors over simulator parameters | RSS 2019 | arXiv 1906.01728 | N1: posterior domain randomization (control) |
| R46 | Neural posterior domain randomization (Muratore et al.) | CoRL 2021 | PMLR 164:1532-1542 (volume dated 2022) | N1 |
| R47 | Meta-Sim: learning to generate synthetic datasets | ICCV 2019 | arXiv 1904.11621 | N1: feature matching over scene graphs |
| R48 | Learning to Simulate (Ruiz et al.); Meta-Sim2; AutoSimulate | ICLR 2019; ECCV 2020; ECCV 2020 | arXiv 1810.02513; 2008.09092; 2008.08424 | N1: learned and bilevel simulator tuning |
| R49 | LiDAR-in-the-Loop Hyperparameter Optimization (Goudreault et al.) | CVPR 2023 | CVF open access | N1: the only LiDAR instance (sensor tuning in simulation) |
| R50 | Real-Fake: synthetic training data as distribution matching | ICLR 2024 | arXiv 2310.10402 | N1 theory |
| R51 | LiDAR-CS: paired multi-sensor renderings of the same scenes (Fang et al.) | ICRA 2024, pp. 14822-14829 (confirmed) | arXiv 2301.12515 | N2: benchmark, no consistency training |
| R52 | Improving Generalization Ability for 3D Object Detection by Learning Sparsity-invariant Features (Lu, Lin, Hsu) | ICRA 2025 (confirmed; code available) | arXiv 2502.02322 | N2: closest detection method (subsampling) |
| R53 | DGLSS: single-domain generalization for LiDAR segmentation | CVPR 2023 | CVF open access | N2: consistency, segmentation only |
| R54 | LiDOG: walking the line between domains | ICCV 2023 | arXiv 2304.11705 | N2: synthetic-to-real segmentation |
| R55 | Single source as multiple density domains | ECCV 2024 | arXiv 2312.12098 | N2: range-dependent density |
| R56 | Towards Zero Domain Gap (Manivasagam et al.) | ICCV 2023 | CVF open access | N6: paired factor ablation (moving ego, real-trained) |
| R57 | Counterexample-guided data augmentation (Dreossi et al.) | IJCAI 2018 | arXiv 1805.06962 | N3 |
| R58 | AdvSim; KING | CVPR 2021; ECCV 2022 | arXiv 2101.06549; 2204.13683 | N3: adversarial scene generation |
| R59 | SHIFT3D; Adv3D | ICCV 2023; CoRL 2023 | arXiv 2309.05810; 2311.01446 | N3: hard objects for 3D detectors |
| R60 | Sonata: self-supervised point representation (PTv3) | CVPR 2025 | arXiv 2503.16429 | N4: pretraining, run on synthetic only |
| R61 | NOMAE: neighborhood occupancy masked autoencoding | CVPR 2025 | arXiv 2502.20316 | N4 |
| R62 | SPOT: occupancy pretraining with beam re-sampling | T-PAMI (accepted per arXiv v4; volume unverified) | arXiv 2309.10527 | N4: gains grow with pretraining data |
| R63 | Point Transformer V3; LitePT (Yue et al.) | CVPR 2024; CVPR 2026 (per arXiv comment) | arXiv 2312.10035; 2512.13689 | N4 backbone |
| R64 | Voxel Mamba; UniMamba | NeurIPS 2024; CVPR 2025 | arXiv 2406.10700; 2503.12009 | N4 backbone |
| R65 | WAKD: weight averaging in distillation under shift | ICCV 2023 workshop | arXiv 2309.11446 | N4 distillation |
| R66 | Model soups; DiWA | ICML 2022; NeurIPS 2022 | arXiv 2203.05482; 2205.09739 | N4 weight averaging |
| R67 | BoS: box stability for label-free detection mAP | ICLR 2024 | arXiv 2403.13803 | N5: label-free mAP (2D) |
| R68 | PCR: label-free detection accuracy estimation | ICCV 2025 | arXiv 2508.12082 | N5 |
| R69 | Accuracy-on-the-line; Agreement-on-the-line; ATC | ICML 2021; NeurIPS 2022; ICLR 2022 | arXiv 2107.04649; 2206.13089; 2201.04234 | N5: transfer prediction |
| R70 | Sim2Real predictivity (Kadian et al.); SIMPLER | RA-L 2020; CoRL 2024 | arXiv 1912.06321; 2405.05941 | N5: rank statistics (SRCC, MMRV) |
| R71 | Organizers (Shahbaz and Agarwal): HiFi-DT; "UrbanTwin: Synthetic Roadside LiDAR Datasets"; LiGuard | arXiv 2025; IEEE OJ-ITS vol. 7, pp. 353-364, 2026 (confirmed); arXiv 2025 | arXiv 2509.02904; 2509.06781 (DOI 10.1109/OJITS.2026.3655581); 2509.02902 | context (Car AP only, different protocol) |
| R72 | A realism metric for generated LiDAR point clouds (Triess et al.) | IJCV 2022 | arXiv 2208.14958 | N5: metric validated on segmentation |
| R73 | LiDARGen (FRD protocol); LiDM (FRID) | ECCV 2022; CVPR 2024 | arXiv 2209.03954; 2404.00815 | N5: subsample instability noted |
| R74 | On the variance of neural network training with respect to test sets (Jordan) | ICLR 2024 | arXiv 2304.01910 | N5: seed variance vs test-set noise |
| R75 | Deep ensembles work, but are they necessary? (Abe et al.) | NeurIPS 2022 | arXiv 2202.06985 | N5, N4: ensembles vs capacity |
| R76 | KID; CMMD; Chong and Forsyth (FID bias) | ICLR 2018; CVPR 2024; CVPR 2020 | arXiv 1801.01401; 2401.09603; 1911.07023 | N5: unbiased estimators |
| R77 | The FID Lottery (Dufour, Efros, Perez) | arXiv June 2026, no venue | arXiv 2606.20536 | N5: seed vs resampling variance of FID |
| R78 | clean-fid; FD-DINOv2 | CVPR 2022; NeurIPS 2023 | arXiv 2104.11222; 2306.04675 | N5: implementation and feature choice |
| R79 | Empirical Wasserstein rates (Weed and Bach); minibatch OT (Fatras et al.) | Bernoulli 2019; AISTATS 2020 | arXiv 1707.00087; 1910.04091, 2101.01792 | N5: subsampled EMD bias |
| R80 | Sinkhorn divergences (Feydy et al.); density-aware Chamfer | AISTATS 2019; NeurIPS 2021 | arXiv 1810.08278; 2111.12702 | N5: debiased distances |
| R81 | Investigating the impact of model misspecification in neural SBI (Cannon, Ward, Schmon) | arXiv 2022 | arXiv 2209.01845 | neural SBI is overconfident out of distribution |
| R82 | A trust crisis in simulation-based inference? (Hermans et al.) | TMLR 2022 | arXiv 2110.06581 | overconfidence; expected-coverage diagnostic |
| R83 | APT / NPE (Greenberg et al.); SNLE (Papamakarios et al.); NRE (Hermans et al.); BNRE (Delaunoy et al.) | ICML 2019; AISTATS 2019; ICML 2020; NeurIPS 2022 | arXiv 1905.07488; 1805.07226; 1903.04057; 2208.13624 | SBI families |
| R84 | Truncated proposals for scalable and hassle-free SBI (TSNPE; Deistler et al.) | NeurIPS 2022 | NeurIPS proceedings | sequential rounds, stable coverage |
| R85 | Flow matching posterior estimation (Wildberger, Dax et al.); score-based NPE (Sharrock et al.); Simformer (Gloeckler et al.) | NeurIPS 2023; ICML 2024; ICML 2024 | arXiv 2305.17161; 2210.04872; 2404.09636 | estimator alternatives |
| R86 | NPE-PFN: TabPFN as the density estimator (Vetter et al.) | NeurIPS 2025 | arXiv 2504.17660 | low-budget cross-check |
| R87 | Robust neural posterior estimation and statistical model criticism (Ward et al.) | NeurIPS 2022 | arXiv 2210.06564 | error model; flags misspecified summaries |
| R88 | Learning robust statistics for SBI under model misspecification (Huang, Bharti, Souza, Acerbi, Kaski) | NeurIPS 2023 | arXiv 2305.15871 | MMD-regularized summaries |
| R89 | Detecting model misspecification in amortized Bayesian inference (Schmitt et al.) | DAGM GCPR (2023 vs 2024 unverified) | arXiv 2112.08866; extended 2406.03154 | summary-space MMD detection |
| R90 | Generalized Bayesian inference for scientific simulators via amortized cost estimation (ACE; Gao, Deistler, Macke); robust Bayesian inference via the MMD posterior bootstrap (Dellaporta et al.) | NeurIPS 2023; AISTATS 2022 | arXiv 2305.15208; 2202.04744 | tempered and generalized posteriors |
| R91 | Sourcerer: sample-based maximum-entropy source distribution estimation (Vetter et al.); HNPE (Rodrigues et al.) | NeurIPS 2024; NeurIPS 2021 | arXiv 2402.07808; NeurIPS proceedings | per-frame (source) distributions |
| R92 | Does unsupervised domain adaptation improve amortized inference? (Elsemuller et al.) | TMLR 2025 | arXiv 2502.04949 | summary alignment backfires under prior misspecification |
| R93 | Domain randomization (Tobin et al.); structured DR (Prakash et al.); Active DR (Mehta et al.); automatic DR (OpenAI) | IROS 2017; ICRA 2019; CoRL 2019; arXiv 2019 | arXiv 1703.06907; 1810.10093; 1904.04762; 1910.07113 | baselines |
| R94 | Benchmarking simulation-based inference (sbibm; Lueckmann et al.) | AISTATS 2021 | arXiv 2101.04653 | simulation budgets 10^3-10^5 |
| R95 | DRUM (Miyawaki et al.); ePointDA (Zhao et al.); RangeLDM | ICRA 2026; AAAI 2021; ECCV 2024 | arXiv 2603.26263; 2009.03456; 2403.10094 | translation upper bounds (research-only) |
| R96 | SESS (Zhao, Chua, Lee); Mean Teacher (Tarvainen, Valpola); 3DIoUMatch (Wang et al.) | CVPR 2020; NeurIPS 2017; CVPR 2021 | arXiv 1912.11803; 1703.01780; 2012.04355 | consistency training |
| R97 | (unused; the sparsity-invariant features paper is R52) | | | |
| R98 | LiDAR Distillation (Wei et al.) | ECCV 2022 | arXiv 2203.14956 | beam-density invariance baseline |
| R99 | ONCE benchmark semi-supervised baselines (Mao et al.); From One to the Power of Many (Uecker, Zollner) | NeurIPS 2021 D&B; AAAI 2025 ML4AD workshop | arXiv 2106.11037; 2409.18592 | consistency baselines; label-free invariance metric |
| R100 | Neural estimators for summary statistics (infomax; Chen et al.); self-supervised SBI summaries (Akhmetzhanova et al.) | ICLR 2021; arXiv 2023 | arXiv 2010.10079; 2308.09751 | learned summaries |
| R101 | SBC (Talts et al.); TARP (Lemos et al.); L-C2ST (Linhart et al.) | arXiv 2018; ICML 2023; NeurIPS 2023 | arXiv 1804.06788; 2302.03026; 2306.03580 | posterior diagnostics |
| R102 | UrbanTwin datasets incl. **UT-TUMTraf-I** (Shahbaz and Agarwal) | IEEE OJ-ITS 2026 | arXiv 2509.06781; Dataverse DOI 10.7910/DVN/D21HNZ | third site |
| R103 | Synth It Like KITTI (Marcus et al.); ReSimAD (Zhang et al.) | ROBOVIS 2025 / Springer CCIS 2026; ICLR 2024 | arXiv 2502.15076 (code: github.com/richardmarcus/synth-it-like-kitti); 2309.05527 | external sim-to-real benchmark (Voxel R-CNN, KITTI Car, single runs) |
| R104 | SPIN: SBI under misspecification with unlabeled real data | arXiv May 2026 (venue unverified) | arXiv 2605.05652 | novelty threat (non-LiDAR) |
| R105 | CVGC: cross-view geometric consistency for LiDAR segmentation domain generalization | arXiv Feb 2026 (venue unverified) | arXiv 2602.14525 | novelty threat for paired consistency |
| R106 | LGPL: Transferring Labels to Solve Annotation Mismatches Across Object Detection Datasets (Liao, Acuna, Mahmood, Lucas, Prabhu, Fidler) | ICLR 2024 (confirmed: proceedings PDF) | proceedings.iclr.cc 2024, paper 5d56e69c | closest prior art for the scribe: names "human-machine misalignment" of synthetic labels; Synscapes to Cityscapes +2.42 mAP; transfer model uses labelled target data; 2D |
| R107 | Mind the Gap / LAT: label alignment with class semantics (Kennerley et al.) | CVPR 2026 | arXiv 2506.04737 | scribe positioning (2D, labelled target) |
| R108 | Correcting and Quantifying Systematic Errors in 3D Box Annotations (Justo Miro et al.) | WACV 2026 | arXiv 2601.14038 | sweep-timing box errors up to 2.5 m; label time |
| R109 | Annotator models: Dawid and Skene; Welinder et al. ("schools of thought"); BDC (Tan et al.) | Applied Statistics 1979; NIPS 2010; ECCV 2024 | arXiv 2407.07958 (BDC) | per-annotator bias models (2D, several annotators per object) |
| R110 | Label uncertainty from points: GLENet (Zhang et al.); DiffuBox (Chen et al.); JIoU (Feng et al.) | IJCV 2023; NeurIPS 2024; venue unverified | arXiv 2207.02466; 2405.16034; 2012.12195 | learned annotator emulators (baselines) |
| R111 | Human label agreement: Offboard 3D (Qi et al.); box-size preference study (Strafforello et al.) | CVPR 2021; ECCV 2024 workshop | arXiv 2103.05073; 2408.10844 | humans agree to about 81% 3D IoU; people prefer larger boxes |
| R112 | Size and convention bias across datasets: SAILOR (Malic et al.); MDT3D (Soum-Fontez et al.); DALI (Lu, Radha); MonoCInIS; ParisLuco3D | WACV 2023; IROS 2023; T-RO 2024 (from the DOI, unverified); unverified; unverified | arXiv 2210.07811; 2308.01000; 2412.08806; 2110.00464; 2310.16542 | "different labeling policies"; tight vs wide box datasets; what pedestrian boxes include |
| R113 | Synthetic humans for LiDAR: HUNTER (Yao et al.); Text3DAug (Reichardt et al.); HuLiGen (Galaaoui et al.); BEDLAM (Black et al.) | CVPR 2024; IROS 2024; arXiv Oct 2026 (no venue); CVPR 2023 | arXiv 2403.02769; 2408.14253; 2610.10196; 2306.16940 | asset diversity; HuLiGen is a novelty threat for paper 4 |
| R114 | Scene generation: LidarDM (Zyrianov et al.); OLiDM (Yan et al.); La La LiDAR; LiDARCrafter; Sim2SG (Prakash et al.); MetaUrban (Wu et al.); Real-Aug | ICRA 2025; AAAI 2025; AAAI 2026 (authors unverified); venue unverified; ICCV 2021; ICLR 2025; venue unverified | arXiv 2404.02903; 2412.17226; 2508.03691; 2508.03692; 2011.14488; 2407.08725; 2305.12853 | scene factor; learned layouts need labelled real scenes |
| R115 | Synthetic-data scaling: Fan et al.; SOC (Huang et al.); Lin et al.; sim-to-real gap of DR (Chen et al.) | CVPR 2024; CVPR 2026; ICLR 2025; ICLR 2022 | arXiv 2312.04567; 2510.09110; 2410.18647; 2110.03239 | paper 4 |
| R116 | Target-aware generation: Deliberate Practice (Askari-Hemmat et al.); ActGen (Huang et al.); feedback-guided synthesis; uncertainty-aware ControlNet (Niemeijer et al.) | ICML 2025; ECCV 2024; TMLR 2024; ICCV 2025 workshop (unverified) | arXiv 2502.15588; 2403.06517; 2310.00158; 2510.11346 | paper 3 (label-free loop) |
| R117 | Data selection for an unlabeled target: TAROT (Feng et al.); DSIR (Xie et al.); DsDm (Engstrom et al.); CARE (Prabhu et al.) | ICML 2025; NeurIPS 2023; ICML 2024; TMLR 2023 | arXiv 2412.00420; 2302.03169; 2401.12926; 2302.04832 | curation baselines |
| R118 | Data-copying tests: Meehan et al.; Bhattacharjee et al.; Alaa et al. | AISTATS 2020; ICML 2023; ICML 2022 | arXiv 2004.05675; 2302.13181; 2102.08921 | site-factored leakage audit |
| R119 | Sensor effects measured on detection: Huch et al. (range noise); Ghost-FWL (Ikeda et al.); Robo3D (Kong et al.); Multi-Echo (Man et al.) | T-IV 2023; CVPR 2026; ICCV 2023; ICCV 2021 | arXiv 2303.01899; 2603.28224; 2303.17597; 2107.11470 | sensor share; published drop gains are small |
| R120 | Drop and re-simulation from unlabeled scans: DUSty, DUSty v2; neural LiDAR re-simulation (Marcus, Stamminger); LidarVerse (Che et al.) | IROS 2021, WACV 2023; ITSC 2025; arXiv Oct 2026 (no venue) | arXiv 2102.11952, 2210.11750; 2507.12489; 2610.19201 | sensor factor; LidarVerse is a threat (unseen scan patterns) |
| R121 | Multi-LiDAR asynchrony: CoBEVFlow (Wei et al.); TrajMatch (Ren et al.); UniCal (Yang et al.); HDV-Mess | NeurIPS 2023; venue unverified; ECCV 2024; venue unverified | arXiv 2309.16940; 2302.02157; 2409.18953; 2106.04175 | label time; asynchronous rendering |
| R122 | Gradient calibration of LiDAR models: Heiden et al.; Katyan, Gardner, Lalonde | ICRA 2020; BMVC 2025 | arXiv 1912.01652; 2602.10492 | cached-hit differentiable sensor head |
| R123 | Sensor placement and sensor gaps: Place3D (Li et al.); Roadside-Opt (Jiang et al.); Hu et al.; S2S-Net | NeurIPS 2024; ICCV 2023; CVPR 2022; no venue | arXiv 2403.17009; 2310.07247; 2105.00373; 2504.17399 | sensor-mixture randomization |
| R124 | TUMTraf Intersection (A9) dataset (Zimmer, Cress, Nguyen, Knoll) | ITSC 2023 | arXiv 2306.09266 | third site: two Ouster OS1-64 gen 2 on a 7 m gantry, 4,800 labelled frames, 10 classes; licence **CC BY-NC-ND 4.0** (dev-kit README and paper; dev-kit code MIT) |
