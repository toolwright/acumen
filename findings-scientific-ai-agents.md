# Self-Improving AI Agents for Scientific Research & Discovery

**Date**: 2026-03-30
**Scope**: Market landscape, infrastructure, key players, and startup viability assessment for self-improving AI agents applied to scientific research and discovery (2025-2026)

---

## 1. The Landscape: What Exists Today

### 1a. Sakana AI Scientist v2

The most advanced end-to-end autonomous research system publicly demonstrated. Published in Nature (collaboration between Sakana AI, UBC, Vector Institute, Oxford). Google partnered with Sakana to integrate Gemini/Gemma models.

**Capabilities:** Iteratively formulates hypotheses, designs experiments, executes them, analyzes data, visualizes results, and writes full scientific manuscripts -- all autonomously. Uses a progressive agentic tree-search methodology managed by a dedicated experiment manager agent.

**Key milestone:** Produced the first entirely AI-generated paper to pass peer review at a workshop level (ICLR 2025). One manuscript exceeded the average human acceptance threshold.

**v2 improvements over v1:** Eliminates reliance on human-authored code templates, generalizes across diverse ML domains, and uses novel agentic tree search for open-ended idea exploration.

**Economics:** Approximately $6-15 per full research paper, ~3.5 hours of human involvement. Traditional research: months to years per paper.

**Current limitation:** Only operates in computer science / machine learning domains. Researchers believe extension to other fields is feasible but not yet demonstrated. Sometimes produces underdeveloped ideas or inaccurate citations.

