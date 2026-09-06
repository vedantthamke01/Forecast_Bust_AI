# SIH26079: Difficult & Trick Questions Guide

**Target Audience**: Presenters facing rigorous questioning from senior meteorologists and senior machine learning evaluators.  
**Tone**: Transparent, humble, mathematically unshakeable, refusing to exaggerate.

---

### Trick Question 1: "Your PR-AUC is only 0.2682. That seems very low. Why should we trust this model?"
**How to Answer**:
"That is an insightful question, and we must look at the base rate of the positive class. 

In our chronologically isolated test set of 7,560 records, severe forecast busts occurred in only 407 instances—a base prevalence of just **5.38%**. 

For a random or uninformative classifier on this partition, the baseline PR-AUC is equal to the prevalence: **0.0950**. Our model achieves **0.2682**—an absolute improvement of **+0.1732**, representing a **2.82× gain** over the baseline. 

In rare-event classification (such as medical diagnosis or fraud detection), raw PR-AUC values between 0.25 and 0.30 over a 5% baseline indicate substantial discriminative signal. Furthermore, our ROC-AUC is **0.8756**, and our Brier calibration score is **0.0450**, proving that the predicted probabilities are mathematically reliable rather than artificially overconfident."

---

### Trick Question 2: "Your accuracy is 94.62%. Isn't accuracy completely misleading on an imbalanced dataset?"
**How to Answer**:
"**You are 100% correct, and we explicitly highlight this in our documentation.** 

Because severe busts represent only ~5% of test records, a naive dummy model that always predicts 'No Bust' would achieve ~94.62% accuracy while having zero operational utility (0% precision, 0% recall, 0.0950 PR-AUC). 

That is precisely why we do **not** rely on accuracy as our primary metric. We evaluate the model using **Precision-Recall AUC (PR-AUC)**, **Brier score (0.0450)**, **Expected Calibration Error (0.0257)**, and the **full confusion matrix**. Our high accuracy simply confirms that the model avoids false alarms on routine benign forecasts, while the PR-AUC proves genuine discriminative capability."

---

### Trick Question 3: "Your model predicted 0.1% bust risk for Pune. How can you possibly prove that 0.1% is correct?"
**How to Answer**:
"We cannot prove that an individual single event has an exact 0.1% probability of occurrence—no probabilistic model can prove a single-event probability in an open physical system. 

What we *can* prove is that our model is **empirically calibrated**. Using Isotonic regression, our predictions are mapped to observed historical frequencies. A predicted probability of 0.1% means that across a sufficiently large group of historical forecasts exhibiting these exact calm synoptic conditions—moderate 8.9 m/s winds, zero precipitation anomaly, and low ensemble spread—approximately 1 out of 1,000 experienced an unexpected bust. 

It is a model estimate of risk, not physical proof of atmospheric stability."

---

### Trick Question 4: "Why isn't ensemble spread sufficient? Meteorologists have used spread for decades."
**How to Answer**:
"Ensemble spread is a foundational tool in operational meteorology, but it has well-documented limitations:
1. **Under-dispersion**: Operational ensemble systems frequently suffer from under-dispersion, where member trajectories cluster tightly around a shared physical bias and subsequently all bust together.
2. **One-Dimensionality**: Spread measures divergence among members, but it does not account for the forecast's proximity to regional climatological extremes, baroclinic deepening, or run-to-run consistency revisions.

Our model does not discard ensemble spread—spread is one of our primary features. However, our model adds value by combining spread with 16 other dynamical, seasonal, and consistency signals to identify busts that spread alone fails to catch."

---

### Trick Question 5: "You claim Days 3 to 10 on your slides, but your training dataset only goes to Day 7. Aren't you misleading us?"
**How to Answer**:
"We want to be completely transparent about this boundary:
- **Historical Model Training**: Covered through **Day 7 (168 hours)**. The free, publicly accessible NWP archive we utilized only retains initializations up to Day 7. Rather than fabricating fake Day 8 to 10 historical data, we chose to maintain complete scientific honesty.
- **Operational Live Inference**: Supported through **Day 10 (240 hours)**. Our feature extraction treats lead time as a continuous variable $\tau \in [24, 240]$, allowing the calibrated model to evaluate operational 10-day ECMWF IFS guidance fetched in real time.
- **Path to Full Training**: Extending historical training to Days 8–10 requires access to deeper institutional tape archives (such as NCMRWF's internal MARS system). We openly disclose this as a dataset limitation rather than pretending it does not exist."

---

### Trick Question 6: "Is ERA5 the actual weather? Why should we believe ERA5 represents ground truth?"
**How to Answer**:
"ERA5 is **not** direct surface ground truth. ERA5 is a global reanalysis product generated by combining past observations with numerical model physics using 4D-Var data assimilation at 0.25° grid resolution (~25 km). 

While ERA5 provides spatially continuous, thermodynamically balanced fields across all of India, it can smooth localized orographic cloudbursts in complex terrain compared to surface rain gauges. In this project, ERA5 serves as an authoritative *post-event reference dataset* for historical development. In an operational NCMRWF setting, the pipeline would directly assimilate IMD automatic weather station networks."

---

### Trick Question 7: "Are you trying to predict weather with AI?"
**How to Answer**:
"**No, absolutely not.** Forward weather prediction—solving the Navier-Stokes fluid dynamical equations on supercomputers—is the statutory mandate of NCMRWF and IMD. 

Our system does not predict whether it will rain tomorrow. Upstream NWP models provide the expected weather forecast. Our system predicts **forecast reliability**—estimating the probability that the NWP guidance itself might experience an extreme failure."

---

### Trick Question 8: "Can NCMRWF deploy this system into production tomorrow morning?"
**How to Answer**:
"**No, and any team claiming immediate operational deployment is not being realistic.** 

While our core architecture, API, and calibration pipeline are fully functional, operational deployment within a national meteorological agency requires:
1. Direct integration with NCMRWF's internal HPC job scheduler and GRIB2 file pipelines.
2. Ingestion of internal NCUM 51-member ensemble grids rather than external web APIs.
3. Conducting a multi-season shadow verification study alongside operational forecasters to evaluate performance across diverse monsoon regimes.
This project is an advanced, validated, and reproducible prototype demonstrating technical feasibility."
