"""Valorant-inspired look: red #FF4655 on dark navy, condensed headings, cut-corner buttons.
Fan project styling only — no Riot logos or artwork."""

RED = "#FF4655"
NAVY = "#0F1923"
PANEL = "#1B2733"
BONE = "#ECE8E1"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput input, .stButton button {{
  font-family: 'Barlow', sans-serif;
}}
.stApp {{
  background:
    linear-gradient(115deg, rgba(255,70,85,0.10) 0%, rgba(15,25,35,0) 38%),
    repeating-linear-gradient(135deg, rgba(236,232,225,0.025) 0 2px, transparent 2px 22px),
    {NAVY};
}}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; max-width: 860px; }}

/* ---------- hero */
.hero {{ position: relative; padding: 1.4rem 1.6rem 1.2rem; margin-bottom: 1.2rem;
  background: linear-gradient(90deg, {PANEL} 0%, rgba(27,39,51,0.6) 100%);
  border-left: 6px solid {RED};
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 22px), calc(100% - 22px) 100%, 0 100%); }}
.hero .kicker {{ color: {RED}; font-weight: 700; letter-spacing: .28em; font-size: .78rem; text-transform: uppercase; }}
.hero h1 {{ font-family: 'Bebas Neue', sans-serif; font-size: 4.1rem; line-height: .92; margin: .25rem 0 .4rem;
  color: {BONE}; letter-spacing: .02em; }}
.hero h1 span {{ color: {RED}; }}
.hero p {{ color: rgba(236,232,225,.78); margin: 0 0 .9rem; font-size: 1.02rem; }}
.stats {{ display: flex; gap: .6rem; flex-wrap: wrap; }}
.stat {{ background: rgba(15,25,35,.75); border: 1px solid rgba(236,232,225,.12); padding: .45rem .8rem;
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 0 100%); }}
.stat b {{ font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; color: {BONE}; display: block; line-height: 1; }}
.stat small {{ color: rgba(236,232,225,.6); text-transform: uppercase; letter-spacing: .12em; font-size: .66rem; }}

/* ---------- section labels */
.label {{ font-family: 'Bebas Neue', sans-serif; letter-spacing: .12em; font-size: 1.25rem; color: {BONE};
  margin: .8rem 0 .35rem; display: flex; align-items: center; gap: .5rem; }}
.label::before {{ content: ""; width: 14px; height: 14px; background: {RED};
  clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%); }}

/* ---------- buttons: cut corners, red on hover */
.stButton button {{ background: {PANEL}; color: {BONE}; border: 1px solid rgba(236,232,225,.18); border-radius: 0;
  text-align: left; font-weight: 600; padding: .7rem .9rem; min-height: 3.4rem;
  clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%); transition: all .15s ease; }}
.stButton button:hover {{ background: {RED}; color: #fff; border-color: {RED}; transform: translateY(-1px); }}

/* ---------- input */
.stTextInput input {{ background: {PANEL}; border: 1px solid rgba(236,232,225,.2); border-radius: 0;
  color: {BONE}; font-size: 1.05rem; padding: .75rem .9rem; }}
.stTextInput input:focus {{ border-color: {RED}; box-shadow: 0 0 0 1px {RED}; }}

/* ---------- answer card */
.card {{ background: {PANEL}; border-top: 3px solid {RED}; padding: 1rem 1.1rem; margin: .6rem 0 .8rem;
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%); }}
.card .q {{ color: rgba(236,232,225,.6); font-size: .85rem; text-transform: uppercase; letter-spacing: .1em; }}
.card .a {{ font-size: 1.15rem; margin-top: .35rem; color: {BONE}; }}
.verdict {{ display: inline-block; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; font-size: .8rem;
  padding: .3rem .7rem; margin-bottom: .5rem;
  clip-path: polygon(8px 0, 100% 0, calc(100% - 8px) 100%, 0 100%); }}
.verdict.success {{ background: #19c37d; color: #06210f; }}
.verdict.warning {{ background: #f5b83d; color: #2a1d00; }}
.verdict.error   {{ background: {RED}; color: #fff; }}
.verdict.info    {{ background: #5aa9e6; color: #04182a; }}

/* ---------- check list */
.check {{ display: flex; gap: .6rem; align-items: baseline; padding: .32rem 0;
  border-bottom: 1px dashed rgba(236,232,225,.08); }}
.check .dot {{ width: 9px; height: 9px; flex: none; transform: rotate(45deg); margin-top: .35rem; }}
.check .ok {{ background: #19c37d; }} .check .flag {{ background: #f5b83d; }} .check .block {{ background: {RED}; }}
.check .name {{ font-weight: 700; text-transform: uppercase; letter-spacing: .08em; font-size: .82rem; min-width: 7.5rem; }}
.check .why {{ color: rgba(236,232,225,.7); font-size: .9rem; }}

[data-testid="stDataFrame"] {{ border: 1px solid rgba(236,232,225,.12); }}
.foot {{ color: rgba(236,232,225,.5); font-size: .8rem; margin-top: 2rem; padding-top: .8rem;
  border-top: 1px solid rgba(236,232,225,.1); }}
.foot a {{ color: {RED}; }}
</style>
"""