**Sources:**
- [AI Scientist v2 paper (arXiv)](https://arxiv.org/abs/2504.08066)
- [Sakana AI Scientist v2 GitHub](https://github.com/SakanaAI/AI-Scientist-v2)
- [Sakana AI Nature publication](https://sakana.ai/ai-scientist-nature/)
- [Sakana AI Scientist v2 announcement](https://pub.sakana.ai/ai-scientist-v2/paper/paper.pdf)
- [Google partnership explanation](https://www.theneuron.ai/explainer-articles/why-google-partnered-with-sakana-ai-explained/)

### 1b. Google AI Co-Scientist

Multi-agent system from Google Research, Cloud AI, and DeepMind. Coalition of specialized agents that iteratively generate, evaluate, and refine hypotheses, creating a self-improving cycle of increasingly high-quality outputs.

**Demonstrated results:**
- **Drug repurposing (Stanford):** Identified drugs that could be repurposed for liver fibrosis treatment
- **Antimicrobial resistance (Imperial College London):** Produced in days the same hypothesis that a human research team took years to develop
- **Cancer research:** C2S-Scale, a 27B parameter foundation model for single-cell analysis (collaboration with DeepMind and Yale), generated a novel hypothesis about cancer cellular behavior

**Architecture:** Uses automated feedback loops for iterative hypothesis generation and refinement. Paired with Gemini-backed coding agent for writing empirical software to evaluate hypotheses.

**Sources:**
- [Google Research blog: AI co-scientist](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/)
- [IEEE Spectrum coverage](https://spectrum.ieee.org/ai-co-scientist)
- [Google DeepMind announcement](https://www.techbuzz.ai/articles/google-deepmind-unveils-ai-co-scientist-tool-for-breakthroughs)
- [Pharmaceutical Technology coverage](https://www.pharmtech.com/view/google-launches-ai-co-scientist-system)

### 1c. Autoscience Institute

Startup that raised $14M seed (March 2026) led by General Catalyst, with Toyota Ventures, Perplexity Fund, MaC Ventures, and S32 participating. Building the first automated AI research lab.

**Milestones:**
- First AI system to produce a peer-reviewed scientific research paper (ICLR 2025 workshop)
- Silver Medal in Kaggle Santa 2025 competition against 3,300 teams -- the first fully autonomous system to place in a live Kaggle competition
- Deploying hundreds of automated AI Research Scientists for Fortune 500 companies training specialized ML models

**Business model:** Managed service deploying autonomous AI research scientists that continuously generate and ship improvements to customer ML models.

**Sources:**
- [Autoscience $14M funding announcement](https://www.businesswire.com/news/home/20260318760407/en/Autoscience-Raises-$14M-to-Build-the-Worlds-First-Automated-AI-Research-Lab)
- [SiliconANGLE coverage](https://siliconangle.com/2026/03/19/autoscience-builds-automated-research-lab-machine-learning-models-14m/)

---

## 2. Autonomous Laboratory Infrastructure

### 2a. Self-Driving Laboratories (Physical)

The physical infrastructure for autonomous experimentation is maturing rapidly.

**MARS (Multi-Agent Research System):** Published January 2026 by China's Shenzhen Institute of Advanced Technology. A knowledge-driven hierarchical architecture coordinating 19 LLM agents with 16 domain-specific tools. Achieved closed-loop autonomous materials discovery by integrating robotic experimentation. Optimized perovskite nanocrystals in 10 iterations, designed novel water-stable composites in 3.5 hours.

**Scale of acceleration:** AI-driven methods reduce the traditional 10-20 year materials discovery timeline to 1-2 years through computational prediction, inverse design, and automated experimentation. Labs at Berkeley, NC State, MIT, and institutions across China synthesize dozens of new materials per week rather than a handful per year.

**Government investment:** The U.S. DOE's Genesis Mission tasks national labs with building an AI-driven discovery platform linking supercomputers, scientific datasets, and autonomous labs. Pacific Northwest National Labs ordered a $47M, 97-robot autonomous lab in December 2025.

**Sources:**
- [MARS multi-agent system (Phys.org)](https://phys.org/news/2026-01-multi-agent-ai-robots-automate.html)
- [AI-driven materials discovery (Newzino)](https://newzino.com/story/ai-materials-discovery-2026)
- [Argonne Autonomous Discovery](https://www.anl.gov/autonomous-discovery)
- [Cypris AI-accelerated materials overview](https://www.cypris.ai/insights/ai-accelerated-materials-discovery-in-2025-how-generative-models-graph-neural-networks-and-autonomous-labs-are-transforming-r-d)
- [ScienceDaily: 10x faster materials discovery](https://www.sciencedaily.com/releases/2025/07/250714052105.htm)

### 2b. Cloud Lab Platforms

**Ginkgo Cloud Lab (launched March 2, 2026):** Allows researchers to transition benchwork to autonomous lab infrastructure via web browser. Runs on proprietary Reconfigurable Automation Carts (RACs) combining high-precision robotic arms, maglev sample transport, and industrial-grade software. Provides remote access to 70+ instruments spanning critical biological unit operations.

**Chemspeed Technologies + SciY (February 2026):** Open Self-Driving Lab (SDL) platform for vendor-agnostic integration uniting modular precision automation, scientific analysis, and lab management software.

**NVIDIA + Thermo Fisher:** Collaboration integrating NVIDIA AI computing with Thermo Fisher instrumentation for edge-to-cloud AI compute and multi-agent systems for lab orchestration.

**Established players:** Strateos and Emerald Cloud Lab provide remote-controlled automated lab facilities. When integrated with AI-driven design of experiments, these enable on-demand self-driving experimentation.

**Sources:**
- [Ginkgo Cloud Lab launch](https://www.prnewswire.com/news-releases/ginkgo-bioworks-launches-ginkgo-cloud-lab-powered-by-autonomous-lab-infrastructure-302700458.html)
- [Chemspeed + SciY SDL platform](https://ir.bruker.com/press-releases/press-release-details/2026/Chemspeed-and-SciY-Announce-SelfDriving-Laboratory-Platform-Integrating-Automation-Analytics-and-AI-Orchestration/default.aspx)
- [ORNL Q&A on autonomous labs](https://www.ornl.gov/news/qa-ornls-advincula-autonomous-labs-materials-research)
- [GEN: Autonomous vs. automated labs](https://www.genengnews.com/insights/trends-for-2026/automation-the-future-of-labs-is-autonomous-not-just-automated/)
- [Awesome self-driving labs (GitHub)](https://github.com/AccelerationConsortium/awesome-self-driving-labs)

---

## 3. AI Drug Discovery

### Current State (2026)

The year 2026 is described as a critical validation year. The field has progressed from speculative technology to early clinical validation, but the gap between promise and performance remains.

**Key data points:**
- 173 AI-originated drug programs are tracked as of 2026
- Phase III clinical results will be the definitive test of whether AI can deliver drugs that work at scale
- Self-driving labs are proliferating for closed-loop design-make-test-learn cycles running 24/7
- However, autonomous labs have NOT yet demonstrated ability to discover validated drug candidates independently

**Recent breakthroughs:**
- **LUMI-lab:** Combines large-scale molecular pretraining, active learning, and robotics. Discovered that brominated lipids (not previously linked to mRNA delivery) enhance efficiency of getting mRNA inside human cells.
- **NVIDIA BioNeMo platform:** Turns experimental data into intelligence for AI, creating a continuous learning cycle where every experiment informs the next. Adopted by multiple life sciences leaders.

**Shuttle Pharmaceuticals (March 26, 2026):** Announced autonomous, multi-agent AI system (molecule.ai platform expansion) for scientific workflows with new predictive and generative models.

**Sources:**
- [Drug Target Review: 2026 predictions](https://www.drugtargetreview.com/article/192962/ai-in-drug-discovery-predictions-for-2026/)
- [Drug Target Review: AI no longer optional](https://www.drugtargetreview.com/article/192243/2026-the-year-ai-stops-being-optional-in-drug-discovery/)
- [Self-driving labs in drug development](https://www.drugtargetreview.com/article/193601/how-self-driving-labs-are-changing-drug-development/)
- [LUMI-lab mRNA discovery](https://phys.org/news/2026-02-ai-powered-platform-discovery-mrna.html)
- [NVIDIA BioNeMo adoption](https://nvidianews.nvidia.com/news/nvidia-bionemo-platform-adopted-by-life-sciences-leaders-to-accelerate-ai-driven-drug-discovery)
- [AI drug discovery complete analysis](https://axis-intelligence.com/ai-drug-discovery-2026-complete-analysis/)

---

## 4. Market Size & Funding

### Market Projections

| Segment | 2025 | 2026 | 2035 | CAGR |
|---------|------|------|------|------|
| AI for Scientific Discovery (global) | $4.80B | $5.85B | $34.78B | 21.9% |
| AI for Scientific Discovery (North America) | $1.92B | -- | $14.09B | 22.1% |
| AI for Scientific Discovery (US) | $1.44B | -- | $10.63B | 22.1% |
| AI in Drug Discovery | $2.9B | $5.1B | $13.4B | 11.3% |
| Drug Discovery (total, AI-driven) | -- | -- | $174.14B | -- |

### Major Funding Rounds (2024-2026)

| Company | Round | Amount | Valuation | Date |
|---------|-------|--------|-----------|------|
| Xaira Therapeutics | Launch | $1B committed | -- | 2025 |
| Isomorphic Labs | Series A | $600M | $1.3B | March 2025 |
| Lila Sciences | Series A ext. | $115M (total $350M) | $1.3B | Oct 2025 |
| Recursion Pharmaceuticals | Raise | $239M | $4B | 2025 |
| Chai Discovery | Series B | $130M (total $230M in 15 mo.) | $1.3B | Dec 2025 |
| Insilico Medicine | Series E | $123M | -- | 2025 |
| Autoscience Institute | Seed | $14M | -- | March 2026 |

**Total VC into AI drug development:** $3.2B across 135 startups in last 12 months.

**Valuation premium:** AI-native biotech companies fetch nearly 100% valuation premium over broader biopharma. However, smaller companies face existential pressures -- multiple have shut down entirely despite substantial backing, others announced 20%+ workforce reductions.

**Sources:**
- [Precedence Research: AI scientific discovery market](https://www.precedenceresearch.com/ai-for-scientific-discovery-market)
- [Market.us: AI scientific discovery market](https://market.us/report/ai-for-scientific-discovery-market/)
- [IntuitionLabs: AI biotech funding analysis](https://intuitionlabs.ai/articles/ai-biotech-funding-trends)
- [Crunchbase: AI funding trends 2025](https://news.crunchbase.com/ai/big-funding-trends-charts-eoy-2025/)
- [PitchBook: AI biotech valuation premiums](https://pitchbook.com/news/articles/ai-biotechs-fetch-big-premiums-as-investors-pile-into-drug-discovery-startups)
- [Chai Discovery Series B (TechCrunch)](https://techcrunch.com/2025/12/15/openai-backed-biotech-firm-chai-discovery-raises-130m-series-b-at-1-3b-valuation/)
- [BioSpace: AI drug discovery market](https://www.biospace.com/press-releases/artificial-intelligence-ai-in-drug-discovery-market-size-expected-to-reach-usd-16-52-billion-by-2034)

---

## 5. Scientific Evaluation: How It Differs from Coding Metrics

### The Core Challenge

Scientific evaluation is fundamentally harder than code evaluation. In coding, tests pass or fail. In science, ground truth is often unknown, experiments are expensive, and validation can take years.

### Metric Categories for Scientific AI

**1. Novelty metrics** -- Is the hypothesis genuinely new? Requires literature search, patent search, and domain expert validation. No fully automated solution exists. The AI Scientist v2 uses automated reviewer agents, but they missed inaccurate citations.

**2. Experimental reproducibility** -- Can the experiment be repeated with the same results? Self-driving labs excel here because robotic execution is inherently reproducible, removing human variability.

**3. Hypothesis quality** -- Is the hypothesis testable, falsifiable, and well-formed? Google's AI Co-Scientist evaluates this iteratively through multi-agent debate, but the ultimate test is experimental validation.

**4. Discovery significance** -- Does the finding matter? This is inherently subjective and domain-dependent. Current systems use peer-review simulation (AI Scientist v2) or downstream experimental validation (AI Co-Scientist at Stanford/Imperial College).

**5. Cost-efficiency** -- Time and money per validated discovery. This is where autonomous systems clearly win: $6-15 per paper (AI Scientist v2), 3.5 hours vs. months of human work, 24/7 operation of self-driving labs.

### Comparison: Coding vs. Scientific Metrics

| Dimension | Coding Agents | Scientific Agents |
|-----------|---------------|-------------------|
| Ground truth | Test suites (binary) | Often unknown |
| Feedback loop | Seconds (compile/test) | Hours to years (experiments) |
| Metric clarity | Pass/fail, benchmarks | Multi-dimensional, subjective |
| Reproducibility | Deterministic | Requires controlled conditions |
| Cost per evaluation | Cheap (compute) | Expensive (reagents, equipment, time) |
| Safety concerns | Code correctness | Chemical/biological safety |
| Peer validation | Code review | Peer review, replication studies |

### Current Evaluation Gaps

Research identifies persistent gaps: non-determinism in agent behavior, limited reproducibility of evaluations, benchmark overfitting, incomplete safety assessment, and insufficient long-horizon evaluation. According to LangChain's 2026 State of AI Agents report, 57% of organizations have agents in production, but quality remains the top barrier (32% of respondents).

**Sources:**
- [AI agent evaluation metrics 2026](https://masterofcode.com/blog/ai-agent-evaluation)
- [TechRxiv: Agent evaluation survey](https://www.techrxiv.org/doi/full/10.36227/techrxiv.177162480.04513202/v2)
- [arXiv: AI Agent Reliability](https://arxiv.org/html/2602.16666v1)
- [O-mega: Agent evaluation benchmarks guide](https://o-mega.ai/articles/the-best-ai-agent-evals-and-benchmarks-full-2025-guide)

---

## 6. AutoML & Self-Evolving ML Systems

By 2026, AutoML has matured into mainstream technology. The field is advancing toward fully autonomous ML pipelines.

**Key trends:**
- **Self-optimizing pipelines:** Automatically select model architecture, hyperparameters, and training strategies based on real-time data. Detect performance drift and trigger retraining without human input.
- **Domain-specific AutoML (AutoML 3.0):** Context-aware, domain-specific techniques leveraging multi-modal learning and user-system collaboration.
- **Generative AI integration:** AutoML now automates data preparation, feature engineering, and even synthetic dataset generation.
- **Agentic AutoML:** The shift from "how to build a model" to "why this model matters for business impact."

**Reality check:** Self-improving AI in 2026 is near-prototype / partial implementation. An important milestone, but still far from full autonomy.

**Sources:**
- [KDnuggets: AutoML techniques 2026](https://www.kdnuggets.com/5-cutting-edge-automl-techniques-to-watch-in-2026)
- [LogicBalls: Agentic AutoML](https://logicballs.com/blog/agentic-automl-future-machine-learning-2026)
- [WeTrans Cloud: Autonomous ML pipelines 2026](https://wetranscloud.com/blog/autonomous-ml-pipelines-2026)
- [Times of AI: Self-improving AI myth or reality](https://www.timesofai.com/industry-insights/self-improving-ai-myth-or-reality/)

---

## 7. Which Scientific Domains Are Most Ready?

Ranked by readiness for autonomous AI agents:

### Tier 1: Ready Now (2026)

**1. Machine Learning Research**
- AI Scientist v2 already producing peer-reviewed papers autonomously
- Clear metrics (loss, accuracy, benchmark scores)
- Fast feedback loops (minutes to hours)
- Low cost per experiment (compute only)
- Autoscience deploying commercially

**2. Materials Science / Chemistry**
- MARS system achieving closed-loop autonomous discovery
- Self-driving labs operational at DOE national labs, Berkeley, MIT
- Well-defined optimization targets (material properties)
- Robotic experimentation infrastructure maturing
- 10x acceleration demonstrated

**3. Computational Biology / Genomics**
- Google AI Co-Scientist demonstrated with cancer, antimicrobial resistance
- Large datasets available (sequencing data)
- Well-defined computational tasks (protein structure, gene expression)
- NVIDIA BioNeMo providing platform infrastructure

### Tier 2: Emerging (2026-2028)

**4. Drug Discovery (computational phases)**
- 173 AI-originated programs tracked
- $3.2B VC invested in last 12 months
- Self-driving labs for compound screening
- Phase III validation still pending
- Gap between computational prediction and wet-lab validation

**5. Climate / Earth Science**
- Massive satellite/sensor datasets
- Complex simulation environments exist
- Government funding (DOE Genesis Mission)
- Long validation timelines

### Tier 3: Early Stage (2028+)

**6. Experimental Biology**
- Ginkgo Cloud Lab providing infrastructure
- High complexity of biological systems
- Safety constraints limit full autonomy
- Reproducibility challenges

**7. Physics / Astronomy**
- Limited by access to specialized instruments
- Long observation cycles
- Theoretical physics lacks experimental feedback loop
- Some computational physics amenable to automation

---

## 8. Startup Viability Assessment

### The Opportunity

**Bull case:**
- $4.8B market in 2025, growing to $34.8B by 2035 at 22% CAGR
- Massive acceleration demonstrated (10-100x in materials, days vs. years in hypothesis generation)
- Government backing: DOE Genesis Mission, PNNL $47M autonomous lab
- Google, NVIDIA, Thermo Fisher all making major platform investments
- Autoscience just raised $14M seed with tier-1 VCs (General Catalyst)
- AI-native biotech companies command nearly 100% valuation premium
- The recursive self-improvement loop (AI discovers things that make AI better at discovering things) is a genuine moat

**Bear case:**
- Smaller AI drug discovery companies are shutting down despite substantial backing
- 20%+ workforce reductions at multiple AI bio companies
- Phase III clinical validation hasn't proven AI-discovered drugs work at scale yet
- Scientific evaluation is genuinely harder than code evaluation -- the "metric problem"
- Requires deep domain expertise (domain scientists, not just ML engineers)
- Infrastructure costs: PNNL's autonomous lab cost $47M. Cloud labs mitigate this but still expensive.
- Regulatory risk: FDA framework for AI-discovered drugs still evolving
- Incumbents (Google, NVIDIA) are building platforms that could commoditize the space
- Self-improving AI is "near-prototype / partial implementation" -- marketing ahead of reality in many cases

### Strategic Positioning Options

**Option A: Horizontal platform (self-improving agent infrastructure)**
- Build the "Acumen for science" -- a domain-agnostic self-improvement layer for scientific AI agents
- Differentiation: the self-improvement loop itself, not the domain science
- Risk: thin layer easily replicated by Google/NVIDIA platforms
- Opportunity: Autoscience raised $14M doing something similar for ML research

**Option B: Vertical domain play (pick one science)**
- Materials science has the strongest infrastructure and fastest feedback loops
- Drug discovery has the largest market but highest risk and longest validation
- Computational biology has Google's backing but the co-scientist may dominate
- Risk: requires deep domain expertise and potentially lab infrastructure
- Opportunity: $600M Isomorphic Labs round shows the ceiling is high

**Option C: Infrastructure / tooling layer**
- Build the evaluation / metrics layer for scientific AI agents
- The "metric problem" is unsolved and everyone needs it
- Comparison: what testing frameworks are to software development
- Risk: unsexy infrastructure play, hard to monetize directly
- Opportunity: the gap between "we can generate hypotheses" and "we know which hypotheses are good" is where value concentrates

**Option D: Cloud lab orchestration with self-improving agents**
- The integration layer between AI agents and physical/cloud lab infrastructure
- Chemspeed+SciY are building vendor-agnostic SDL platforms, but the AI orchestration layer is still open
- Risk: requires hardware partnerships and lab operations expertise
- Opportunity: Ginkgo Cloud Lab just launched, creating a platform to build on

### Verdict

The market is real and growing fast ($4.8B to $34.8B). The technology is at an inflection point -- 2026 is the year autonomous labs go from demos to deployment. However:

1. **The safest entry point is ML research automation** -- metrics are clear, feedback is fast, infrastructure is cheap (just compute), and Autoscience just proved the model with $14M in seed funding.

2. **Materials science is the best physical-world domain** -- strongest infrastructure, fastest feedback loops, government backing, demonstrated 10x acceleration.

3. **Drug discovery is the largest market but the highest risk** -- longest validation timelines, most capital intensive, regulatory uncertainty, and multiple well-funded companies have already failed.

4. **The "metric problem" is the biggest unsolved challenge** and whoever solves scientific hypothesis evaluation at scale has a genuine moat. Every player in this space needs it, and no one has a great solution.

5. **Self-improvement is the key differentiator** -- the recursive loop where AI uses its discoveries to become better at making discoveries is what separates a tool from a flywheel. This is directly analogous to what Acumen does for coding agents: observe, learn, improve, compound.

---

## 9. Key People & Organizations

| Entity | Role | Key Contribution |
|--------|------|------------------|
| Sakana AI | Research lab (Tokyo) | AI Scientist v1/v2, first AI peer-reviewed paper |
| Google DeepMind | Research lab | AI Co-Scientist, Isomorphic Labs spin-out, C2S-Scale |
| Autoscience Institute | Startup | First commercial automated AI research lab ($14M seed) |
| NVIDIA | Platform | BioNeMo platform, Thermo Fisher partnership |
| Ginkgo Bioworks | Platform | Cloud Lab launch (March 2026), 70+ instruments |
| Chemspeed + SciY | Platform | Open SDL platform, vendor-agnostic |
| Xaira Therapeutics | Startup | $1B launch funding, ARCH Ventures |
| Isomorphic Labs | Startup (DeepMind) | $600M Series A, AlphaFold team |
| Chai Discovery | Startup (OpenAI) | $230M in 15 months, $1.3B valuation |
| Lila Sciences | Startup | $350M Series A, $1.3B valuation |
| Recursion Pharma | Public co. | $4B valuation, large-scale drug discovery |
| Argonne National Lab | Gov lab | Autonomous Discovery initiative |
| PNNL | Gov lab | $47M 97-robot autonomous lab |
| UBC | University | AI Scientist collaboration, foundational research |
