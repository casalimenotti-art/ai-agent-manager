# Ricerca skill per gli agenti (2026-11-26)

Fonti: pagine pubbliche di skills.sh e API pubbliche GitHub. Nulla e stato installato. Non riproposte le skill gia installate (es. seo, frontend-design, ui-ux-pro-max, web-design-guidelines, find-skills, graphify, security-review) ne quelle gia in scoperte.json. Le installazioni cambiano nel tempo.

Comandi come testo, da eseguire solo dopo approvazione.

| # | Skill | Install | Stelle repo | Licenza | Ultimo push repo | Script | Agente | Perche |
|---|-------|---------|-------------|---------|------------------|--------|--------|--------|
| 1 | coreyhaines31/marketingskills@copywriting | 268.6K | 62.7k | MIT | 2026-11-25 | nessuno nella skill (la repo ha script di sviluppo) | web-designer, vendite | Testi di landing e pagine, bozze commerciali |
| 2 | coreyhaines31/marketingskills@cold-email | 147K | 62.7k | MIT | 2026-11-25 | nessuno | vendite/outreach | Bozze email B2B, follow-up, 5 framework. Audit: Socket Pass, Snyk Warn |
| 3 | coreyhaines31/marketingskills@schema | 98.7K | 62.7k | MIT | 2026-11-25 | nessuno visibile | web-designer | JSON-LD LocalBusiness per SEO locale. Audit tutti Pass |
| 4 | addyosmani/web-quality-skills@core-web-vitals | 37.6K | 3.1k | MIT | 2026-08-24 | nessuno | web-designer | LCP/INP/CLS, misura prima di ottimizzare. Audit tutti Pass |
| 5 | addyosmani/web-quality-skills@performance | 46.8K | 3.1k | MIT | 2026-08-24 | nessuno | web-designer | Prestazioni di caricamento |
| 6 | wshobson/agents@python-testing-patterns | 41.7K | 42.9k | MIT | 2026-11-24 | non verificato (albero troncato) | sviluppatore-dashboard | pytest, fixture, mock, CI. Audit tutti Pass |
| 7 | vercel-labs/agent-browser@agent-browser | 1.7M | 54.1k | Apache-2.0 | 2026-11-26 | CLI esterna, SKILL.md e solo un rimando | ricercatore-web | Browser automatico per pagine dinamiche |
| 8 | elevenlabs/skills@text-to-speech | 24.8K | 590 | MIT | 2026-11-26 | nessuno (solo .md) | voce/TTS | Skill ufficiale ElevenLabs, 90+ lingue |
| 9 | streamlit/agent-skills@developing-with-streamlit | 3.6K | 227 | Apache-2.0 | 2026-07-23 | si: scripts/discover.py | sviluppatore-dashboard | Skill ufficiale Streamlit, docs allineate alla versione |
| 10 | jamditis/claude-skills-journalism@source-verification | 511 | 462 | MIT | 2026-11-25 | non nella skill (la repo ne ha altri) | ricercatore-web | Metodo SIFT, tratta il contenuto web come dato non fidato |
| 11 | addyosmani/web-quality-skills@web-quality-audit | 40.1K | 3.1k | MIT | 2026-08-24 | si: scripts/analyze.sh | web-designer | Audit complessivo; leggere lo script prima |

## Comandi

```
npx skills add coreyhaines31/marketingskills@copywriting -g -y
npx skills add coreyhaines31/marketingskills@cold-email -g -y
npx skills add coreyhaines31/marketingskills@schema -g -y
npx skills add addyosmani/web-quality-skills@core-web-vitals -g -y
npx skills add addyosmani/web-quality-skills@performance -g -y
npx skills add wshobson/agents@python-testing-patterns -g -y
npx skills add vercel-labs/agent-browser@agent-browser -g -y
npx skills add elevenlabs/skills@text-to-speech -g -y
npx skills add streamlit/agent-skills@developing-with-streamlit -g -y
npx skills add jamditis/claude-skills-journalism@source-verification -g -y
npx skills add addyosmani/web-quality-skills@web-quality-audit -g -y
```

## Rischi

- cold-email: solo bozze. L'invio e la profilazione di persone restano sotto GDPR e regole anti-spam; nessun invio automatico.
- agent-browser: Snyk Warn; puo usare profili Chrome reali, sessioni cloud, proxy e tunnel. Usare solo profilo isolato, senza accessi personali. SKILL.md scarica le istruzioni dalla CLI a runtime, quindi il comportamento dipende dalla versione.
- elevenlabs text-to-speech: serve ELEVENLABS_API_KEY, servizio a pagamento di terzi; i testi vengono inviati al servizio. Non verificato il prezzo. Alternativa locale non scelta: le skill TTS locali (Kokoro, ecc.) hanno meno di 250 installazioni.
- source-verification: poche installazioni, Snyk Warn.
- Pagine skills.sh non mostrano la licenza: valori presi dall'API GitHub della repo, non della singola skill.
- Gli audit (Gen Agent Trust Hub, Socket, Snyk) sono automatici, non sostituiscono la lettura di SKILL.md.

## Lacune

- SEO locale dedicato (GBP, NAP): esistono skill (kostja94/marketing-skills@local-seo, garrettjsmith/localseoskills) ma senza installazioni verificate e fonti poco note; non incluse.
- Sicurezza Python: nessuna skill con piu di 1000 installazioni verificata (la migliore vista: unitoneai/securityskills, circa 158). Resta la skill security-review gia installata.
- Ricerca/verifica: le alternative (fact-check, web-research) hanno poche installazioni.
- Non esaminati gli ultimi commit della singola skill, solo della repo.
