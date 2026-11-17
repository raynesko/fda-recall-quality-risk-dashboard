# 60-Second Pitch (T7.2.1)

~145 words, about 55-60 s at a normal speaking pace (150 words per minute). Time yourself once; trim the bracketed sentence if you run over.

> "I'm an industrial and systems engineering student, and I wanted a project in the language of quality. FDA publishes every drug and food recall with a free-text reason, but you can't see at a glance which failure modes matter. I classified about 12,700 recall events into 14 root-cause categories. I tested an ML model against simple keyword rules, and the rules won, so that's what runs in production. A Pareto showed that six to eight categories drive about 80% of events. I used control charts to separate real shifts from normal month-to-month noise. [I simulated the false-alarm rate, because textbook limits break down on small counts.] Then I pre-registered a risk score and backtested it. It didn't beat naive baselines, because spikes regress to the mean, so I present it as a triage tool, not a forecast. Everything is in a Power BI dashboard with DMAIC actions."

Numbers: 12,700 ≈ `data.n_events` 12,687; 14 = taxonomy categories; "about 80%" = `pareto.*.vital_few_share` 0.825.
